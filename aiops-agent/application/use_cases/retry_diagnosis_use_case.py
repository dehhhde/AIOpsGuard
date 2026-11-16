"""重新诊断用例"""

import structlog

from application.dto.requests import TriggerDiagnosisRequest
from application.dto.responses import TriggerDiagnosisResponse
from application.services.diagnosis_engine_service import DiagnosisEngineService
from application.use_cases.trigger_diagnosis_use_case import TriggerDiagnosisUseCase
from domain.enums import DiagnosisStatus
from infrastructure.cache.redis_client import RedisClient
from infrastructure.persistence.database import get_db_session
from infrastructure.persistence.repositories.diagnosis_repository_impl import (
    DiagnosisSessionRepositoryImpl,
)

logger = structlog.get_logger(__name__)


class DiagnosisNotFoundError(Exception):
    """诊断未找到异常"""

    pass


class DiagnosisCannotBeRetriedError(Exception):
    """诊断无法重试异常"""

    pass


class RetryDiagnosisUseCase:
    """重新诊断用例

    职责：
    1. 查询原诊断会话
    2. 验证是否可重试（只有 failed 状态可重试）
    3. 使用原参数重新触发诊断
    """

    def __init__(
        self, redis_client: RedisClient, diagnosis_engine: DiagnosisEngineService
    ):
        self.redis_client = redis_client
        self.diagnosis_engine = diagnosis_engine
        self.trigger_use_case = TriggerDiagnosisUseCase(redis_client, diagnosis_engine)

    async def execute(self, session_id: str) -> TriggerDiagnosisResponse:
        """执行重试

        Args:
            session_id: 原诊断会话 ID

        Returns:
            触发诊断响应

        Raises:
            DiagnosisNotFoundError: 诊断未找到
            DiagnosisCannotBeRetriedError: 诊断无法重试
        """
        logger.info("retry_diagnosis_start", session_id=session_id)

        async with get_db_session() as db_session:
            if not db_session:
                logger.warning("database_disabled_cannot_retry")
                raise DiagnosisNotFoundError(
                    f"Cannot retry diagnosis {session_id}: database disabled"
                )

            repo = DiagnosisSessionRepositoryImpl(db_session)
            session = await repo.find_by_id(session_id)

            if not session:
                logger.warning("session_not_found", session_id=session_id)
                raise DiagnosisNotFoundError(
                    f"Diagnosis session {session_id} not found"
                )

            # 验证是否可重试
            if session.status != DiagnosisStatus.FAILED:
                logger.warning(
                    "diagnosis_cannot_be_retried",
                    session_id=session_id,
                    status=session.status.value,
                )
                raise DiagnosisCannotBeRetriedError(
                    f"Diagnosis {session_id} cannot be retried: "
                    f"current status is {session.status.value}"
                )

            # 构建触发请求（使用原参数）
            time_range_minutes = int(
                (session.time_range.end_time - session.time_range.start_time).total_seconds()
                / 60
            )

            request = TriggerDiagnosisRequest(
                service_name=session.service.service_name,
                service_instance=session.service.service_instance,
                environment=session.service.environment,
                time_range_minutes=time_range_minutes,
                trigger_source=session.trigger_type.value,
            )

            # 重新触发诊断
            response = await self.trigger_use_case.execute(request)

            logger.info(
                "diagnosis_retried",
                original_session_id=session_id,
                new_session_id=response.session_id,
            )

            return response
