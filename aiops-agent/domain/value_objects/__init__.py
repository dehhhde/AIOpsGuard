"""值对象

值对象特性：
1. 不可变（immutable）
2. 值相等性（基于属性而非引用）
3. 自包含验证逻辑
"""

from .confidence import Confidence
from .service_identifier import ServiceIdentifier
from .time_range import TimeRange

__all__ = ["TimeRange", "Confidence", "ServiceIdentifier"]
