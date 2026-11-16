"""诊断查询与触发 REST 路由

路径与字段契约遵循任务文档 09（9.9 解除阻塞条件）与前端 frontend/src/types/diagnosis.ts。
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from application.container import engine, repository
from application.dto.diagnosis_dto import (
    DiagnosisSessionDto,
    MetricGroupDto,
    OverviewStatsDto,
    PageResultDto,
    TriggerRequest,
    TriggerResponse,
)
from application.mappers.diagnosis_mapper import map_session
from domain.models.diagnosis import DiagnosisStatus, DiagnosisTimeWindow

router = APIRouter(prefix="/api/v1/diagnosis", tags=["Diagnosis"])


@router.get("")
async def list_sessions() -> list[DiagnosisSessionDto]:
    """查询全部诊断会话，按开始时间倒序"""
    sessions = await repository.list_all()
    ordered = sorted(sessions, key=lambda item: item.started_at, reverse=True)
    return [map_session(item) for item in ordered]


@router.get("/overview")
async def get_overview() -> OverviewStatsDto:
    """工作台概览统计：今日诊断数、成功率、平均耗时、进行中数量"""
    sessions = await repository.list_all()
    terminal = [item for item in sessions if item.is_terminal]
    completed = [item for item in terminal if item.status == DiagnosisStatus.COMPLETED]
    durations = []
    for item in terminal:
        if item.finished_at:
            started = _parse_iso(item.started_at)
            finished = _parse_iso(item.finished_at)
            if started is not None and finished is not None and finished > started:
                durations.append((finished - started).total_seconds() * 1000)
    return OverviewStatsDto(
        total_today=len(sessions),
        success_rate=(len(completed) / len(terminal)) if terminal else 0.0,
        avg_duration_ms=int(sum(durations) / len(durations)) if durations else 0,
        running_count=sum(1 for item in sessions if item.is_running),
    )


@router.get("/history")
async def get_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100, alias="pageSize"),
    service_name: Optional[str] = Query(default=None, alias="serviceName"),
    status: Optional[str] = Query(default=None),
    start_time: Optional[str] = Query(default=None, alias="startTime"),
    end_time: Optional[str] = Query(default=None, alias="endTime"),
) -> PageResultDto:
    """分页查询历史诊断，支持服务、状态与时间范围组合筛选"""
    sessions = await repository.list_all()
    start_ms = _parse_iso(start_time) if start_time else None
    end_ms = _parse_iso(end_time) if end_time else None

    filtered = []
    for item in sessions:
        if service_name and item.service_name != service_name:
            continue
        if status and item.status.value != status:
            continue
        started = _parse_iso(item.started_at)
        if started is None:
            continue
        if start_ms is not None and started < start_ms:
            continue
        if end_ms is not None and started > end_ms:
            continue
        filtered.append(item)

    filtered.sort(key=lambda item: item.started_at, reverse=True)
    offset = (page - 1) * page_size
    items = filtered[offset : offset + page_size]
    return PageResultDto(
        items=[map_session(item) for item in items],
        total=len(filtered),
        page=page,
        page_size=page_size,
    )


@router.post("/trigger")
async def trigger_diagnosis(request: TriggerRequest) -> TriggerResponse:
    """触发一次诊断，返回会话 ID 与受理状态"""
    if request.end_time <= request.start_time:
        raise HTTPException(status_code=422, detail="时间窗无效：endTime 必须晚于 startTime")
    session = await engine.trigger(
        DiagnosisTimeWindow(
            target_service=request.target_service,
            start_time=request.start_time,
            end_time=request.end_time,
        )
    )
    return TriggerResponse(
        diagnosis_id=session.diagnosis_id,
        status="processing",
        message="诊断任务已创建，正在采集数据",
    )


@router.get("/{diagnosis_id}")
async def get_detail(diagnosis_id: str) -> DiagnosisSessionDto:
    """按 ID 查询诊断会话详情"""
    session = await repository.get(diagnosis_id)
    if session is None:
        raise HTTPException(status_code=404, detail="诊断会话不存在或已过期")
    return map_session(session)


@router.get("/{diagnosis_id}/report")
async def get_report(diagnosis_id: str) -> Optional[object]:
    """查询诊断报告，未生成时返回 null"""
    session = await repository.get(diagnosis_id)
    if session is None:
        raise HTTPException(status_code=404, detail="诊断会话不存在或已过期")
    return map_session(session).report


@router.get("/{diagnosis_id}/metrics")
async def get_metrics(diagnosis_id: str) -> list[MetricGroupDto]:
    """查询会话时间窗内的指标趋势数据（JVM / HTTP / 连接池）"""
    session = await repository.get(diagnosis_id)
    if session is None:
        raise HTTPException(status_code=404, detail="诊断会话不存在或已过期")
    groups = await engine.build_metric_groups(session)
    return [MetricGroupDto.model_validate(group) for group in groups]


def _parse_iso(value: str):
    """解析 ISO 8601 时间戳，失败返回 None"""
    from datetime import datetime

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
