"""响应 DTO"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DiagnosisSessionResponse(BaseModel):
    """诊断会话响应"""

    session_id: str
    service_name: str
    service_instance: Optional[str]
    environment: str
    status: str
    current_stage: Optional[str]
    progress: int
    start_time: datetime
    end_time: datetime
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class EvidenceResponse(BaseModel):
    """证据响应"""

    id: str
    evidence_type: str
    source: str
    summary: str
    detail: Optional[str]
    confidence: int
    timestamp: datetime


class RootCauseResponse(BaseModel):
    """根因响应"""

    id: str
    problem_type: str
    summary: str
    reasoning: str
    confidence: int
    recommendations: List[str]


class DiagnosisReportResponse(BaseModel):
    """诊断报告响应"""

    session: DiagnosisSessionResponse
    evidences: List[EvidenceResponse]
    root_causes: List[RootCauseResponse]
    summary: str

    class Config:
        from_attributes = True


class TriggerDiagnosisResponse(BaseModel):
    """触发诊断响应"""

    session_id: str
    status: str
    message: str
