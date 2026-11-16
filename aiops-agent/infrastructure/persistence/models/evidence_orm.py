"""证据 ORM 模型"""
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from ..database import Base


class EvidenceORM(Base):
    """证据 ORM 模型
    
    对应领域模型：domain.models.evidence.Evidence
    """
    __tablename__ = "evidences"
    
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
    
    # 证据信息
    evidence_type = Column(String(50), nullable=False, comment="证据类型（METRIC/LOG/TRACE）")
    source = Column(String(500), nullable=False, comment="证据来源")
    summary = Column(Text, nullable=False, comment="证据摘要")
    detail = Column(Text, nullable=True, comment="证据详情")
    
    # 置信度（存储为整数 0-100，对应领域模型的 0.0-1.0）
    confidence = Column(Integer, nullable=False, comment="置信度 0-100")
    
    # 时间戳
    timestamp = Column(DateTime, nullable=False, comment="证据时间戳")
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    
    # 元数据
    metadata_ = Column("metadata", JSONB, nullable=True, comment="元数据 JSON")
    
    def __repr__(self) -> str:
        return f"<EvidenceORM(id={self.id}, type={self.evidence_type}, source={self.source[:50]})>"
