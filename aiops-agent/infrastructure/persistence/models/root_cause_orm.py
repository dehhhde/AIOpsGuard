"""根因 ORM 模型"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime

from ..database import Base


class RootCauseORM(Base):
    """根因 ORM 模型
    
    对应领域模型：domain.models.root_cause.RootCause
    """
    __tablename__ = "root_causes"
    
    # 主键
    id = Column(String(36), primary_key=True, comment="主键 ID")
    
    # 外键：关联诊断会话
    diagnosis_session_id = Column(
        String(36),
        ForeignKey("diagnosis_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="诊断会话 ID"
    )
    
    # 根因信息
    problem_type = Column(String(100), nullable=False, comment="问题类型")
    summary = Column(Text, nullable=False, comment="根因摘要")
    reasoning = Column(Text, nullable=False, comment="推理过程")
    
    # 置信度（存储为整数 0-100）
    confidence = Column(Integer, nullable=False, comment="置信度 0-100")
    
    # 修复建议（PostgreSQL 数组）
    recommendations = Column(ARRAY(Text), nullable=False, comment="修复建议列表")
    
    # 元数据
    metadata_ = Column("metadata", JSONB, nullable=True, comment="元数据 JSON")
    
    # 时间戳
    created_at = Column(datetime, default=datetime.now, nullable=False, comment="创建时间")
    
    def __repr__(self) -> str:
        return f"<RootCauseORM(id={self.id}, type={self.problem_type}, confidence={self.confidence})>"
