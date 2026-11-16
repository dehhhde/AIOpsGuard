"""诊断会话仓储接口"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from domain.models.diagnosis import DiagnosisSession


class DiagnosisRepository(ABC):
    """诊断会话仓储抽象，由 infrastructure/persistence 提供实现"""

    @abstractmethod
    async def save(self, session: DiagnosisSession) -> None:
        """保存或更新诊断会话"""

    @abstractmethod
    async def get(self, diagnosis_id: str) -> Optional[DiagnosisSession]:
        """按诊断 ID 查询会话，不存在时返回 None"""

    @abstractmethod
    async def list_all(self) -> list[DiagnosisSession]:
        """返回全部会话（由调用方排序与过滤）"""
