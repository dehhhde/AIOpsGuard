"""DiagnosisSession 聚合根测试"""
import pytest
from datetime import datetime

from domain.models.diagnosis_session import DiagnosisSession, generate_diagnosis_id
from domain.models.evidence import Evidence
from domain.models.root_cause import RootCause
from domain.models.report import Report
from domain.enums import DiagnosisStage, DiagnosisStatus, EvidenceType, TriggerType
from domain.value_objects.time_range import TimeRange
from domain.value_objects.service_identifier import ServiceIdentifier
from domain.value_objects.confidence import Confidence


@pytest.fixture
def valid_session():
    """创建有效的诊断会话"""
    return DiagnosisSession(
        diagnosis_id=generate_diagnosis_id(),
        service=ServiceIdentifier(service_name="target-app", instance="192.168.1.10:8080"),
        time_range=TimeRange(
            start=datetime(2026, 11, 16, 10, 0, 0),
            end=datetime(2026, 11, 16, 10, 5, 0)
        ),
        trigger_type=TriggerType.MANUAL
    )


class TestDiagnosisSessionCreation:
    """测试诊断会话创建"""
    
    def test_create_valid_session(self, valid_session):
        """测试创建有效会话"""
        assert valid_session.diagnosis_id is not None
        assert valid_session.service.service_name == "target-app"
        assert valid_session.status == DiagnosisStatus.PENDING
        assert valid_session.stage is None
        assert valid_session.progress == 0
    
    def test_create_session_with_empty_id_raises_error(self):
        """测试创建空 ID 会话"""
        with pytest.raises(ValueError, match="诊断 ID 不能为空"):
            DiagnosisSession(
                diagnosis_id="",
                service=ServiceIdentifier(service_name="target-app"),
                time_range=TimeRange(
                    start=datetime(2026, 11, 16, 10, 0, 0),
                    end=datetime(2026, 11, 16, 10, 5, 0)
                )
            )
    
    def test_generate_diagnosis_id_format(self):
        """测试生成诊断 ID 格式"""
        diagnosis_id = generate_diagnosis_id()
        
        assert diagnosis_id.startswith("diag-")
        assert len(diagnosis_id.split("-")) == 4  # diag-yyyymmdd-hhmmss-uuid


