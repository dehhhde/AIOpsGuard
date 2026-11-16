"""领域事件发布器"""
from typing import Any
import structlog

from .kafka_producer import KafkaProducer
from domain.events.diagnosis_events import (
    DiagnosisTriggered,
    StageCompleted,
    DiagnosisCompleted,
    DiagnosisFailed
)

logger = structlog.get_logger(__name__)


class EventPublisher:
    """领域事件发布器
    
    职责：将领域事件发布到 Kafka
    
    特性：
    - 自动事件类型识别
    - 事件到消息的转换
    - 降级支持
    """
    
    def __init__(self, kafka_producer: KafkaProducer):
        """初始化事件发布器
        
        Args:
            kafka_producer: Kafka 生产者实例
        """
        self.kafka = kafka_producer
        self.topic = "events.diagnosis"
    
    async def publish(self, event: Any) -> bool:
        """发布领域事件
        
        Args:
            event: 领域事件对象
        
        Returns:
            是否发布成功
        """
        try:
            # 转换事件到消息格式
            message = self._event_to_message(event)
            
            if not message:
                logger.warning(
                    "event_to_message_failed_unknown_type",
                    event_type=type(event).__name__
                )
                return False
            
            # 发送到 Kafka
            success = await self.kafka.send(
                topic=self.topic,
                message=message,
                key=message.get("diagnosis_id")
            )
            
            if success:
                logger.info(
                    "event_published",
                    event_type=message["event_type"],
                    diagnosis_id=message.get("diagnosis_id")
                )
            
            return success
            
        except Exception as e:
            logger.error(
                "event_publish_failed",
                event_type=type(event).__name__,
                error=str(e)
            )
            return False
    
    async def publish_batch(self, events: list[Any]) -> int:
        """批量发布事件
        
        Args:
            events: 事件列表
        
        Returns:
            成功发布的事件数量
        """
        success_count = 0
        
        for event in events:
            if await self.publish(event):
                success_count += 1
        
        logger.info(
            "events_batch_published",
            total=len(events),
            success=success_count
        )
        
        return success_count
    
    def _event_to_message(self, event: Any) -> dict[str, Any] | None:
        """事件转消息
        
        将领域事件转换为 Kafka 消息格式
        
        Args:
            event: 领域事件对象
        
        Returns:
            消息字典，如果无法识别事件类型则返回 None
        """
        if isinstance(event, DiagnosisTriggered):
            return {
                "event_type": "DiagnosisTriggered",
                "diagnosis_id": event.diagnosis_id,
                "service_name": event.service_name,
                "service_instance": event.service_instance,
                "trigger_type": event.trigger_type,
                "triggered_at": event.triggered_at.isoformat(),
                "time_range": {
                    "start_time": event.time_range.start_time.isoformat(),
                    "end_time": event.time_range.end_time.isoformat()
                }
            }
        
        elif isinstance(event, StageCompleted):
            return {
                "event_type": "StageCompleted",
                "diagnosis_id": event.diagnosis_id,
                "stage": event.stage.value,
                "progress": event.progress,
                "evidence_count": event.evidence_count,
                "completed_at": event.completed_at.isoformat()
            }
        
        elif isinstance(event, DiagnosisCompleted):
            return {
                "event_type": "DiagnosisCompleted",
                "diagnosis_id": event.diagnosis_id,
                "service_name": event.service_name,
                "status": event.status.value,
                "root_cause_count": event.root_cause_count,
                "evidence_count": event.evidence_count,
                "duration_seconds": event.duration_seconds,
                "completed_at": event.completed_at.isoformat()
            }
        
        elif isinstance(event, DiagnosisFailed):
            return {
                "event_type": "DiagnosisFailed",
                "diagnosis_id": event.diagnosis_id,
                "service_name": event.service_name,
                "status": event.status.value,
                "stage": event.stage.value if event.stage else None,
                "error_message": event.error_message,
                "failed_at": event.failed_at.isoformat()
            }
        
        else:
            logger.warning(
                "unknown_event_type",
                event_type=type(event).__name__
            )
            return None
