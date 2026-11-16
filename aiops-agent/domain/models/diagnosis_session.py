"""诊断会话聚合根"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4

from ..enums import DiagnosisStage, DiagnosisStatus, TriggerType, is_valid_stage_transition
from ..value_objects.service_identifier import ServiceIdentifier
from ..value_objects.time_range import TimeRange
from .evidence import Evidence
from .report import Report
from .root_cause import RootCause


@dataclass
class DiagnosisSession:
    """诊断会话聚合根
    
    代表一次完整的诊断会话，是领域模型的核心。
    
    职责：
    - 管理诊断生命周期（启动、推进阶段、完成、失败）
    - 维护不变量约束
    - 聚合证据、根因、报告
    
    不变量：
    1. 服务标识和时间窗启动后不可变
    2. 阶段只能按固定顺序推进
    3. 终态（completed/failed）后不可再修改
    4. 根因按置信度自动排序
    """
    
    diagnosis_id: str  # 诊断 ID（唯一标识）
    service: ServiceIdentifier  # 服务标识
    time_range: TimeRange  # 诊断时间窗
    trigger_type: TriggerType = TriggerType.MANUAL  # 触发方式
    
    # 状态字段
    status: DiagnosisStatus = DiagnosisStatus.PENDING
    stage: Optional[DiagnosisStage] = None
    progress: int = 0  # 进度百分比（0-100）
    
    # 时间戳
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    
    # 聚合数据
    evidence: list[Evidence] = field(default_factory=list)
    root_causes: list[RootCause] = field(default_factory=list)
    report: Optional[Report] = None
    
    # 错误信息（失败时记录）
    error_message: Optional[str] = None
    
    def __post_init__(self) -> None:
        """验证诊断会话"""
        if not self.diagnosis_id or not self.diagnosis_id.strip():
            raise ValueError("诊断 ID 不能为空")
    
    # ==================== 生命周期管理 ====================
    
    def start(self) -> None:
        """启动诊断"""
        if self.status != DiagnosisStatus.PENDING:
            raise ValueError(f"诊断已启动，当前状态：{self.status}")
        
        self.status = DiagnosisStatus.ANALYZING
        self.stage = DiagnosisStage.COLLECT
        self.progress = 0
        self.started_at = datetime.now()
    
    def advance_stage(self, next_stage: DiagnosisStage) -> None:
        """推进到下一个阶段
        
        Args:
            next_stage: 下一个阶段
        
        Raises:
            ValueError: 如果状态不是 analyzing 或阶段转换无效
        """
        if self.status != DiagnosisStatus.ANALYZING:
            raise ValueError(f"诊断未在分析中，当前状态：{self.status}")
        
        if self.stage is None:
            raise ValueError("当前阶段为空，请先调用 start() 启动诊断")
        
        if not is_valid_stage_transition(self.stage, next_stage):
            raise ValueError(f"无效的阶段转换：{self.stage} -> {next_stage}")
        
        self.stage = next_stage
        self._update_progress()
    
    def complete(self, report: Report) -> None:
        """完成诊断
        
        Args:
            report: 诊断报告
        
        Raises:
            ValueError: 如果状态不是 analyzing
        """
        if self.status != DiagnosisStatus.ANALYZING:
            raise ValueError(f"诊断未在分析中，当前状态：{self.status}")
        
        self.status = DiagnosisStatus.COMPLETED
        self.stage = DiagnosisStage.REPORT_GENERATION
        self.progress = 100
        self.finished_at = datetime.now()
        self.report = report
    
    def fail(self, error_message: str) -> None:
        """标记诊断失败
        
        Args:
            error_message: 错误信息
        """
        if self.is_terminal():
            raise ValueError(f"诊断已处于终态，不能再标记失败：{self.status}")
        
        self.status = DiagnosisStatus.FAILED
        self.finished_at = datetime.now()
        self.error_message = error_message
    
    # ==================== 证据管理 ====================
    
    def add_evidence(self, evidence: Evidence) -> None:
        """添加证据
        
        Args:
            evidence: 证据实体
        
        Raises:
            ValueError: 如果诊断已处于终态
        """
        if self.is_terminal():
            raise ValueError(f"诊断已处于终态，不能再添加证据：{self.status}")
        
        # 检查是否已存在相同 ID 的证据
        if any(e.id == evidence.id for e in self.evidence):
            raise ValueError(f"证据已存在：{evidence.id}")
        
        self.evidence.append(evidence)
    
    def get_evidence_by_type(self, evidence_type: str) -> list[Evidence]:
        """按类型获取证据"""
        return [e for e in self.evidence if e.type.value == evidence_type]
    
    # ==================== 根因管理 ====================
    
    def add_root_cause(self, root_cause: RootCause) -> None:
        """添加根因
        
        添加后会自动按置信度排序并更新 rank
        
        Args:
            root_cause: 根因实体
        
        Raises:
            ValueError: 如果诊断已处于终态
        """
        if self.is_terminal():
            raise ValueError(f"诊断已处于终态，不能再添加根因：{self.status}")
        
        self.root_causes.append(root_cause)
        self._sort_root_causes()
    
    def _sort_root_causes(self) -> None:
        """按置信度排序根因（从高到低），并更新 rank"""
        self.root_causes.sort()  # 使用 RootCause.__lt__ 排序（已实现为置信度降序）
        for idx, root_cause in enumerate(self.root_causes, start=1):
            root_cause.rank = idx
    
    # ==================== 状态查询 ====================
    
    def is_terminal(self) -> bool:
        """判断是否处于终态（completed 或 failed）"""
        return self.status in (DiagnosisStatus.COMPLETED, DiagnosisStatus.FAILED)
    
    def is_analyzing(self) -> bool:
        """判断是否正在分析"""
        return self.status == DiagnosisStatus.ANALYZING
    
    def is_completed(self) -> bool:
        """判断是否已完成"""
        return self.status == DiagnosisStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """判断是否失败"""
        return self.status == DiagnosisStatus.FAILED
    
    def duration_seconds(self) -> Optional[float]:
        """获取诊断耗时（秒）"""
        if self.started_at is None:
            return None
        
        end_time = self.finished_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
    
    # ==================== 私有方法 ====================
    
    def _update_progress(self) -> None:
        """根据当前阶段更新进度百分比"""
        if self.stage is None:
            self.progress = 0
            return
        
        stage_progress_map = {
            DiagnosisStage.COLLECT: 10,
            DiagnosisStage.METRIC_ANALYSIS: 25,
            DiagnosisStage.LOG_ANALYSIS: 45,
            DiagnosisStage.TRACE_ANALYSIS: 65,
            DiagnosisStage.RCA: 85,
            DiagnosisStage.REPORT_GENERATION: 100,
        }
        
        self.progress = stage_progress_map.get(self.stage, 0)
    
    # ==================== 序列化 ====================
    
    def to_dict(self) -> dict:
        """转换为字典（与前端 TypeScript 类型对齐）"""
        return {
            "diagnosisId": self.diagnosis_id,
            "serviceName": self.service.service_name,
            "serviceInstance": self.service.instance,
            "status": self.status.value,
            "stage": self.stage.value if self.stage else None,
            "progress": self.progress,
            "timeRange": self.time_range.to_dict(),
            "startedAt": self.started_at.isoformat() if self.started_at else None,
            "finishedAt": self.finished_at.isoformat() if self.finished_at else None,
            "triggerType": self.trigger_type.value,
            "rootCauses": [rc.to_dict() for rc in self.root_causes],
            "evidence": [e.to_dict() for e in self.evidence],
            "report": self.report.to_dict() if self.report else None,
            "errorMessage": self.error_message,
        }
    
    def __str__(self) -> str:
        duration = self.duration_seconds()
        duration_str = f"{duration:.1f}s" if duration else "未开始"
        return f"DiagnosisSession({self.diagnosis_id}, {self.service}, {self.status.value}, 耗时: {duration_str})"


def generate_diagnosis_id() -> str:
    """生成诊断 ID
    
    格式：diag-yyyymmdd-hhmmss-uuid前8位
    """
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    uuid_part = str(uuid4())[:8]
    return f"diag-{timestamp}-{uuid_part}"
