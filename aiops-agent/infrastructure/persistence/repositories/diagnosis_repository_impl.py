"""诊断会话仓储实现"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from domain.models.diagnosis_session import DiagnosisSession
from domain.repositories.diagnosis_session_repository import DiagnosisSessionRepository
from domain.enums import DiagnosisStatus
from ..models.diagnosis_orm import DiagnosisSessionORM
from ..mappers.diagnosis_mapper import DiagnosisMapper
from config.settings import settings

logger = structlog.get_logger(__name__)


class DiagnosisSessionRepositoryImpl(DiagnosisSessionRepository):
    """诊断会话仓储实现
    
    实现领域层的 DiagnosisSessionRepository 接口，
    提供数据持久化能力
    """
    
    def __init__(self, session: Optional[AsyncSession] = None):
        """初始化仓储
        
        Args:
            session: 数据库会话，如果为 None 则表示数据库未启用
        """
        self.session = session
        self.mapper = DiagnosisMapper()
    
    async def save(self, diagnosis_session: DiagnosisSession) -> None:
        """保存诊断会话
        
        Args:
            diagnosis_session: 诊断会话领域模型
        """
        if not settings.database_enabled or not self.session:
            logger.debug(
                "database_disabled_skip_save",
                session_id=diagnosis_session.session_id
            )
            return
        
        try:
            # 转换为 ORM 模型
            orm = self.mapper.to_orm(diagnosis_session)
            
            # 添加到会话
            self.session.add(orm)
            await self.session.flush()
            
            logger.info(
                "diagnosis_session_saved",
                session_id=diagnosis_session.session_id,
                status=diagnosis_session.status.value
            )
        except Exception as e:
            logger.error(
                "diagnosis_session_save_failed",
                session_id=diagnosis_session.session_id,
                error=str(e)
            )
            raise
    
    async def find_by_id(self, session_id: str) -> Optional[DiagnosisSession]:
        """根据 ID 查找诊断会话
        
        Args:
            session_id: 诊断会话 ID
        
        Returns:
            诊断会话领域模型，如果未找到则返回 None
        """
        if not settings.database_enabled or not self.session:
            logger.debug("database_disabled_skip_find", session_id=session_id)
            return None
        
        try:
            result = await self.session.execute(
                select(DiagnosisSessionORM).where(
                    DiagnosisSessionORM.session_id == session_id
                )
            )
            orm = result.scalar_one_or_none()
            
            if not orm:
                logger.debug("diagnosis_session_not_found", session_id=session_id)
                return None
            
            # 转换为领域模型
            domain_model = self.mapper.to_domain(orm)
            
            logger.debug("diagnosis_session_found", session_id=session_id)
            return domain_model
            
        except Exception as e:
            logger.error(
                "diagnosis_session_find_failed",
                session_id=session_id,
                error=str(e)
            )
            return None
    
    async def find_by_service(
        self,
        service_name: str,
        limit: int = 10
    ) -> list[DiagnosisSession]:
        """根据服务名查找诊断会话列表
        
        Args:
            service_name: 服务名称
            limit: 返回数量限制
        
        Returns:
            诊断会话列表（按创建时间倒序）
        """
        if not settings.database_enabled or not self.session:
            logger.debug("database_disabled_skip_find_by_service")
            return []
        
        try:
            result = await self.session.execute(
                select(DiagnosisSessionORM)
                .where(DiagnosisSessionORM.service_name == service_name)
                .order_by(DiagnosisSessionORM.created_at.desc())
                .limit(limit)
            )
            orms = result.scalars().all()
            
            # 转换为领域模型列表
            sessions = [self.mapper.to_domain(orm) for orm in orms]
            
            logger.debug(
                "diagnosis_sessions_found_by_service",
                service_name=service_name,
                count=len(sessions)
            )
            return sessions
            
        except Exception as e:
            logger.error(
                "diagnosis_session_find_by_service_failed",
                service_name=service_name,
                error=str(e)
            )
            return []
    
    async def find_by_status(
        self,
        status: DiagnosisStatus,
        limit: int = 10
    ) -> list[DiagnosisSession]:
        """根据状态查找诊断会话列表
        
        Args:
            status: 诊断状态
            limit: 返回数量限制
        
        Returns:
            诊断会话列表（按创建时间倒序）
        """
        if not settings.database_enabled or not self.session:
            logger.debug("database_disabled_skip_find_by_status")
            return []
        
        try:
            result = await self.session.execute(
                select(DiagnosisSessionORM)
                .where(DiagnosisSessionORM.status == status.value)
                .order_by(DiagnosisSessionORM.created_at.desc())
                .limit(limit)
            )
            orms = result.scalars().all()
            
            # 转换为领域模型列表
            sessions = [self.mapper.to_domain(orm) for orm in orms]
            
            logger.debug(
                "diagnosis_sessions_found_by_status",
                status=status.value,
                count=len(sessions)
            )
            return sessions
            
        except Exception as e:
            logger.error(
                "diagnosis_session_find_by_status_failed",
                status=status.value,
                error=str(e)
            )
            return []
    
    async def delete(self, session_id: str) -> bool:
        """删除诊断会话
        
        Args:
            session_id: 诊断会话 ID
        
        Returns:
            是否删除成功
        """
        if not settings.database_enabled or not self.session:
            logger.debug("database_disabled_skip_delete")
            return False
        
        try:
            result = await self.session.execute(
                select(DiagnosisSessionORM).where(
                    DiagnosisSessionORM.session_id == session_id
                )
            )
            orm = result.scalar_one_or_none()
            
            if not orm:
                logger.debug("diagnosis_session_not_found_skip_delete", session_id=session_id)
                return False
            
            await self.session.delete(orm)
            await self.session.flush()
            
            logger.info("diagnosis_session_deleted", session_id=session_id)
            return True
            
        except Exception as e:
            logger.error(
                "diagnosis_session_delete_failed",
                session_id=session_id,
                error=str(e)
            )
            return False
    
    async def update(self, diagnosis_session: DiagnosisSession) -> None:
        """更新诊断会话
        
        Args:
            diagnosis_session: 诊断会话领域模型
        """
        # 使用 merge 进行更新
        await self.save(diagnosis_session)
