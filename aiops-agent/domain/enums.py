"""领域枚举"""
from enum import Enum


class DiagnosisStatus(str, Enum):
    """诊断状态"""
    PENDING = "pending"  # 等待开始
    ANALYZING = "analyzing"  # 分析中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class DiagnosisStage(str, Enum):
    """诊断阶段"""
    COLLECT = "collect"  # 数据采集
    METRIC_ANALYSIS = "metric_analysis"  # 指标分析
    LOG_ANALYSIS = "log_analysis"  # 日志分析
    TRACE_ANALYSIS = "trace_analysis"  # 链路分析
    RCA = "rca"  # 根因分析
    REPORT_GENERATION = "report_generation"  # 报告生成


class EvidenceType(str, Enum):
    """证据类型"""
    METRIC = "METRIC"  # 指标证据
    LOG = "LOG"  # 日志证据
    TRACE = "TRACE"  # 链路证据


class TriggerType(str, Enum):
    """触发方式"""
    MANUAL = "manual"  # 手动触发
    ALERT = "alert"  # 告警触发
    SCHEDULED = "scheduled"  # 定时触发


# 阶段顺序（用于验证阶段推进）
STAGE_ORDER = [
    DiagnosisStage.COLLECT,
    DiagnosisStage.METRIC_ANALYSIS,
    DiagnosisStage.LOG_ANALYSIS,
    DiagnosisStage.TRACE_ANALYSIS,
    DiagnosisStage.RCA,
    DiagnosisStage.REPORT_GENERATION,
]


def get_stage_index(stage: DiagnosisStage) -> int:
    """获取阶段索引"""
    return STAGE_ORDER.index(stage)


def is_valid_stage_transition(from_stage: DiagnosisStage, to_stage: DiagnosisStage) -> bool:
    """判断阶段转换是否有效（只能向前推进）"""
    return get_stage_index(to_stage) == get_stage_index(from_stage) + 1
