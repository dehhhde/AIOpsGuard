"""诊断会话映射器"""
from domain.models.diagnosis_session import DiagnosisSession
from domain.value_objects.time_range import TimeRange
from domain.value_objects.service_identifier import ServiceIdentifier
from domain.enums import DiagnosisStatus, DiagnosisStage, TriggerType
from ..models.diagnosis_orm import DiagnosisSessionORM


class DiagnosisMapper:
    """领域模型 ↔ ORM 映射器
    
    负责在 DiagnosisSession（领域模型）和 DiagnosisSessionORM（数据库模型）之间转换
    """
    
    @staticmethod
    def to_orm(session: DiagnosisSession) -> DiagnosisSessionORM:
        """领域模型转 ORM
        
        将领域层的 DiagnosisSession 转换为持久化层的 ORM 模型
        
        Args:
            session: 诊断会话领域模型
        
        Returns:
            DiagnosisSessionORM: ORM 模型
        """
        return DiagnosisSessionORM(
            id=session.id,
            session_id=session.session_id,
            service_name=session.service_identifier.service_name,
            service_instance=session.service_identifier.service_instance,
            environment=session.service_identifier.environment,
            start_time=session.time_range.start_time,
            end_time=session.time_range.end_time,
            status=session.status.value,
            current_stage=session.current_stage.value if session.current_stage else None,
            progress=session.progress,
            trigger_type=session.trigger_type.value,
            trigger_source=session.trigger_source,
            metadata_=session.metadata,
            created_at=session.created_at,
            updated_at=session.updated_at,
            error_message=session.error_message
        )
    
    @staticmethod
    def to_domain(orm: DiagnosisSessionORM) -> DiagnosisSession:
        """ORM 转领域模型
        
        将持久化层的 ORM 模型转换为领域层的 DiagnosisSession
        
        Args:
            orm: ORM 模型
        
        Returns:
            DiagnosisSession: 诊断会话领域模型
        """
        # 重建值对象
        service_identifier = ServiceIdentifier(
            service_name=orm.service_name,
            service_instance=orm.service_instance,
            environment=orm.environment
        )
        
        time_range = TimeRange(
            start_time=orm.start_time,
            end_time=orm.end_time
        )
        
        # 重建聚合根
        session = DiagnosisSession(
            id=orm.id,
            session_id=orm.session_id,
            service_identifier=service_identifier,
            time_range=time_range,
            status=DiagnosisStatus(orm.status),
            current_stage=DiagnosisStage(orm.current_stage) if orm.current_stage else None,
            progress=orm.progress,
            trigger_type=TriggerType(orm.trigger_type),
            trigger_source=orm.trigger_source,
            metadata=orm.metadata_ or {},
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            error_message=orm.error_message
        )
        
        return session
