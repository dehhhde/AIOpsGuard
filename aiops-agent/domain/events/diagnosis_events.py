"""诊断相关领域事件"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..enums import DiagnosisStage, DiagnosisStatus
from ..value_objects.time_range import TimeRange


@dataclass(frozen=True)
class DiagnosisTriggered:
    """诊断触发事件
    
    当诊断会话被创建并启动时发布此事件
    """
    
    diagnosis_id: str  # 诊断 ID
    service_name: str  # 服务名
    service_instance: Optional[str]  # 服务实例
    time_range: TimeRange  # 诊断时间窗
    trigger_type: str  # 触发方式
    triggered_at: datetime = field(default_factory=datetime.now)  # 触发时间
    
    def __str__(self) -> str:
        return f"DiagnosisTriggered(id={self.diagnosis_id}, service={self.service_name})"


@dataclass(frozen=True)
class StageCompleted:
    """阶段完成事件
    
    当诊断推进到下一个阶段时发布此事件
    """
    
    diagnosis_id: str  # 诊断 ID
    stage: DiagnosisStage  # 完成的阶段
    progress: int  # 进度百分比
    completed_at: datetime = field(default_factory=datetime.now)  # 完成时间
    
    # 可选：阶段产出数据
    evidence_count: int = 0  # 该阶段产生的证据数量
    
    def __str__(self) -> str:
        return f"StageCompleted(id={self.diagnosis_id}, stage={self.stage.value}, progress={self.progress}%)"


@dataclass(frozen=True)
class DiagnosisCompleted:
    """诊断完成事件
    
    当诊断成功完成时发布此事件
    """
    
    diagnosis_id: str  # 诊断 ID
    service_name: str  # 服务名
    status: DiagnosisStatus  # 最终状态（completed）
    root_cause_count: int  # 根因数量
    evidence_count: int  # 证据数量
    duration_seconds: float  # 诊断耗时（秒）
    completed_at: datetime = field(default_factory=datetime.now)  # 完成时间
    
    def __str__(self) -> str:
        return f"DiagnosisCompleted(id={self.diagnosis_id}, duration={self.duration_seconds:.1f}s, root_causes={self.root_cause_count})"


@dataclass(frozen=True)
class DiagnosisFailed:
    """诊断失败事件
    
    当诊断执行失败时发布此事件
    """
    
    diagnosis_id: str  # 诊断 ID
    service_name: str  # 服务名
    status: DiagnosisStatus  # 最终状态（failed）
    stage: Optional[DiagnosisStage]  # 失败的阶段
    error_message: str  # 错误信息
    failed_at: datetime = field(default_factory=datetime.now)  # 失败时间
    
    def __str__(self) -> str:
        return f"DiagnosisFailed(id={self.diagnosis_id}, stage={self.stage.value if self.stage else 'unknown'}, error={self.error_message})"
