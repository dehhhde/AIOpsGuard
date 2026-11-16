"""诊断引擎服务"""

import structlog
from langgraph.graph import CompiledStateGraph

from domain.enums import DiagnosisStage
from domain.models.diagnosis_session import DiagnosisSession
from domain.models.report import Report

logger = structlog.get_logger(__name__)


class DiagnosisEngineService:
    """诊断引擎服务

    职责：
    1. 执行 LangGraph 诊断流程
    2. 更新诊断会话状态
    3. 持久化证据和根因
    """

    def __init__(self, graph: CompiledStateGraph):
        self.graph = graph

    async def run(self, session: DiagnosisSession) -> None:
        """运行诊断

        Args:
            session: 诊断会话
        """
        logger.info("diagnosis_engine_start", session_id=session.diagnosis_id)

        try:
            # 启动会话
            session.start()

            # 执行 LangGraph
            logger.info("langgraph_invoke_start", session_id=session.diagnosis_id)

            result = await self.graph.ainvoke(
                {
                    "service_name": session.service.service_name,
                    "start_time": session.time_range.start_time.isoformat(),
                    "end_time": session.time_range.end_time.isoformat(),
                }
            )

            logger.info(
                "langgraph_invoke_completed",
                session_id=session.diagnosis_id,
                result_keys=list(result.keys()),
            )

            # 推进阶段：数据收集
            session.advance_stage(DiagnosisStage.COLLECT)

            # 添加证据
            for evidence in result.get("metric_evidences", []):
                session.add_evidence(evidence)
            for evidence in result.get("log_evidences", []):
                session.add_evidence(evidence)
            for evidence in result.get("trace_evidences", []):
                session.add_evidence(evidence)

            # 推进阶段：根因分析
            session.advance_stage(DiagnosisStage.RCA)

            # 添加根因
            for root_cause in result.get("root_causes", []):
                session.add_root_cause(root_cause)

            # 推进阶段：报告生成
            session.advance_stage(DiagnosisStage.REPORT_GENERATION)

            # 生成报告
            report_content = self._generate_report_content(session, result)
            report = Report(content=report_content)

            # 完成诊断
            session.complete(report)

            logger.info(
                "diagnosis_engine_completed",
                session_id=session.diagnosis_id,
                evidence_count=len(session.evidence),
                root_cause_count=len(session.root_causes),
            )

        except Exception as e:
            logger.error(
                "diagnosis_engine_failed",
                session_id=session.diagnosis_id,
                error=str(e),
                exc_info=True,
            )
            session.fail(str(e))
            raise

    def _generate_report_content(
        self, session: DiagnosisSession, result: dict
    ) -> str:
        """生成报告内容（Markdown）

        Args:
            session: 诊断会话
            result: LangGraph 执行结果

        Returns:
            Markdown 格式的报告内容
        """
        lines = [
            f"# 诊断报告：{session.service.service_name}",
            "",
            f"**诊断 ID**：{session.diagnosis_id}",
            f"**服务名称**：{session.service.service_name}",
            f"**环境**：{session.service.environment}",
            f"**时间范围**：{session.time_range.start_time} ~ {session.time_range.end_time}",
            f"**诊断耗时**：{session.duration_seconds():.2f} 秒",
            "",
            "---",
            "",
            "## 诊断摘要",
            "",
            result.get("summary", "诊断完成"),
            "",
            "---",
            "",
            "## 根因分析",
            "",
        ]

        # 根因列表
        if session.root_causes:
            for i, rc in enumerate(session.root_causes, 1):
                lines.append(f"### {i}. {rc.cause}")
                lines.append("")
                lines.append(f"- **置信度**：{rc.confidence.value}%")
                lines.append(
                    f"- **关联证据数**：{len(rc.evidence_ids)} 条"
                )
                lines.append("")
        else:
            lines.append("未发现明确的根本原因。")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("## 证据清单")
        lines.append("")

        # 证据列表
        if session.evidence:
            for i, ev in enumerate(session.evidence, 1):
                lines.append(
                    f"{i}. **[{ev.type.value}]** {ev.summary}"
                )
                lines.append(f"   - 来源：`{ev.source}`")
                lines.append("")
        else:
            lines.append("未收集到证据。")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*报告生成时间：" + str(session.finished_at) + "*")

        return "\n".join(lines)