class TestDiagnosisSessionLifecycle:
    """测试诊断会话生命周期"""
    
    def test_start_session(self, valid_session):
        """测试启动会话"""
        valid_session.start()
        
        assert valid_session.status == DiagnosisStatus.ANALYZING
        assert valid_session.stage == DiagnosisStage.COLLECT
        assert valid_session.progress == 10
        assert valid_session.started_at is not None
    
    def test_start_session_twice_raises_error(self, valid_session):
        """测试重复启动会话"""
        valid_session.start()
        
        with pytest.raises(ValueError, match="诊断已启动"):
            valid_session.start()
    
    def test_advance_stage_success(self, valid_session):
        """测试推进阶段"""
        valid_session.start()
        
        # COLLECT -> METRIC_ANALYSIS
        valid_session.advance_stage(DiagnosisStage.METRIC_ANALYSIS)
        assert valid_session.stage == DiagnosisStage.METRIC_ANALYSIS
        assert valid_session.progress == 25
        
        # METRIC_ANALYSIS -> LOG_ANALYSIS
        valid_session.advance_stage(DiagnosisStage.LOG_ANALYSIS)
        assert valid_session.stage == DiagnosisStage.LOG_ANALYSIS
        assert valid_session.progress == 45
    
    def test_advance_stage_skip_raises_error(self, valid_session):
        """测试跳过阶段（无效转换）"""
        valid_session.start()
        
        # COLLECT -> LOG_ANALYSIS（跳过 METRIC_ANALYSIS）
        with pytest.raises(ValueError, match="无效的阶段转换"):
            valid_session.advance_stage(DiagnosisStage.LOG_ANALYSIS)
    
    def test_advance_stage_before_start_raises_error(self, valid_session):
        """测试在启动前推进阶段"""
        with pytest.raises(ValueError, match="诊断未在分析中"):
            valid_session.advance_stage(DiagnosisStage.METRIC_ANALYSIS)
    
    def test_complete_session(self, valid_session):
        """测试完成会话"""
        valid_session.start()
        
        report = Report(content="# 诊断报告\n\n这是一份测试报告")
        valid_session.complete(report)
        
        assert valid_session.status == DiagnosisStatus.COMPLETED
        assert valid_session.stage == DiagnosisStage.REPORT_GENERATION
        assert valid_session.progress == 100
        assert valid_session.finished_at is not None
        assert valid_session.report == report
    
    def test_complete_session_before_start_raises_error(self, valid_session):
        """测试在启动前完成会话"""
        report = Report(content="# 诊断报告")
        
        with pytest.raises(ValueError, match="诊断未在分析中"):
            valid_session.complete(report)
    
    def test_fail_session(self, valid_session):
        """测试标记会话失败"""
        valid_session.start()
        valid_session.fail("连接 Prometheus 超时")
        
        assert valid_session.status == DiagnosisStatus.FAILED
        assert valid_session.finished_at is not None
        assert valid_session.error_message == "连接 Prometheus 超时"
    
    def test_fail_completed_session_raises_error(self, valid_session):
        """测试对已完成的会话标记失败"""
        valid_session.start()
        report = Report(content="# 诊断报告")
        valid_session.complete(report)
        
        with pytest.raises(ValueError, match="诊断已处于终态"):
            valid_session.fail("不应该失败")


class TestDiagnosisSessionEvidence:
    """测试证据管理"""
    
    def test_add_evidence(self, valid_session):
        """测试添加证据"""
        valid_session.start()
        
        evidence = Evidence(
            type=EvidenceType.METRIC,
            summary="JVM 堆内存使用率达到 95%",
            source="jvm_memory_used_bytes",
            time_range=valid_session.time_range,
            detail={"value": 0.95}
        )
        
        valid_session.add_evidence(evidence)
        
        assert len(valid_session.evidence) == 1
        assert valid_session.evidence[0] == evidence
    
    def test_add_duplicate_evidence_raises_error(self, valid_session):
        """测试添加重复证据"""
        valid_session.start()
        
        evidence = Evidence(
            id="test-evidence-001",
            type=EvidenceType.METRIC,
            summary="测试证据",
            source="test_metric",
            time_range=valid_session.time_range
        )
        
        valid_session.add_evidence(evidence)
        
        with pytest.raises(ValueError, match="证据已存在"):
            valid_session.add_evidence(evidence)
    
    def test_add_evidence_to_terminal_session_raises_error(self, valid_session):
        """测试向终态会话添加证据"""
        valid_session.start()
        report = Report(content="# 诊断报告")
        valid_session.complete(report)
        
        evidence = Evidence(
            type=EvidenceType.METRIC,
            summary="测试证据",
            source="test_metric",
            time_range=valid_session.time_range
        )
        
        with pytest.raises(ValueError, match="诊断已处于终态"):
            valid_session.add_evidence(evidence)
    
    def test_get_evidence_by_type(self, valid_session):
        """测试按类型获取证据"""
        valid_session.start()
        
        metric_evidence = Evidence(
            type=EvidenceType.METRIC,
            summary="指标证据",
            source="metric",
            time_range=valid_session.time_range
        )
        
        log_evidence = Evidence(
            type=EvidenceType.LOG,
            summary="日志证据",
            source="log",
            time_range=valid_session.time_range
        )
        
        valid_session.add_evidence(metric_evidence)
        valid_session.add_evidence(log_evidence)
        
        metric_list = valid_session.get_evidence_by_type("METRIC")
        assert len(metric_list) == 1
        assert metric_list[0].type == EvidenceType.METRIC
        
        log_list = valid_session.get_evidence_by_type("LOG")
        assert len(log_list) == 1
        assert log_list[0].type == EvidenceType.LOG


