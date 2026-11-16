"""诊断状态定义"""

from typing import List, Optional, TypedDict

from domain.models.evidence import Evidence
from domain.models.root_cause import RootCause


class DiagnosisState(TypedDict, total=False):
    """诊断状态

    LangGraph 状态机的状态定义
    """

    # 输入
    service_name: str
    start_time: str
    end_time: str

    # 中间状态
    metric_evidences: List[Evidence]
    log_evidences: List[Evidence]
    trace_evidences: List[Evidence]

    # 输出
    root_causes: List[RootCause]
    summary: str

    # 错误
    error: Optional[str]
