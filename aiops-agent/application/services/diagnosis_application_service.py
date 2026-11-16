"""诊断应用服务"""

from typing import List, Optional

import structlog

from application.dto.requests import QueryDiagnosisRequest, TriggerDiagnosisRequest
from application.dto.responses import (
    DiagnosisReportResponse,
    DiagnosisSessionResponse,
    TriggerDiagnosisResponse,
)
from application.services.diagnosis_engine_service import DiagnosisEngineService
from application.use_cases.cancel_diagnosis_use_case import CancelDiagnosisUseCase
from application.use_cases.get_diagnosis_report_use_case import (
    GetDiagnosisReportUseCase,
)
from application.use_cases.query_diagnosis_use_case import QueryDiagnosisUseCase
from application.use_cases.retry_diagnosis_use_case import RetryDiagnosisUseCase
from application.use_cases.trigger_diagnosis_use_case import (
    DiagnosisAlreadyInProgressError,
    TriggerDiagnosisUseCase,
)
from infrastructure.cache.redis_client import RedisClient

logger = structlog.get_logger(__name__)


class DiagnosisApplicationService:
    """诊断应用服务

    职责：
    1. 协调多个用例
    2. 统一异常处理
    3. 事务边界管理
    """

    def __init__(
        self, redis_client: RedisClient, diagnosis_engine: DiagnosisEngineService
    ):
        self.trigger_use_case = TriggerDiagnosisUseCase(redis_client, diagnosis_engine)
        self.query_use_case = QueryDiagnosisUseCase(redis_client)
        self.get_report_use_case = GetDiagnosisReportUseCase(redis_client)
        self.cancel_use_case = CancelDiagnosisUseCase(redis_client)
        self.retry_use_case = RetryDiagnosisUseCase(redis_client, diagnosis_engine)

    async def trigger_diagnosis(
        self, request: TriggerDiagnosisRequest
    ) -> TriggerDiagnosisResponse:
        """触发诊断

        Args:
            request: 触发诊断请求

        Returns:
            触发诊断响应

        Raises:
            DiagnosisAlreadyInProgressError: 服务正在诊断中
        """
        return await self.trigger_use_case.execute(request)

    async def query_diagnosis(
        self, request: QueryDiagnosisRequest
    ) -> List[DiagnosisSessionResponse]:
        """查询诊断

        Args:
            request: 查询请求

        Returns:
            诊断会话响应列表
        """
        return await self.query_use_case.execute(request)

    async def get_diagnosis_by_id(
        self, session_id: str
    ) -> Optional[DiagnosisSessionResponse]:
        """根据 ID 获取诊断

        Args:
            session_id: 诊断会话 ID

        Returns:
            诊断会话响应，如果不存在返回 None
        """
        request = QueryDiagnosisRequest(session_id=session_id)
        results = await self.query_use_case.execute(request)
        return results[0] if results else None

    async def get_diagnosis_report(self, session_id: str) -> DiagnosisReportResponse:
        """获取诊断报告

        Args:
            session_id: 诊断会话 ID

        Returns:
            诊断报告响应

        Raises:
            DiagnosisReportNotFoundError: 诊断报告未找到
        """
        return await self.get_report_use_case.execute(session_id)

    async def cancel_diagnosis(self, session_id: str) -> None:
        """取消诊断

        Args:
            session_id: 诊断会话 ID

        Raises:
            DiagnosisNotFoundError: 诊断未找到
            DiagnosisCannotBeCancelledError: 诊断无法取消
        """
        await self.cancel_use_case.execute(session_id)

    async def retry_diagnosis(self, session_id: str) -> TriggerDiagnosisResponse:
        """重新诊断

        Args:
            session_id: 原诊断会话 ID

        Returns:
            触发诊断响应

        Raises:
            DiagnosisNotFoundError: 诊断未找到
            DiagnosisCannotBeRetriedError: 诊断无法重试
        """
        return await self.retry_use_case.execute(session_id)
