"""事件处理服务"""

import structlog

from domain.events.diagnosis_events import (
    DiagnosisCompletedEvent,
    DiagnosisFailedEvent,
    DiagnosisTriggeredEvent,
    StageCompletedEvent,
)
from infrastructure.cache.redis_client import RedisClient
from infrastructure.cache.session_cache import SessionCache
from infrastructure.messaging.event_publisher import EventPublisher

logger = structlog.get_logger(__name__)


class EventHandlerService:
    """事件处理服务

    职责：
    1. 订阅领域事件
    2. 将领域事件发布到消息队列
    3. 更新缓存
    4. 记录审计日志
    """

    def __init__(self, redis_client: RedisClient, event_publisher: EventPublisher):
        self.cache = SessionCache(redis_client)
        self.event_publisher = event_publisher

    async def handle_diagnosis_triggered(self, event: DiagnosisTriggeredEvent) -> None:
        """处理诊断触发事件

        Args:
            event: 诊断触发事件
        """
        logger.info(
            "handle_diagnosis_triggered",
            session_id=event.session_id,
            service_name=event.service_name,
        )

        # 发布到消息队列
        await self.event_publisher.publish_event(
            topic="diagnosis.triggered",
            event_data={
                "event_type": "diagnosis_triggered",
                "session_id": event.session_id,
                "service_name": event.service_name,
                "trigger_type": event.trigger_type,
                "timestamp": event.timestamp.isoformat(),
            },
        )

        # 缓存会话（占位，实际需要完整数据）
        # await self.cache.set(event.session_id, session_data, ttl=3600)

    async def handle_stage_completed(self, event: StageCompletedEvent) -> None:
        """处理阶段完成事件

        Args:
            event: 阶段完成事件
        """
        logger.info(
            "handle_stage_completed",
            session_id=event.session_id,
            stage=event.stage,
            progress=event.progress,
        )

        # 发布到消息队列
        await self.event_publisher.publish_event(
            topic="diagnosis.stage_completed",
            event_data={
                "event_type": "stage_completed",
                "session_id": event.session_id,
                "stage": event.stage,
                "progress": event.progress,
                "timestamp": event.timestamp.isoformat(),
            },
        )

        # 更新缓存中的进度
        # cached_data = await self.cache.get(event.session_id)
        # if cached_data:
        #     cached_data["progress"] = event.progress
        #     await self.cache.set(event.session_id, cached_data, ttl=3600)

    async def handle_diagnosis_completed(self, event: DiagnosisCompletedEvent) -> None:
        """处理诊断完成事件

        Args:
            event: 诊断完成事件
        """
        logger.info(
            "handle_diagnosis_completed",
            session_id=event.session_id,
            duration=event.duration_seconds,
        )

        # 发布到消息队列
        await self.event_publisher.publish_event(
            topic="diagnosis.completed",
            event_data={
                "event_type": "diagnosis_completed",
                "session_id": event.session_id,
                "duration_seconds": event.duration_seconds,
                "timestamp": event.timestamp.isoformat(),
            },
        )

        # 缓存报告（延长 TTL）
        # await self.cache.set(event.session_id, report_data, ttl=86400)

    async def handle_diagnosis_failed(self, event: DiagnosisFailedEvent) -> None:
        """处理诊断失败事件

        Args:
            event: 诊断失败事件
        """
        logger.error(
            "handle_diagnosis_failed",
            session_id=event.session_id,
            error_message=event.error_message,
        )

        # 发布到消息队列
        await self.event_publisher.publish_event(
            topic="diagnosis.failed",
            event_data={
                "event_type": "diagnosis_failed",
                "session_id": event.session_id,
                "error_message": event.error_message,
                "timestamp": event.timestamp.isoformat(),
            },
        )

        # 清除缓存
        await self.cache.delete(event.session_id)
