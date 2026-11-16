"""诊断 REST 接口 DTO

字段序列化为 camelCase，与前端 frontend/src/types/diagnosis.ts 的契约一致。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """camelCase 序列化基类"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class TriggerRequest(CamelModel):
    """诊断触发请求"""

    target_service: str
    start_time: datetime
    end_time: datetime


class TriggerResponse(CamelModel):
    """诊断触发响应"""

    diagnosis_id: str
    status: str
    message: str


class TimeRangeDto(CamelModel):
    """时间窗"""

    start: str
    end: str


class RootCauseDto(CamelModel):
    """根因"""

    rank: int
    cause: str
    confidence: float
    evidence_ids: list[str] = []
    recommendations: list[str] = []


class EvidenceDto(CamelModel):
    """证据"""

    id: str
    type: str
    summary: str
    source: str
    time_range: TimeRangeDto
    detail: dict[str, Any] = {}
    metric_name: Optional[str] = None
    instance: Optional[str] = None
    dashboard_uid: Optional[str] = None
    panel_id: Optional[int] = None


class ReportSectionDto(CamelModel):
    """报告章节"""

    title: str
    content: str
    collapsed: bool = False


class DiagnosisReportDto(CamelModel):
    """诊断报告"""

    diagnosis_id: str
    generated_at: str
    summary: str
    sections: list[ReportSectionDto] = []
    recommendations: list[str] = []


class DiagnosisSessionDto(CamelModel):
    """诊断会话"""

    diagnosis_id: str
    service_name: str
    status: str
    started_at: str
    service_instance: Optional[str] = None
    stage: Optional[str] = None
    progress: int = 0
    finished_at: Optional[str] = None
    trigger_type: Optional[str] = None
    time_range: Optional[TimeRangeDto] = None
    root_causes: list[RootCauseDto] = []
    evidence: list[EvidenceDto] = []
    report: Optional[DiagnosisReportDto] = None


class PageResultDto(CamelModel):
    """分页结果"""

    items: list[DiagnosisSessionDto]
    total: int
    page: int
    page_size: int


class OverviewStatsDto(CamelModel):
    """工作台概览统计"""

    total_today: int
    success_rate: float
    avg_duration_ms: int
    running_count: int


class MetricPointDto(CamelModel):
    """指标数据点"""

    timestamp: str
    value: float


class MetricSeriesDto(CamelModel):
    """指标序列"""

    name: str
    unit: str
    points: list[MetricPointDto]


class MetricGroupDto(CamelModel):
    """指标分组"""

    key: str
    title: str
    description: str
    series: list[MetricSeriesDto]
