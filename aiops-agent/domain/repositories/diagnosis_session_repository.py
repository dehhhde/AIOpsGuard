"""诊断会话仓储接口"""
from abc import ABC, abstractmethod
from typing import Optional

from ..models.diagnosis_session import DiagnosisSession


class DiagnosisSessionRepository(ABC):
    """诊断会话仓储接口
    
    职责：
    - 持久化诊断会话
    - 按条件查询诊断会话
    
    实现要求：
    - 所有方法都是异步的（async）
    - 实现层（基础设施层）负责 ORM 映射与事务管理
    """
    
    @abstractmethod
    async def save(self, session: DiagnosisSession) -> None:
        """保存诊断会话（新增）
        
        Args:
            session: 诊断会话聚合根
        
        Raises:
            ValueError: 如果会话 ID 已存在
        """
        pass
    
    @abstractmethod
    async def update(self, session: DiagnosisSession) -> None:
        """更新诊断会话
        
        Args:
            session: 诊断会话聚合根
        
        Raises:
            ValueError: 如果会话不存在
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, diagnosis_id: str) -> Optional[DiagnosisSession]:
        """根据诊断 ID 查询会话
        
        Args:
            diagnosis_id: 诊断 ID
        
        Returns:
            诊断会话，如果不存在则返回 None
        """
        pass
    
    @abstractmethod
    async def list(
        self,
        service_name: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DiagnosisSession], int]:
        """分页查询诊断会话
        
        Args:
            service_name: 服务名（可选）
            status: 状态（可选）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            page: 页码（从 1 开始）
            page_size: 每页数量
        
        Returns:
            (会话列表, 总数)
        """
        pass
    
    @abstractmethod
    async def delete(self, diagnosis_id: str) -> bool:
        """删除诊断会话
        
        Args:
            diagnosis_id: 诊断 ID
        
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def count_by_status(self, status: str) -> int:
        """按状态统计诊断会话数量
        
        Args:
            status: 状态
        
        Returns:
            会话数量
        """
        pass
