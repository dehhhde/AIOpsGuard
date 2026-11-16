"""置信度值对象"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Confidence:
    """置信度值对象
    
    范围：0.0 ~ 1.0
    - 0.0：完全不确定
    - 1.0：完全确定
    
    特性：
    - 不可变
    - 范围验证
    - 支持比较
    """
    
    value: float
    
    def __post_init__(self) -> None:
        """验证置信度范围"""
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"置信度必须在 0.0 ~ 1.0 之间，当前值：{self.value}")
    
    def is_high(self, threshold: float = 0.7) -> bool:
        """判断是否为高置信度"""
        return self.value >= threshold
    
    def is_low(self, threshold: float = 0.3) -> bool:
        """判断是否为低置信度"""
        return self.value < threshold
    
    def percentage(self) -> float:
        """转换为百分比"""
        return self.value * 100
    
    def __lt__(self, other: "Confidence") -> bool:
        return self.value < other.value
    
    def __le__(self, other: "Confidence") -> bool:
        return self.value <= other.value
    
    def __gt__(self, other: "Confidence") -> bool:
        return self.value > other.value
    
    def __ge__(self, other: "Confidence") -> bool:
        return self.value >= other.value
    
    def __str__(self) -> str:
        return f"{self.percentage():.1f}%"
