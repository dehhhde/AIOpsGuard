"""Metric Agent - 指标分析"""

import json
from datetime import datetime
from typing import List

import structlog

from application.agents.prompts import PromptTemplate
from application.agents.tools import AgentTools
from domain.enums import EvidenceType
from domain.models.evidence import Evidence
from domain.value_objects.time_range import TimeRange
from infrastructure.llm.llm_client import LLMClient

logger = structlog.get_logger(__name__)


class MetricAgent:
    """Metric Agent

    职责：
    1. 从 Prometheus 查询指标数据
    2. 使用 LLM 分析异常模式
    3. 提取指标证据
    """

    def __init__(self, llm_client: LLMClient, tools: AgentTools):
        self.llm = llm_client
        self.tools = tools

    async def analyze(
        self,
        service_name: str,
        time_range: TimeRange,
    ) -> List[Evidence]:
        """分析指标数据

        Args:
            service_name: 服务名称
            time_range: 时间范围

        Returns:
            证据列表
        """
        logger.info(
            "metric_agent_start",
            service_name=service_name,
            time_range=str(time_range),
        )

        # 1. 查询指标数据
        metrics_data = await self.tools.query_metrics(
            service_name=service_name,
            start_time=time_range.start_time,
            end_time=time_range.end_time,
        )

        # 2. 格式化 prompt
        messages = PromptTemplate.format_metric_agent_prompt(
            service_name=service_name,
            time_range=str(time_range),
            metrics_data=metrics_data,
        )

        # 3. 调用 LLM 分析
        try:
            response = await self.llm.chat(messages)

            # 尝试解析 JSON
            try:
                analysis = json.loads(response)
            except json.JSONDecodeError:
                # 如果 LLM 返回的不是纯 JSON，尝试提取 JSON 部分
                logger.warning("llm_response_not_json_try_extract", response=response[:200])
                # 简化处理：如果解析失败，返回空列表
                return []

            # 4. 转换为领域模型
            evidences = []
            for ev in analysis.get("evidence", []):
                evidence = Evidence(
                    type=EvidenceType.METRIC,
                    summary=ev["summary"],
                    source=ev["source"],
                    time_range=time_range,
                    detail=ev.get("detail", {}),
                )
                evidences.append(evidence)

            logger.info(
                "metric_agent_completed",
                service_name=service_name,
                evidence_count=len(evidences),
            )

            return evidences

        except Exception as e:
            logger.error("metric_agent_failed", error=str(e))
            return []
