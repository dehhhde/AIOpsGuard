"""模拟诊断引擎

在阶段六的 LangGraph 编排与真实数据采集实现之前，本引擎以固定节奏推进诊断阶段，
生成模板化的根因、证据与报告，用于支撑前端真实接口联调（任务 9.9.1 / 9.9.2）。
接入真实 Agent 后，由 application/agents 中的编排器替换本引擎的阶段推进逻辑，
进度推送与 REST 契约保持不变。
"""
from __future__ import annotations

import asyncio
import math
from datetime import datetime, timezone
from typing import Callable, Optional

import structlog

from domain.models.diagnosis import (
    DiagnosisSession,
    DiagnosisStage,
    DiagnosisStatus,
    DiagnosisTimeWindow,
    Evidence,
    EvidenceType,
    ReportSection,
    RootCause,
    TimeRange,
)
from domain.repositories.diagnosis_repository import DiagnosisRepository

logger = structlog.get_logger()

STAGE_FLOW: list[DiagnosisStage] = [
    DiagnosisStage.COLLECTING,
    DiagnosisStage.METRIC,
    DiagnosisStage.LOG,
    DiagnosisStage.TRACE,
    DiagnosisStage.RCA,
    DiagnosisStage.REPORT,
]

STAGE_INTERVAL_SECONDS = 2.0
METRIC_POINT_COUNT = 150


def _now_iso() -> str:
    """当前 UTC 时间的 ISO 8601 字符串"""
    return datetime.now(timezone.utc).isoformat()


def _seed_random(seed_text: str) -> Callable[[], float]:
    """与前端 mock/metrics.ts 一致的确定性伪随机数生成器"""
    seed = sum(ord(char) for char in seed_text) + 7

    def random() -> float:
        nonlocal seed
        seed = (seed * 9301 + 49297) % 233280
        return seed / 233280

    return random


