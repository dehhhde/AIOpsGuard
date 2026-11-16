"""领域事件

领域事件用于解耦不同模块，实现事件驱动架构。
"""

from .diagnosis_events import (
    DiagnosisCompleted,
    DiagnosisFailed,
    DiagnosisTriggered,
    StageCompleted,
)

__all__ = [
    "DiagnosisTriggered",
    "StageCompleted",
    "DiagnosisCompleted",
    "DiagnosisFailed",
]
