"""DTO 映射器"""

from datetime import datetime
from typing import List

from application.dto.responses import (
    DiagnosisReportResponse,
    DiagnosisSessionResponse,
    EvidenceResponse,
    RootCauseResponse,
)
from domain.models.diagnosis_session import DiagnosisSession
from domain.models.evidence import Evidence
from domain.models.report import Report
from domain.models.root_cause import RootCause


class DiagnosisDTOMapper:
    """诊断 DTO 映射器"""

    @staticmethod
    def to_session_response(session: DiagnosisSession) -> DiagnosisSessionResponse:
        """领域模型转响应 DTO"""
        return DiagnosisSessionResponse(
            session_id=session.diagnosis_id,
            service_name=session.service.service_name,
            service_instance=session.service.service_instance,
            environment=session.service.environment,
            status=session.status.value,
            current_stage=session.stage.value if session.stage else None,
            progress=session.progress,
            start_time=session.time_range.start_time,
            end_time=session.time_range.end_time,
            created_at=session.started_at or session.time_range.start_time,
            updated_at=session.finished_at or datetime.now(),
            error_message=session.error_message,
        )

    @staticmethod
    def to_evidence_response(evidence: Evidence) -> EvidenceResponse:
        """证据转响应 DTO"""
        return EvidenceResponse(
            id=evidence.id,
            evidence_type=evidence.type.value,
            source=evidence.source,
            summary=evidence.summary,
            detail=str(evidence.detail) if evidence.detail else None,
            confidence=85,  # 证据本身没有置信度，使用默认值
            timestamp=evidence.time_range.start_time,
        )

    @staticmethod
    def to_root_cause_response(root_cause: RootCause) -> RootCauseResponse:
        """根因转响应 DTO"""
        return RootCauseResponse(
            id=root_cause.id,
            problem_type="unknown",  # RootCause 没有 problem_type 字段
            summary=root_cause.cause,
            reasoning=f"基于 {len(root_cause.evidence_ids)} 条证据",
            confidence=root_cause.confidence.value,
            recommendations=[],  # RootCause 没有 recommendations 字段
        )

    @staticmethod
    def to_report_response(session: DiagnosisSession) -> DiagnosisReportResponse:
        """诊断报告转响应 DTO（从 session 提取）"""
        if not session.report:
            raise ValueError("诊断会话中没有报告")

        return DiagnosisReportResponse(
            session=DiagnosisDTOMapper.to_session_response(session),
            evidences=[
                DiagnosisDTOMapper.to_evidence_response(e) for e in session.evidence
            ],
            root_causes=[
                DiagnosisDTOMapper.to_root_cause_response(rc)
                for rc in session.root_causes
            ],
            summary=session.report.content[:500],  # 取前 500 字符作为摘要
        )
