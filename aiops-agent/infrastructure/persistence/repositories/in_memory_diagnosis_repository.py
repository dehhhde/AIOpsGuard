"""诊断会话内存仓储实现

说明：PostgreSQL 尚处于“预留”状态（见外部依赖配置清单），未配置前使用内存仓储
兜底，服务重启后会话数据不保留；接入 PostgreSQL 后由 ORM 仓储替换本实现。
"""
from __future__ import annotations

from typing import Optional

from domain.models.diagnosis import DiagnosisSession
from domain.repositories.diagnosis_repository import DiagnosisRepository


class InMemoryDiagnosisRepository(DiagnosisRepository):
    """基于字典的内存仓储，单进程内有效"""

    def __init__(self) -> None:
        self._sessions: dict[str, DiagnosisSession] = {}

    async def save(self, session: DiagnosisSession) -> None:
        """保存或更新诊断会话"""
        self._sessions[session.diagnosis_id] = session

    async def get(self, diagnosis_id: str) -> Optional[DiagnosisSession]:
        """按诊断 ID 查询会话"""
        return self._sessions.get(diagnosis_id)

    async def list_all(self) -> list[DiagnosisSession]:
        """返回全部会话"""
        return list(self._sessions.values())
