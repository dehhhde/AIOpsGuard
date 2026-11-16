"""诊断会话 ORM 模型"""
from sqlalchemy import Column, String, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from ..database import Base


class DiagnosisSessionORM(Base):
    """诊断会话 ORM 模型
    
    对应领域模型：domain.models.diagnosis_session.DiagnosisSession
    """
    __tablename__ = "diagnosis_sessions"
    
    # 主键
    id = Column(String(36), primary_key=True, comment="主键 ID")
    session_id = Column(String(100), unique=True, nullable=False, index=True, comment="诊断会话 ID")
    
    # 服务信息
    service_name = Column(String(200), nullable=False, index=True, comment="服务名称")
    service_instance = Column(String(200), nullable=True, comment="服务实例")
    environment = Column(String(50), nullable=False, comment="环境（prod/staging/dev）")
    
    # 时间范围
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, nullable=False, comment="结束时间")
    
    # 状态
    status = Column(String(50), nullable=False, index=True, comment="诊断状态")
    current_stage = Column(String(50), nullable=True, comment="当前阶段")
    progress = Column(Integer, default=0, comment="进度百分比 0-100")
    
    # 触发信息
    trigger_type = Column(String(50), nullable=False, comment="触发类型")
    trigger_source = Column(String(200), nullable=True, comment="触发来源")
    
    # 元数据
    metadata_ = Column("metadata", JSONB, nullable=True, comment="元数据 JSON")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    failed_at = Column(DateTime, nullable=True, comment="失败时间")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    def __repr__(self) -> str:
        return f"<DiagnosisSessionORM(session_id={self.session_id}, status={self.status})>"
