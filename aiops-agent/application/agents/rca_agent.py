"""RCA Agent - 根因分析"""

import json
from typing import List

import structlog

from application.agents.prompts import PromptTemplate
from domain.models.evidence import Evidence
from domain.models.root_cause import RootCause
from domain.value_objects.confidence import Confidence
from domain.value_objects.time_range import TimeRange
from infrastructure.llm.llm_client import LLMClient

logger = structlog.get_logger(__name__)


class RCAAgent:
    """RCA Agent

    职责：
    1. 综合分析指标、日志、链路证据
    2. 使用 LLM 推理根本原因
    3. 提取根因并给出修复建议
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def analyze(
        self,
        service_name: str,
        time_range: TimeRange,
        evidences: List[Evidence],
    ) -> List[RootCause]:
        """分析根因

        Args:
            service_name: 服务名称
            time_range: 时间范围
            evidences: 证据列表

        Returns:
            根因列表
        """
        logger.info(
            "rca_agent_start",
            service_name=service_name,
            time_range=str(time_range),
            evidence_count=len(evidences),
        )

        # 1. 格式化证据列表
        evidence_list = self._format_evidence_list(evidences)

        # 2. 格式化 prompt
        messages = PromptTemplate.format_rca_agent_prompt(
            service_name=service_name,
            time_range=str(time_range),
            evidence_list=evidence_list,
        )

        # 3. 调用 LLM 分析
        try:
            response = await self.llm.chat(messages, max_tokens=3000)

            # 尝试解析 JSON
            try:
                analysis = json.loads(response)
            except json.JSONDecodeError:
                logger.warning("llm_response_not_json_try_extract", response=response[:200])
                return []

            # 4. 转换为领域模型
            root_causes = []
            for rc in analysis.get("root_causes", []):
                # 转换置信度（0.0-1.0 -> 0-100）
                confidence_value = int(rc["confidence"] * 100)
                confidence = Confidence(confidence_value)

                root_cause = RootCause(
                    cause=rc["cause"],
                    confidence=confidence,
                    evidence_ids=rc.get("evidence_ids", []),
                )
                root_causes.append(root_cause)

            logger.info(
                "rca_agent_completed",
                service_name=service_name,
                root_cause_count=len(root_causes),
            )

            return root_causes

        except Exception as e:
            logger.error("rca_agent_failed", error=str(e))
            return []

    def _format_evidence_list(self, evidences: List[Evidence]) -> str:
        """格式化证据列表为文本"""
        lines = []
        for i, ev in enumerate(evidences, 1):
            lines.append(f"{i}. [{ev.type.value}] {ev.summary}")
            lines.append(f"   来源: {ev.source}")
            lines.append(f"   ID: {ev.id}")
            if ev.detail:
                lines.append(f"   详情: {json.dumps(ev.detail, ensure_ascii=False)}")
            lines.append("")

        return "\n".join(lines)