class TestDiagnosisSessionRootCause:
    """测试根因管理"""
    
    def test_add_root_cause(self, valid_session):
        """测试添加根因"""
        valid_session.start()
        
        root_cause = RootCause(
            cause="JVM 堆内存泄漏",
            confidence=Confidence(0.85)
        )
        
        valid_session.add_root_cause(root_cause)
        
        assert len(valid_session.root_causes) == 1
        assert valid_session.root_causes[0].rank == 1
    
    def test_add_multiple_root_causes_auto_sort(self, valid_session):
        """测试添加多个根因时自动排序"""
        valid_session.start()
        
        # 添加顺序：低 -> 高 -> 中
        rc1 = RootCause(cause="原因1", confidence=Confidence(0.5))
        rc2 = RootCause(cause="原因2", confidence=Confidence(0.9))
        rc3 = RootCause(cause="原因3", confidence=Confidence(0.7))
        
        valid_session.add_root_cause(rc1)
        valid_session.add_root_cause(rc2)
        valid_session.add_root_cause(rc3)
        
        # 期望排序：0.9 -> 0.7 -> 0.5
        assert valid_session.root_causes[0].confidence.value == 0.9
        assert valid_session.root_causes[0].rank == 1
        
        assert valid_session.root_causes[1].confidence.value == 0.7
        assert valid_session.root_causes[1].rank == 2
        
        assert valid_session.root_causes[2].confidence.value == 0.5
        assert valid_session.root_causes[2].rank == 3
    
    def test_add_root_cause_to_terminal_session_raises_error(self, valid_session):
        """测试向终态会话添加根因"""
        valid_session.start()
        report = Report(content="# 诊断报告")
        valid_session.complete(report)
        
        root_cause = RootCause(cause="不应该添加", confidence=Confidence(0.8))
        
        with pytest.raises(ValueError, match="诊断已处于终态"):
            valid_session.add_root_cause(root_cause)


class TestDiagnosisSessionQuery:
    """测试状态查询"""
    
    def test_is_terminal(self, valid_session):
        """测试判断是否终态"""
        assert valid_session.is_terminal() is False
        
        valid_session.start()
        assert valid_session.is_terminal() is False
        
        report = Report(content="# 诊断报告")
        valid_session.complete(report)
        assert valid_session.is_terminal() is True
    
    def test_is_analyzing(self, valid_session):
        """测试判断是否分析中"""
        assert valid_session.is_analyzing() is False
        
        valid_session.start()
        assert valid_session.is_analyzing() is True
        
        report = Report(content="# 诊断报告")
        valid_session.complete(report)
        assert valid_session.is_analyzing() is False
    
    def test_duration_seconds(self, valid_session):
        """测试计算耗时"""
        assert valid_session.duration_seconds() is None
        
        valid_session.start()
        duration = valid_session.duration_seconds()
        assert duration is not None
        assert duration >= 0


class TestDiagnosisSessionSerialization:
    """测试序列化"""
    
    def test_to_dict(self, valid_session):
        """测试转换为字典"""
        valid_session.start()
        
        data = valid_session.to_dict()
        
        assert data["diagnosisId"] == valid_session.diagnosis_id
        assert data["serviceName"] == "target-app"
        assert data["serviceInstance"] == "192.168.1.10:8080"
        assert data["status"] == "analyzing"
        assert data["stage"] == "collect"
        assert data["progress"] == 10
        assert data["triggerType"] == "manual"
        assert data["timeRange"]["start"] == "2026-11-16T10:00:00"
        assert data["timeRange"]["end"] == "2026-11-16T10:05:00"
        assert data["rootCauses"] == []
        assert data["evidence"] == []
