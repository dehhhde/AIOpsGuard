"""诊断领域模型

与前端数据契约（frontend/src/types/diagnosis.ts）保持语义一致，
序列化为 camelCase JSON 的职责由 application/dto 与 application/mappers 承担。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class DiagnosisStatus(str, Enum):
    """诊断状态"""

    PENDING = "pending"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class DiagnosisStage(str, Enum):
    """诊断阶段，与 LangGraph 节点顺序保持一致"""

    COLLECTING = "collecting"
    METRIC = "metric"
    LOG = "log"
    TRACE = "trace"
    RCA = "rca"
    REPORT = "report"


class EvidenceType(str, Enum):
    """证据类型"""

    METRIC = "METRIC"
    LOG = "LOG"
    TRACE = "TRACE"


class DiagnosisTriggerType(str, Enum):
    """诊断触发方式"""

    MANUAL = "manual"
    ALERT = "alert"
    SCHEDULE = "schedule"


@dataclass
class TimeRange:
    """时间窗（ISO 8601 字符串）"""

    start: str
    end: str


@dataclass
class RootCause:
    """根因"""

    rank: int
    cause: str
    confidence: float
    evidence_ids: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class Evidence:
    """证据"""

    id: str
    type: EvidenceType
    summary: str
    source: str
    time_range: TimeRange
    detail: dict[str, Any] = field(default_factory=dict)
    metric_name: Optional[str] = None
    instance: Optional[str] = None
    dashboard_uid: Optional[str] = None
    panel_id: Optional[int] = None


@dataclass
class ReportSection:
    """报告章节"""

    title: str
    content: str
    collapsed: bool = False


@dataclass
class DiagnosisReport:
    """诊断报告"""

    diagnosis_id: str
    generated_at: str
    summary: str
    sections: list[ReportSection] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class DiagnosisSession:
    """诊断会话聚合根"""

    diagnosis_id: str
    service_name: str
    started_at: str
    status: DiagnosisStatus = DiagnosisStatus.PENDING
    service_instance: Optional[str] = None
    stage: Optional[DiagnosisStage] = None
    progress: int = 0
    finished_at: Optional[str] = None
    trigger_type: DiagnosisTriggerType = DiagnosisTriggerType.MANUAL
    time_range: Optional[TimeRange] = None
    root_causes: list[RootCause] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    report: Optional[DiagnosisReport] = None

    @property
    def is_terminal(self) -> bool:
        """是否处于终态"""
        return self.status in (DiagnosisStatus.COMPLETED, DiagnosisStatus.FAILED)

    @property
    def is_running(self) -> bool:
        """是否进行中"""
        return self.status in (DiagnosisStatus.PENDING, DiagnosisStatus.COLLECTING, DiagnosisStatus.ANALYZING)


@dataclass
class DiagnosisTimeWindow:
    """诊断触发入参（时间窗以 datetime 表达，由 DTO 转换而来）"""

    target_service: str
    start_time: datetime
    end_time: datetime
    trigger_type: DiagnosisTriggerType = DiagnosisTriggerType.MANUAL
