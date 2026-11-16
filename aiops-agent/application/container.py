"""依赖注入容器"""

from typing import Optional

import structlog

from application.agents.diagnosis_graph import build_diagnosis_graph
from application.agents.log_agent import LogAgent
from application.agents.metric_agent import MetricAgent
from application.agents.rca_agent import RCAAgent
from application.agents.tools import AgentTools
from application.agents.trace_agent import TraceAgent
from application.services.diagnosis_application_service import (
    DiagnosisApplicationService,
)
from application.services.diagnosis_engine_service import DiagnosisEngineService
from application.services.event_handler_service import EventHandlerService
from config.settings import settings
from infrastructure.cache.redis_client import RedisClient
from infrastructure.external.loki_client import LokiClient
from infrastructure.external.prometheus_client import PrometheusClient
from infrastructure.external.tempo_client import TempoClient
from infrastructure.llm.llm_client import LLMClient
from infrastructure.messaging.event_publisher import EventPublisher
from infrastructure.messaging.kafka_producer import KafkaProducer
from infrastructure.persistence.database import init_engine

logger = structlog.get_logger(__name__)


class Container:
    """依赖注入容器

    职责：管理应用级别的依赖
    """

    def __init__(self):
        self._redis_client: Optional[RedisClient] = None
        self._kafka_producer: Optional[KafkaProducer] = None
        self._event_publisher: Optional[EventPublisher] = None
        self._diagnosis_service: Optional[DiagnosisApplicationService] = None
        self._event_handler_service: Optional[EventHandlerService] = None
        self._llm_client: Optional[LLMClient] = None
        self._diagnosis_engine: Optional[DiagnosisEngineService] = None

    async def init(self) -> None:
        """初始化容器"""
        logger.info("container_init_start")

        # 初始化数据库引擎
        init_engine()

        # 初始化 Redis 客户端
        self._redis_client = RedisClient()
        await self._redis_client.connect()

        # 初始化 Kafka 生产者
        if settings.kafka_enabled:
            self._kafka_producer = KafkaProducer()
            await self._kafka_producer.connect()

        # 初始化事件发布器
        self._event_publisher = EventPublisher(self._kafka_producer)

        # 初始化 LLM 客户端
        self._llm_client = LLMClient()
        await self._llm_client.connect()

        # 初始化外部服务客户端
        prometheus_client = PrometheusClient()
        loki_client = LokiClient()
        tempo_client = TempoClient()

        # 初始化 Agent 工具集
        tools = AgentTools(
            prometheus_client=prometheus_client,
            loki_client=loki_client,
            tempo_client=tempo_client,
        )

        # 初始化 4 个 Agent
        metric_agent = MetricAgent(llm_client=self._llm_client, tools=tools)
        log_agent = LogAgent(llm_client=self._llm_client, tools=tools)
        trace_agent = TraceAgent(llm_client=self._llm_client, tools=tools)
        rca_agent = RCAAgent(llm_client=self._llm_client)

        # 构建 LangGraph
        diagnosis_graph = build_diagnosis_graph(
            metric_agent=metric_agent,
            log_agent=log_agent,
            trace_agent=trace_agent,
            rca_agent=rca_agent,
        )

        # 初始化诊断引擎
        self._diagnosis_engine = DiagnosisEngineService(graph=diagnosis_graph)

        # 初始化应用服务
        self._diagnosis_service = DiagnosisApplicationService(
            self._redis_client, self._diagnosis_engine
        )

        # 初始化事件处理服务
        self._event_handler_service = EventHandlerService(
            self._redis_client, self._event_publisher
        )

        logger.info("container_init_completed")

    async def close(self) -> None:
        """关闭容器"""
        logger.info("container_close_start")

        if self._llm_client:
            await self._llm_client.close()

        if self._kafka_producer:
            await self._kafka_producer.close()

        if self._redis_client:
            await self._redis_client.close()

        logger.info("container_close_completed")

    @property
    def diagnosis_service(self) -> DiagnosisApplicationService:
        """获取诊断应用服务"""
        if not self._diagnosis_service:
            raise RuntimeError("Container not initialized")
        return self._diagnosis_service

    @property
    def diagnosis_engine(self) -> DiagnosisEngineService:
        """获取诊断引擎"""
        if not self._diagnosis_engine:
            raise RuntimeError("Container not initialized")
        return self._diagnosis_engine

    @property
    def event_handler_service(self) -> EventHandlerService:
        """获取事件处理服务"""
        if not self._event_handler_service:
            raise RuntimeError("Container not initialized")
        return self._event_handler_service

    @property
    def redis_client(self) -> RedisClient:
        """获取 Redis 客户端"""
        if not self._redis_client:
            raise RuntimeError("Container not initialized")
        return self._redis_client


# 全局容器实例
container = Container()
