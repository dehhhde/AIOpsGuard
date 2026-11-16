"""报告实体"""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class Report:
    """诊断报告实体
    
    特性：
    - 有唯一标识（id）
    - Markdown 格式内容
    - 生成时间戳
    - 可选元数据
    """
    
    content: str  # Markdown 格式的报告内容
    generated_at: datetime = field(default_factory=datetime.now)  # 生成时间
    metadata: dict[str, str] = field(default_factory=dict)  # 元数据
    id: str = field(default_factory=lambda: str(uuid4()))  # 唯一标识
    
    def __post_init__(self) -> None:
        """验证报告"""
        if not self.content or not self.content.strip():
            raise ValueError("报告内容不能为空")
    
    def word_count(self) -> int:
        """获取字数"""
        return len(self.content)
    
    def section_count(self) -> int:
        """获取章节数（通过 Markdown 标题计数）"""
        return self.content.count("\n## ") + self.content.count("\n# ")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "generatedAt": self.generated_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Report":
        """从字典创建"""
        return cls(
            id=data.get("id", str(uuid4())),
            content=data["content"],
            generated_at=datetime.fromisoformat(data["generatedAt"]),
            metadata=data.get("metadata", {}),
        )
    
    def __str__(self) -> str:
        return f"Report(生成于 {self.generated_at.isoformat()}, 字数: {self.word_count()})"
