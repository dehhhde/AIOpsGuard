"""诊断 Graph 构建"""

from datetime import datetime

import structlog
from langgraph.graph import END, StateGraph

from application.agents.diagnosis_state import DiagnosisState
from application.agents.log_agent import LogAgent
from application.agents.metric_agent import MetricAgent
from application.agents.rca_agent import RCAAgent
from application.agents.trace_agent import TraceAgent
from domain.value_objects.time_range import TimeRange

logger = structlog.get_logger(__name__)


def build_diagnosis_graph(
    metric_agent: MetricAgent,
    log_agent: LogAgent,
    trace_agent: TraceAgent,
    rca_agent: RCAAgent,
) -> StateGraph:
    """构建诊断 Graph

    工作流程：
    1. Metric Agent 收集指标证据
    2. Log Agent 收集日志证据
    3. Trace Agent 收集链路证据
    4. RCA Agent 综合分析推理根因

    Args:
        metric_agent: 指标 Agent
        log_agent: 日志 Agent
        trace_agent: 链路 Agent
        rca_agent: 根因分析 Agent

    Returns:
        编译后的 StateGraph
    """

    # 定义节点
    async def metric_node(state: DiagnosisState) -> DiagnosisState:
        """Metric Agent 节点"""
        logger.info("metric_node_start", service=state["service_name"])

        time_range = TimeRange(
            start_time=datetime.fromisoformat(state["start_time"]),
            end_time=datetime.fromisoformat(state["end_time"]),
        )

        evidences = await metric_agent.analyze(
            service_name=state["service_name"],
            time_range=time_range,
        )

        state["metric_evidences"] = evidences
        logger.info("metric_node_completed", evidence_count=len(evidences))
        return state

    async def log_node(state: DiagnosisState) -> DiagnosisState:
        """Log Agent 节点"""
        logger.info("log_node_start", service=state["service_name"])

        time_range = TimeRange(
            start_time=datetime.fromisoformat(state["start_time"]),
            end_time=datetime.fromisoformat(state["end_time"]),
        )

        evidences = await log_agent.analyze(
            service_name=state["service_name"],
            time_range=time_range,
        )

        state["log_evidences"] = evidences
        logger.info("log_node_completed", evidence_count=len(evidences))
        return state

    async def trace_node(state: DiagnosisState) -> DiagnosisState:
        """Trace Agent 节点"""
        logger.info("trace_node_start", service=state["service_name"])

        time_range = TimeRange(
            start_time=datetime.fromisoformat(state["start_time"]),
            end_time=datetime.fromisoformat(state["end_time"]),
        )

        evidences = await trace_agent.analyze(
            service_name=state["service_name"],
            time_range=time_range,
        )

        state["trace_evidences"] = evidences
        logger.info("trace_node_completed", evidence_count=len(evidences))
        return state

    async def rca_node(state: DiagnosisState) -> DiagnosisState:
        """RCA Agent 节点"""
        logger.info("rca_node_start", service=state["service_name"])

        # 收集所有证据
        all_evidences = (
            state.get("metric_evidences", [])
            + state.get("log_evidences", [])
            + state.get("trace_evidences", [])
        )

        time_range = TimeRange(
            start_time=datetime.fromisoformat(state["start_time"]),
            end_time=datetime.fromisoformat(state["end_time"]),
        )

        root_causes = await rca_agent.analyze(
            service_name=state["service_name"],
            time_range=time_range,
            evidences=all_evidences,
        )

        state["root_causes"] = root_causes
        state["summary"] = f"诊断完成，发现 {len(root_causes)} 个根因"
        logger.info("rca_node_completed", root_cause_count=len(root_causes))
        return state

    # 构建 Graph
    workflow = StateGraph(DiagnosisState)

    # 添加节点
    workflow.add_node("metric_agent", metric_node)
    workflow.add_node("log_agent", log_node)
    workflow.add_node("trace_agent", trace_agent)
    workflow.add_node("rca_agent", rca_node)

    # 定义边（顺序执行：metric -> log -> trace -> rca）
    # 注意：如果需要并行执行，可以使用 LangGraph 的 parallel 功能
    workflow.set_entry_point("metric_agent")
    workflow.add_edge("metric_agent", "log_agent")
    workflow.add_edge("log_agent", "trace_agent")
    workflow.add_edge("trace_agent", "rca_agent")
    workflow.add_edge("rca_agent", END)

    return workflow.compile()
