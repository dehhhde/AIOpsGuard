"""查询诊断用例"""

from typing import List, Optional

import structlog

from application.dto.requests import QueryDiagnosisRequest
from application.dto.responses import DiagnosisSessionResponse
from application.mappers.diagnosis_dto_mapper import DiagnosisDTOMapper
from domain.enums import DiagnosisStatus
from domain.models.diagnosis_session import DiagnosisSession
from infrastructure.cache.redis_client import RedisClient
from infrastructure.cache.session_cache import SessionCache
from infrastructure.persistence.database import get_db_session
from infrastructure.persistence.repositories.diagnosis_repository_impl import (
    DiagnosisSessionRepositoryImpl,
)

logger = structlog.get_logger(__name__)


class QueryDiagnosisUseCase:
    """查询诊断用例

    职责：
    1. 先查缓存
    2. 缓存未命中查数据库
    3. 转换为响应 DTO
    """

    def __init__(self, redis_client: RedisClient):
        self.cache = SessionCache(redis_client)
        self.mapper = DiagnosisDTOMapper()

    async def execute(
        self, request: QueryDiagnosisRequest
    ) -> List[DiagnosisSessionResponse]:
        """执行查询

        Args:
            request: 查询请求

        Returns:
            诊断会话响应列表
        """
        # 如果指定了 session_id，查询单个
        if request.session_id:
            session = await self._find_by_id(request.session_id)
            return [self.mapper.to_session_response(session)] if session else []

        # 如果指定了 service_name，查询服务的诊断历史
        if request.service_name:
            sessions = await self._find_by_service(request.service_name, request.limit)
            return [self.mapper.to_session_response(s) for s in sessions]

        # 如果指定了 status，查询指定状态的诊断
        if request.status:
            status = DiagnosisStatus(request.status)
            sessions = await self._find_by_status(status, request.limit)
            return [self.mapper.to_session_response(s) for s in sessions]

        # 默认返回空列表
        return []

    async def _find_by_id(self, session_id: str) -> Optional[DiagnosisSession]:
        """根据 ID 查找（先缓存后数据库）"""
        # 1. 先查缓存
        cached_data = await self.cache.get(session_id)
        if cached_data:
            logger.debug("session_found_in_cache", session_id=session_id)
            # TODO: 从缓存数据重建领域模型
            # 目前直接查数据库

        # 2. 查数据库
        async with get_db_session() as db_session:
            if not db_session:
                logger.warning("database_disabled_skip_query")
                return None

            repo = DiagnosisSessionRepositoryImpl(db_session)
            return await repo.find_by_id(session_id)

    async def _find_by_service(
        self, service_name: str, limit: int
    ) -> List[DiagnosisSession]:
        """根据服务名查找"""
        async with get_db_session() as db_session:
            if not db_session:
                return []

            repo = DiagnosisSessionRepositoryImpl(db_session)
            return await repo.find_by_service(service_name, limit)

    async def _find_by_status(
        self, status: DiagnosisStatus, limit: int
    ) -> List[DiagnosisSession]:
        """根据状态查找"""
        async with get_db_session() as db_session:
            if not db_session:
                return []

            repo = DiagnosisSessionRepositoryImpl(db_session)
            return await repo.find_by_status(status, limit)
