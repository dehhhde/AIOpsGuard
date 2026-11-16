"""证据实体"""
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import uuid4

from ..enums import EvidenceType
from ..value_objects.time_range import TimeRange


@dataclass
class Evidence:
    """证据实体
    
    代表一条诊断证据（指标、日志或链路）
    
    特性：
    - 有唯一标识（id）
    - 分为三类：METRIC、LOG、TRACE
    - 包含时间范围
    - 包含详细信息（detail）
    - 包含 Grafana 跳转参数（用于前端深链）
    """
    
    type: EvidenceType  # 证据类型
    summary: str  # 摘要
    source: str  # 来源（指标名、日志来源、链路 ID）
    time_range: TimeRange  # 时间范围
    detail: dict[str, Any] = field(default_factory=dict)  # 详细信息
    id: str = field(default_factory=lambda: str(uuid4()))  # 唯一标识
    
    # 用于 Grafana 跳转（可选）
    instance: Optional[str] = None  # 实例地址
    metric_name: Optional[str] = None  # 指标名
    dashboard_uid: Optional[str] = None  # Dashboard UID
    panel_id: Optional[int] = None  # Panel ID
    
    def __post_init__(self) -> None:
        """验证证据"""
        if not self.summary or not self.summary.strip():
            raise ValueError("证据摘要不能为空")
        
        if not self.source or not self.source.strip():
            raise ValueError("证据来源不能为空")
    
    def is_metric_evidence(self) -> bool:
        """判断是否为指标证据"""
        return self.type == EvidenceType.METRIC
    
    def is_log_evidence(self) -> bool:
        """判断是否为日志证据"""
        return self.type == EvidenceType.LOG
    
    def is_trace_evidence(self) -> bool:
        """判断是否为链路证据"""
        return self.type == EvidenceType.TRACE
    
    def to_dict(self) -> dict:
        """转换为字典（与前端 TypeScript 类型对齐）"""
        return {
            "id": self.id,
            "type": self.type.value,
            "summary": self.summary,
            "source": self.source,
            "timeRange": self.time_range.to_dict(),
            "detail": self.detail,
            "instance": self.instance,
            "metricName": self.metric_name,
            "dashboardUid": self.dashboard_uid,
            "panelId": self.panel_id,
        }
    
    def __str__(self) -> str:
        return f"[{self.type.value}] {self.summary}"
