"""取消诊断用例"""

import structlog

from domain.enums import DiagnosisStatus
from infrastructure.cache.redis_client import RedisClient
from infrastructure.cache.session_cache import SessionCache
from infrastructure.persistence.database import get_db_session
from infrastructure.persistence.repositories.diagnosis_repository_impl import (
    DiagnosisSessionRepositoryImpl,
)

logger = structlog.get_logger(__name__)


class DiagnosisNotFoundError(Exception):
    """诊断未找到异常"""

    pass


class DiagnosisCannotBeCancelledError(Exception):
    """诊断无法取消异常"""

    pass


class CancelDiagnosisUseCase:
    """取消诊断用例

    职责：
    1. 查询诊断会话
    2. 验证是否可取消（只有 pending 和 analyzing 状态可取消）
    3. 更新状态为 failed
    4. 释放分布式锁
    """

    def __init__(self, redis_client: RedisClient):
        self.cache = SessionCache(redis_client)

    async def execute(self, session_id: str) -> None:
        """执行取消

        Args:
            session_id: 诊断会话 ID

        Raises:
            DiagnosisNotFoundError: 诊断未找到
            DiagnosisCannotBeCancelledError: 诊断无法取消
        """
        logger.info("cancel_diagnosis_start", session_id=session_id)

        async with get_db_session() as db_session:
            if not db_session:
                logger.warning("database_disabled_cannot_cancel")
                raise DiagnosisNotFoundError(
                    f"Cannot cancel diagnosis {session_id}: database disabled"
                )

            repo = DiagnosisSessionRepositoryImpl(db_session)
            session = await repo.find_by_id(session_id)

            if not session:
                logger.warning("session_not_found", session_id=session_id)
                raise DiagnosisNotFoundError(
                    f"Diagnosis session {session_id} not found"
                )

            # 验证是否可取消
            if session.status not in [DiagnosisStatus.PENDING, DiagnosisStatus.ANALYZING]:
                logger.warning(
                    "diagnosis_cannot_be_cancelled",
                    session_id=session_id,
                    status=session.status.value,
                )
                raise DiagnosisCannotBeCancelledError(
                    f"Diagnosis {session_id} cannot be cancelled: "
                    f"current status is {session.status.value}"
                )

            # 标记为失败
            session.fail("Cancelled by user")
            await repo.save(session)

            # 清除缓存
            await self.cache.delete(session_id)

            logger.info("diagnosis_cancelled", session_id=session_id)
