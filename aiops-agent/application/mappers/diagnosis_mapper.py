"""领域模型到 DTO 的映射器"""
from __future__ import annotations

from typing import Optional

from application.dto.diagnosis_dto import (
    DiagnosisReportDto,
    DiagnosisSessionDto,
    EvidenceDto,
    ReportSectionDto,
    RootCauseDto,
    TimeRangeDto,
)
from domain.models.diagnosis import DiagnosisReport, DiagnosisSession


def map_session(session: DiagnosisSession) -> DiagnosisSessionDto:
    """领域会话 → 会话 DTO"""
    return DiagnosisSessionDto(
        diagnosis_id=session.diagnosis_id,
        service_name=session.service_name,
        service_instance=session.service_instance,
        status=session.status.value,
        stage=session.stage.value if session.stage else None,
        progress=session.progress,
        started_at=session.started_at,
        finished_at=session.finished_at,
        trigger_type=session.trigger_type.value if session.trigger_type else None,
        time_range=(
            TimeRangeDto(start=session.time_range.start, end=session.time_range.end)
            if session.time_range
            else None
        ),
        root_causes=[
            RootCauseDto(
                rank=cause.rank,
                cause=cause.cause,
                confidence=cause.confidence,
                evidence_ids=list(cause.evidence_ids),
                recommendations=list(cause.recommendations),
            )
            for cause in session.root_causes
        ],
        evidence=[
            EvidenceDto(
                id=item.id,
                type=item.type.value,
                summary=item.summary,
                source=item.source,
                time_range=TimeRangeDto(start=item.time_range.start, end=item.time_range.end),
                detail=item.detail,
                metric_name=item.metric_name,
                instance=item.instance,
                dashboard_uid=item.dashboard_uid,
                panel_id=item.panel_id,
            )
            for item in session.evidence
        ],
        report=map_report(session.report),
    )


def map_report(report: Optional[DiagnosisReport]) -> Optional[DiagnosisReportDto]:
    """领域报告 → 报告 DTO；入参为 None 时返回 None"""
    if report is None:
        return None
    return DiagnosisReportDto(
        diagnosis_id=report.diagnosis_id,
        generated_at=report.generated_at,
        summary=report.summary,
        sections=[
            ReportSectionDto(title=section.title, content=section.content, collapsed=section.collapsed)
            for section in report.sections
        ],
        recommendations=list(report.recommendations),
    )
