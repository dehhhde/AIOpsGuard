"""Kafka 生产者"""
from aiokafka import AIOKafkaProducer
import json
from typing import Any, Optional
import structlog

from config.settings import settings

logger = structlog.get_logger(__name__)


class KafkaProducer:
    """Kafka 生产者
    
    职责：发布消息到 Kafka
    
    特性：
    - 异步发送
    - 支持禁用（降级）
    - JSON 序列化
    """
    
    def __init__(self):
        """初始化生产者"""
        self.enabled = settings.kafka_enabled
        self.producer: Optional[AIOKafkaProducer] = None
        
        if self.enabled:
            logger.info(
                "kafka_producer_initialized",
                bootstrap_servers=settings.kafka_bootstrap_servers
            )
        else:
            logger.info("kafka_producer_disabled")
    
    async def start(self):
        """启动生产者"""
        if not self.enabled:
            logger.debug("kafka_disabled_skip_start")
            return
        
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            await self.producer.start()
            logger.info("kafka_producer_started")
        except Exception as e:
            logger.error("kafka_producer_start_failed", error=str(e))
            self.producer = None
    
    async def stop(self):
        """停止生产者"""
        if self.producer:
            try:
                await self.producer.stop()
                logger.info("kafka_producer_stopped")
            except Exception as e:
                logger.error("kafka_producer_stop_failed", error=str(e))
    
    async def send(
        self,
        topic: str,
        message: dict[str, Any],
        key: Optional[str] = None
    ) -> bool:
        """发送消息
        
        Args:
            topic: Topic 名称
            message: 消息内容（字典，会自动序列化为 JSON）
            key: 消息键（可选，用于分区）
        
        Returns:
            是否发送成功
        """
        if not self.enabled or not self.producer:
            logger.debug(
                "kafka_disabled_skip_send",
                topic=topic,
                key=key
            )
            return False
        
        try:
            await self.producer.send(
                topic,
                value=message,
                key=key
            )
            
            logger.debug(
                "kafka_message_sent",
                topic=topic,
                key=key,
                message_type=message.get("event_type")
            )
            return True
            
        except Exception as e:
            logger.error(
                "kafka_send_failed",
                topic=topic,
                key=key,
                error=str(e)
            )
            return False
    
    async def send_batch(
        self,
        topic: str,
        messages: list[dict[str, Any]]
    ) -> int:
        """批量发送消息
        
        Args:
            topic: Topic 名称
            messages: 消息列表
        
        Returns:
            成功发送的消息数量
        """
        if not self.enabled or not self.producer:
            logger.debug("kafka_disabled_skip_batch_send", topic=topic)
            return 0
        
        success_count = 0
        
        for message in messages:
            key = message.get("id") or message.get("diagnosis_id")
            if await self.send(topic, message, key=key):
                success_count += 1
        
        logger.info(
            "kafka_batch_sent",
            topic=topic,
            total=len(messages),
            success=success_count
        )
        
        return success_count
    
    async def flush(self):
        """刷新缓冲区，确保所有消息已发送"""
        if self.producer:
            try:
                await self.producer.flush()
                logger.debug("kafka_producer_flushed")
            except Exception as e:
                logger.error("kafka_flush_failed", error=str(e))
