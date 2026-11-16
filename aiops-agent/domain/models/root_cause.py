"""根因实体"""
from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4

from ..value_objects.confidence import Confidence


@dataclass
class RootCause:
    """根因实体
    
    代表一个可能的根本原因
    
    特性：
    - 有唯一标识（id）
    - 包含排序序号（rank）
    - 包含置信度（confidence）
    - 关联证据列表（evidence_ids）
    """
    
    cause: str  # 根因描述
    confidence: Confidence  # 置信度
    evidence_ids: list[str] = field(default_factory=list)  # 关联的证据 ID 列表
    rank: int = 0  # 排序序号（按置信度排序后设置）
    id: str = field(default_factory=lambda: str(uuid4()))  # 唯一标识
    
    def __post_init__(self) -> None:
        """验证根因"""
        if not self.cause or not self.cause.strip():
            raise ValueError("根因描述不能为空")
        
        if self.rank < 0:
            raise ValueError(f"排序序号不能为负数：{self.rank}")
    
    def is_high_confidence(self, threshold: float = 0.7) -> bool:
        """判断是否为高置信度根因"""
        return self.confidence.is_high(threshold)
    
    def evidence_count(self) -> int:
        """获取证据数量"""
        return len(self.evidence_ids)
    
    def add_evidence(self, evidence_id: str) -> None:
        """添加证据"""
        if evidence_id not in self.evidence_ids:
            self.evidence_ids.append(evidence_id)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "rank": self.rank,
            "cause": self.cause,
            "confidence": self.confidence.value,
            "evidenceIds": self.evidence_ids,
        }
    
    def __lt__(self, other: "RootCause") -> bool:
        """支持排序（按置信度从高到低）"""
        return self.confidence > other.confidence
    
    def __str__(self) -> str:
        return f"#{self.rank} {self.cause} (置信度: {self.confidence})"
