"""仓储接口

仓储接口定义在领域层，实现在基础设施层。
这样可以保证领域层不依赖基础设施（依赖倒置原则）。
"""

from .diagnosis_session_repository import DiagnosisSessionRepository

__all__ = ["DiagnosisSessionRepository"]
