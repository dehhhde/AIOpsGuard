"""获取诊断报告用例"""

from typing import Optional

import structlog

from application.dto.responses import DiagnosisReportResponse
from application.mappers.diagnosis_dto_mapper import DiagnosisDTOMapper
from domain.models.report import DiagnosisReport
from infrastructure.cache.redis_client import RedisClient
from infrastructure.cache.session_cache import SessionCache
from infrastructure.persistence.database import get_db_session
from infrastructure.persistence.repositories.diagnosis_repository_impl import (
    DiagnosisSessionRepositoryImpl,
)

logger = structlog.get_logger(__name__)


class DiagnosisReportNotFoundError(Exception):
    """诊断报告未找到异常"""

    pass


class GetDiagnosisReportUseCase:
    """获取诊断报告用例

    职责：
    1. 根据 session_id 查询诊断会话
    2. 获取关联的证据和根因
    3. 构建完整的诊断报告
    """

    def __init__(self, redis_client: RedisClient):
        self.cache = SessionCache(redis_client)
        self.mapper = DiagnosisDTOMapper()

    async def execute(self, session_id: str) -> DiagnosisReportResponse:
        """执行用例

        Args:
            session_id: 诊断会话 ID

        Returns:
            诊断报告响应

        Raises:
            DiagnosisReportNotFoundError: 诊断报告未找到
        """
        logger.info("get_diagnosis_report_start", session_id=session_id)

        # 1. 先查缓存
        cached_data = await self.cache.get(session_id)
        if cached_data:
            logger.debug("report_found_in_cache", session_id=session_id)
            # TODO: 从缓存数据重建报告
            # 目前直接查数据库

        # 2. 查数据库
        async with get_db_session() as db_session:
            if not db_session:
                logger.warning("database_disabled_cannot_get_report")
                raise DiagnosisReportNotFoundError(
                    f"Cannot retrieve report for session {session_id}: database disabled"
                )

            repo = DiagnosisSessionRepositoryImpl(db_session)
            session = await repo.find_by_id(session_id)

            if not session:
                logger.warning("session_not_found", session_id=session_id)
                raise DiagnosisReportNotFoundError(
                    f"Diagnosis session {session_id} not found"
                )

            if not session.report:
                logger.warning("report_not_generated", session_id=session_id)
                raise DiagnosisReportNotFoundError(
                    f"Diagnosis report for session {session_id} has not been generated yet"
                )

            # 3. 转换为响应 DTO
            report_response = self.mapper.to_report_response(session)

            logger.info("diagnosis_report_retrieved", session_id=session_id)
            return report_response
