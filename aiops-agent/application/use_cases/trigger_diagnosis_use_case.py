"""触发诊断用例"""

import asyncio
from datetime import datetime, timedelta

import structlog

from application.dto.requests import TriggerDiagnosisRequest
from application.dto.responses import TriggerDiagnosisResponse
from application.services.diagnosis_engine_service import DiagnosisEngineService
from domain.enums import TriggerType
from domain.models.diagnosis_session import DiagnosisSession
from domain.value_objects.service_identifier import ServiceIdentifier
from domain.value_objects.time_range import TimeRange
from infrastructure.cache.distributed_lock import DistributedLock
from infrastructure.cache.redis_client import RedisClient

logger = structlog.get_logger(__name__)


class DiagnosisAlreadyInProgressError(Exception):
    """诊断已在进行中异常"""

    pass


class TriggerDiagnosisUseCase:
    """触发诊断用例

    职责：
    1. 验证请求参数
    2. 使用分布式锁防止重复诊断
    3. 创建诊断会话
    4. 异步启动诊断流程
    """

    def __init__(
        self, redis_client: RedisClient, diagnosis_engine: DiagnosisEngineService
    ):
        self.lock = DistributedLock(redis_client)
        self.diagnosis_engine = diagnosis_engine

    async def execute(self, request: TriggerDiagnosisRequest) -> TriggerDiagnosisResponse:
        """执行用例

        Args:
            request: 触发诊断请求

        Returns:
            触发诊断响应

        Raises:
            DiagnosisAlreadyInProgressError: 服务正在诊断中
        """
        service_name = request.service_name
        lock_key = f"diagnosis:{service_name}"

        logger.info(
            "trigger_diagnosis_start",
            service_name=service_name,
            environment=request.environment,
        )

        # 尝试获取分布式锁
        try:
            async with self.lock.lock(
                resource=lock_key,
                ttl=300,  # 5 分钟
                wait=False,
            ):
                # 创建诊断会话
                session = await self._create_session(request)

                # 异步启动诊断（不阻塞响应）
                asyncio.create_task(self._run_diagnosis_async(session))

                logger.info(
                    "diagnosis_triggered",
                    session_id=session.diagnosis_id,
                    service_name=service_name,
                )

                return TriggerDiagnosisResponse(
                    session_id=session.diagnosis_id,
                    status="triggered",
                    message=f"Diagnosis for {service_name} has been triggered",
                )

        except RuntimeError:
            # 锁获取失败，服务正在诊断中
            logger.warning("diagnosis_already_in_progress", service_name=service_name)
            raise DiagnosisAlreadyInProgressError(
                f"Service {service_name} is already being diagnosed. "
                f"Please wait for the current diagnosis to complete."
            )

    async def _create_session(
        self, request: TriggerDiagnosisRequest
    ) -> DiagnosisSession:
        """创建诊断会话"""
        # 构建时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=request.time_range_minutes)
        time_range = TimeRange(start_time=start_time, end_time=end_time)

        # 构建服务标识
        service_identifier = ServiceIdentifier(
            service_name=request.service_name,
            service_instance=request.service_instance,
            environment=request.environment,
        )

        # 创建诊断会话
        session = DiagnosisSession(
            diagnosis_id=f"diag-{datetime.now().strftime('%Y%m%d%H%M%S')}-{request.service_name}",
            service=service_identifier,
            time_range=time_range,
            trigger_type=TriggerType(request.trigger_source),
        )

        return session

    async def _run_diagnosis_async(self, session: DiagnosisSession) -> None:
        """异步执行诊断（后台任务）"""
        try:
            logger.info("diagnosis_execution_start", session_id=session.diagnosis_id)

            # 调用诊断引擎
            await self.diagnosis_engine.run(session)

            logger.info(
                "diagnosis_execution_completed",
                session_id=session.diagnosis_id,
            )

        except Exception as e:
            logger.error(
                "diagnosis_execution_failed",
                session_id=session.diagnosis_id,
                error=str(e),
            )
