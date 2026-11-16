"""时间范围值对象"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TimeRange:
    """时间范围值对象
    
    特性：
    - 不可变
    - 自包含验证逻辑
    - 值相等性
    """
    
    start: datetime
    end: datetime
    
    def __post_init__(self) -> None:
        """验证时间范围"""
        if self.start >= self.end:
            raise ValueError(f"时间范围无效：开始时间 {self.start} 必须早于结束时间 {self.end}")
    
    def duration_seconds(self) -> float:
        """获取时间范围的时长（秒）"""
        return (self.end - self.start).total_seconds()
    
    def contains(self, timestamp: datetime) -> bool:
        """判断指定时间点是否在此范围内"""
        return self.start <= timestamp <= self.end
    
    def overlaps(self, other: "TimeRange") -> bool:
        """判断是否与另一个时间范围重叠"""
        return self.start < other.end and other.start < self.end
    
    def to_dict(self) -> dict[str, str]:
        """转换为字典（用于序列化）"""
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "TimeRange":
        """从字典创建（用于反序列化）"""
        return cls(
            start=datetime.fromisoformat(data["start"]),
            end=datetime.fromisoformat(data["end"])
        )
    
    def __str__(self) -> str:
        return f"{self.start.isoformat()} ~ {self.end.isoformat()}"