class DiagnosisEngine:
    """诊断编排引擎：触发会话、推进阶段、广播进度事件"""

    def __init__(self, repository: DiagnosisRepository) -> None:
        self._repository = repository
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._subscribers: dict[str, set[asyncio.Queue[dict]]] = {}

    # ------------------------------------------------------------------ 生命周期

    async def start(self) -> None:
        """应用启动钩子：预置演示数据，保证首次访问列表与历史页不为空"""
        await self._seed_demo_sessions()
        logger.info("diagnosis_engine_started")

    async def shutdown(self) -> None:
        """应用关闭钩子：取消所有进行中的诊断任务"""
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()
        logger.info("diagnosis_engine_stopped")

    # ------------------------------------------------------------------ 公共接口

    async def trigger(self, window: DiagnosisTimeWindow) -> DiagnosisSession:
        """创建诊断会话并启动阶段推进任务"""
        diagnosis_id = self._build_diagnosis_id()
        session = DiagnosisSession(
            diagnosis_id=diagnosis_id,
            service_name=window.target_service,
            service_instance=f"{window.target_service}-1:8080",
            status=DiagnosisStatus.PENDING,
            stage=DiagnosisStage.COLLECTING,
            progress=0,
            started_at=_now_iso(),
            time_range=TimeRange(
                start=window.start_time.isoformat(),
                end=window.end_time.isoformat(),
            ),
            trigger_type=window.trigger_type,
        )
        await self._repository.save(session)

        task = asyncio.create_task(self._run_pipeline(session.diagnosis_id))
        self._tasks[diagnosis_id] = task
        logger.info("diagnosis_triggered", diagnosis_id=diagnosis_id, service=session.service_name)
        return session

    def subscribe(self, diagnosis_id: str) -> asyncio.Queue[dict]:
        """注册进度订阅队列，调用方负责在断开后调用 unsubscribe"""
        queue: asyncio.Queue[dict] = asyncio.Queue()
        self._subscribers.setdefault(diagnosis_id, set()).add(queue)
        return queue

    def unsubscribe(self, diagnosis_id: str, queue: asyncio.Queue[dict]) -> None:
        """移除进度订阅队列"""
        handlers = self._subscribers.get(diagnosis_id)
        if handlers is not None:
            handlers.discard(queue)
            if not handlers:
                self._subscribers.pop(diagnosis_id, None)

    async def build_metric_groups(self, session: DiagnosisSession) -> list[dict]:
        """按会话时间窗生成 JVM / HTTP / 连接池三组指标数据"""
        start_ms = self._parse_timestamp_ms(session.time_range.start if session.time_range else None)
        end_ms = self._parse_timestamp_ms(session.time_range.end if session.time_range else None)
        if end_ms <= start_ms:
            end_ms = start_ms + 60 * 60 * 1000
        step = max(1000, math.floor((end_ms - start_ms) / METRIC_POINT_COUNT))

        heap_random = _seed_random("堆内存使用")
        non_heap_random = _seed_random("非堆内存使用")

        def heap_value(index: int) -> float:
            growth = (index / METRIC_POINT_COUNT) * 1150
            surge = (index - int(METRIC_POINT_COUNT * 0.4)) * 7 if index > METRIC_POINT_COUNT * 0.4 else 0
            return round(620 + growth + surge + heap_random() * 45, 2)

        def non_heap_value(_index: int) -> float:
            return round(180 + non_heap_random() * 35, 2)

        p50_random = _seed_random("P50 延迟")
        p95_random = _seed_random("P95 延迟")
        p99_random = _seed_random("P99 延迟")

        def p50_value(_index: int) -> float:
            return round(120 + p50_random() * 40, 2)

        def p95_value(index: int) -> float:
            return round(280 + math.sin(index / 12) * 60 + p95_random() * 80, 2)

        def p99_value(index: int) -> float:
            deterioration = (index - int(METRIC_POINT_COUNT * 0.45)) * 12 if index > METRIC_POINT_COUNT * 0.45 else 0
            return round(320 + deterioration + p99_random() * 120, 2)

        active_random = _seed_random("活跃连接")
        idle_random = _seed_random("空闲连接")
        pending_random = _seed_random("等待连接")

        def active_value(index: int) -> float:
            return round(4 + min(6, index / METRIC_POINT_COUNT) * 5 + active_random() * 2, 2)

        def idle_value(index: int) -> float:
            return round(max(1, 5 - (index / METRIC_POINT_COUNT) * 4 + idle_random() * 2), 2)

        def pending_value(index: int) -> float:
            return round(pending_random() * 18 if index > METRIC_POINT_COUNT * 0.35 else pending_random() * 2, 2)

        def series(name: str, unit: str, generator: Callable[[int], float]) -> dict:
            points: list[dict] = []
            for index in range(METRIC_POINT_COUNT):
                timestamp = datetime.fromtimestamp((start_ms + index * step) / 1000, tz=timezone.utc)
                points.append({"timestamp": timestamp.isoformat(), "value": generator(index)})
            return {"name": name, "unit": unit, "points": points}

        return [
            {
                "key": "jvm",
                "title": "JVM 内存",
                "description": "堆内存持续上升是本次诊断的核心指标证据",
                "series": [
                    series("堆内存使用", "MB", heap_value),
                    series("非堆内存使用", "MB", non_heap_value),
                ],
            },
            {
                "key": "http",
                "title": "HTTP 延迟",
                "description": "订单查询接口 P99 在故障窗口内明显劣化",
                "series": [
                    series("P50 延迟", "ms", p50_value),
                    series("P95 延迟", "ms", p95_value),
                    series("P99 延迟", "ms", p99_value),
                ],
            },
            {
                "key": "pool",
                "title": "HikariCP 连接池",
                "description": "pending 连接堆积，说明数据库等待放大接口耗时",
                "series": [
                    series("活跃连接", "个", active_value),
                    series("空闲连接", "个", idle_value),
                    series("等待连接", "个", pending_value),
                ],
            },
        ]

    # ------------------------------------------------------------------ 阶段推进

    async def _run_pipeline(self, diagnosis_id: str) -> None:
        """按固定节奏推进诊断阶段，直至终态"""
        try:
            session = await self._repository.get(diagnosis_id)
            if session is None:
                return

            for index, stage in enumerate(STAGE_FLOW):
                session.status = DiagnosisStatus.COLLECTING if stage == DiagnosisStage.COLLECTING else DiagnosisStatus.ANALYZING
                session.stage = stage
                session.progress = min(99, 8 + round(index / len(STAGE_FLOW) * 92))
                await self._repository.save(session)
                self._broadcast(session, "diagnosis.progress")
                await asyncio.sleep(STAGE_INTERVAL_SECONDS)
                session = await self._repository.get(diagnosis_id)
                if session is None:
                    return

            self._complete_session(session)
            await self._repository.save(session)
            self._broadcast(session, "diagnosis.completed")
            logger.info("diagnosis_completed", diagnosis_id=diagnosis_id)
        except asyncio.CancelledError:
            logger.info("diagnosis_pipeline_cancelled", diagnosis_id=diagnosis_id)
            raise
        except Exception as exc:  # noqa: BLE001 —— 引擎内部兜底，避免未捕获异常导致任务静默消失
            logger.error("diagnosis_pipeline_failed", diagnosis_id=diagnosis_id, error=str(exc))
            session = await self._repository.get(diagnosis_id)
            if session is not None and not session.is_terminal:
                session.status = DiagnosisStatus.FAILED
                session.finished_at = _now_iso()
                await self._repository.save(session)
                self._broadcast(session, "diagnosis.failed")
        finally:
            self._tasks.pop(diagnosis_id, None)

    def _complete_session(self, session: DiagnosisSession) -> None:
        """填充模板化的根因、证据与报告"""
        session.status = DiagnosisStatus.COMPLETED
        session.stage = DiagnosisStage.REPORT
        session.progress = 100
        session.finished_at = _now_iso()
        window = session.time_range or TimeRange(start=session.started_at, end=session.finished_at or session.started_at)

        if not session.evidence:
            session.evidence = [
                Evidence(
                    id=f"{session.diagnosis_id}-ev-1",
                    type=EvidenceType.METRIC,
                    summary="堆内存 40 分钟内从 620MB 升至 1.7GB，GC 后回收不足",
                    source="Prometheus / jvm_memory_used_bytes",
                    time_range=window,
                    detail={"metric": "jvm_memory_used_bytes", "area": "heap", "growth_mb_per_min": 27},
                    metric_name="jvm_memory_used_bytes",
                    instance=session.service_instance,
                    dashboard_uid="aiops-target-app-jvm",
                    panel_id=12,
                ),
                Evidence(
                    id=f"{session.diagnosis_id}-ev-2",
                    type=EvidenceType.LOG,
                    summary="订单查询接口出现 43 次 ConnectionTimeout，集中在等待连接获取",
                    source="Loki / {service=\"order-service\"}",
                    time_range=window,
                    detail={"pattern": "HikariPool-1 - Connection is not available", "count": 43},
                    instance=session.service_instance,
                    dashboard_uid="aiops-target-app-logs",
                ),
                Evidence(
                    id=f"{session.diagnosis_id}-ev-3",
                    type=EvidenceType.TRACE,
                    summary="P99 链路耗时 4.2s，其中数据库等待占比 82%",
                    source="Tempo / trace query",
                    time_range=window,
                    detail={"p99_ms": 4200, "db_wait_ratio": 0.82, "slow_span": "jdbc/query"},
                    instance=session.service_instance,
                    dashboard_uid="aiops-target-app-traces",
                ),
            ]

        evidence_ids = [item.id for item in session.evidence]
        if not session.root_causes:
            session.root_causes = [
                RootCause(
                    rank=1,
                    cause="内存泄漏导致频繁 Full GC，引发停顿与连接释放延迟",
                    confidence=0.86,
                    evidence_ids=[evidence_ids[0], evidence_ids[2]],
                    recommendations=[
                        "对缓存对象设置上限与过期时间，排查无界集合",
                        "获取堆转储并使用 MAT 分析支配树",
                    ],
                ),
                RootCause(
                    rank=2,
                    cause="HikariCP 连接池容量不足，高并发下请求排队放大接口耗时",
                    confidence=0.72,
                    evidence_ids=[evidence_ids[1], evidence_ids[2]],
                    recommendations=["评估 maximum-pool-size 至 20 并观察等待队列", "为慢查询添加索引，缩短连接占用时间"],
                ),
            ]

        if session.report is None:
            session.report = DiagnosisReport(
                diagnosis_id=session.diagnosis_id,
                generated_at=session.finished_at or _now_iso(),
                summary="order-service 在诊断时间窗内出现接口延迟劣化，主因是堆内存持续上升引发频繁 Full GC，"
                "叠加连接池等待，共同放大了 P99 耗时。",
                sections=[
                    ReportSection(title="故障概述", content="诊断窗口内 P99 延迟由 320ms 升至 4.2s，错误率上升至 2.3%。"),
                    ReportSection(
                        title="分析过程",
                        content="指标分析确认堆内存线性上升；日志聚类发现大量连接获取超时；链路分析显示数据库等待占比 82%。",
                    ),
                    ReportSection(title="影响范围", content="order-service 全部实例，下游 delivery-service 间接受到排队影响。"),
                ],
                recommendations=[
                    "短期：重启受影响实例并临时调大堆内存上限",
                    "中期：修复无界缓存，为连接池增加容量告警",
                    "长期：为 Full GC 频次与连接等待建立常态化监控",
                ],
            )

    # ------------------------------------------------------------------ 内部工具

    def _broadcast(self, session: DiagnosisSession, event: str) -> None:
        """向订阅者推送进度事件，无订阅者时静默跳过"""
        handlers = self._subscribers.get(session.diagnosis_id)
        if not handlers:
            return
        payload = {
            "event": event,
            "diagnosisId": session.diagnosis_id,
            "status": session.status.value,
            "stage": session.stage.value if session.stage else None,
            "progress": session.progress,
            "timestamp": _now_iso(),
        }
        for queue in tuple(handlers):
            queue.put_nowait(payload)

    def _build_diagnosis_id(self) -> str:
        """按 diag-YYYYMMDDHHMMSS 生成诊断 ID，与前端展示约定一致"""
        return f"diag-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    @staticmethod
    def _parse_timestamp_ms(value: Optional[str]) -> float:
        """解析 ISO 时间戳，失败时回退到一小时前"""
        if not value:
            return datetime.now(timezone.utc).timestamp() * 1000 - 60 * 60 * 1000
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000
        except ValueError:
            return datetime.now(timezone.utc).timestamp() * 1000 - 60 * 60 * 1000

    async def _seed_demo_sessions(self) -> None:
        """预置 2 个已完成 + 1 个进行中的演示会话"""
        demo_specs = [
            ("order-service", 26, DiagnosisStatus.COMPLETED),
            ("payment-service", 8, DiagnosisStatus.COMPLETED),
            ("order-service", 1, DiagnosisStatus.ANALYZING),
        ]
        for service, hours_ago, status in demo_specs:
            started = datetime.fromtimestamp(datetime.now(timezone.utc).timestamp() - hours_ago * 3600, tz=timezone.utc)
            window_start = datetime.fromtimestamp(started.timestamp() - 1800, tz=timezone.utc)
            window_end = started
            created = await self.trigger(
                DiagnosisTimeWindow(
                    target_service=service,
                    start_time=window_start,
                    end_time=window_end,
                )
            )
            if status == DiagnosisStatus.COMPLETED:
                # 直接推演到终态，避免等待流水线真实跑完
                current = await self._repository.get(created.diagnosis_id)
                if current is not None:
                    task = self._tasks.pop(created.diagnosis_id, None)
                    if task is not None:
                        task.cancel()
                    started_iso = started.isoformat()
                    current.started_at = started_iso
                    current.time_range = TimeRange(start=window_start.isoformat(), end=window_end.isoformat())
                    self._complete_session(current)
                    # 保留已完成会话的原始时间语义
                    current.started_at = started_iso
                    current.finished_at = datetime.fromtimestamp(
                        started.timestamp() + 9 * 60, tz=timezone.utc
                    ).isoformat()
                    await self._repository.save(current)
