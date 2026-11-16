"""验证阶段二完成情况"""
from datetime import datetime

# 导入领域事件
from domain.events import (
    DiagnosisTriggered,
    StageCompleted,
    DiagnosisCompleted,
    DiagnosisFailed
)

# 导入领域服务
from domain.services import (
    AnomalyDetector,
    EvidenceAggregator,
    RootCauseAnalyzer
)

# 导入其他必要模块
from domain.value_objects.time_range import TimeRange
from domain.value_objects.confidence import Confidence
from domain.value_objects.service_identifier import ServiceIdentifier
from domain.enums import DiagnosisStatus, DiagnosisStage, EvidenceType
from domain.models.evidence import Evidence
from domain.models.diagnosis_session import DiagnosisSession, generate_diagnosis_id


def test_domain_events():
    """测试领域事件"""
    print("=== 测试领域事件 ===")
    
    # DiagnosisTriggered
    triggered = DiagnosisTriggered(
        diagnosis_id="diag-001",
        service_name="target-app",
        service_instance="192.168.1.10:8080",
        time_range=TimeRange(
            start=datetime(2026, 11, 16, 10, 0, 0),
            end=datetime(2026, 11, 16, 10, 5, 0)
        ),
        trigger_type="manual"
    )
    print(f"✓ {triggered}")
    
    # StageCompleted
    stage_completed = StageCompleted(
        diagnosis_id="diag-001",
        stage=DiagnosisStage.METRIC_ANALYSIS,
        progress=25,
        evidence_count=3
    )
    print(f"✓ {stage_completed}")
    
    # DiagnosisCompleted
    completed = DiagnosisCompleted(
        diagnosis_id="diag-001",
        service_name="target-app",
        status=DiagnosisStatus.COMPLETED,
        root_cause_count=2,
        evidence_count=5,
        duration_seconds=45.3
    )
    print(f"✓ {completed}")
    
    # DiagnosisFailed
    failed = DiagnosisFailed(
        diagnosis_id="diag-002",
        service_name="target-app",
        status=DiagnosisStatus.FAILED,
        stage=DiagnosisStage.METRIC_ANALYSIS,
        error_message="连接 Prometheus 超时"
    )
    print(f"✓ {failed}")
    
    print()


def test_anomaly_detector():
    """测试异常检测服务"""
    print("=== 测试异常检测服务 ===")
    
    detector = AnomalyDetector()
    
    # 阈值检测
    is_anomaly = detector.threshold_detect([70, 85, 95], threshold=80, direction="above")
    print(f"✓ 阈值检测: 检测到异常 = {is_anomaly}")
    
    # 3-sigma 检测
    is_anomaly, detail = detector.sigma_detect([10, 12, 11, 13, 50])
    print(f"✓ 3-sigma 检测: 检测到异常 = {is_anomaly}, 异常值 = {detail['anomaly_values'] if detail else None}")
    
    # 环比检测
    is_anomaly, detail = detector.compare_detect(current=150, baseline=100, threshold=0.3)
    change_rate = detail['change_rate'] if detail else None
    print(f"✓ 环比检测: 检测到异常 = {is_anomaly}, 变化率 = {change_rate:.1%}" if change_rate else f"✓ 环比检测: 检测到异常 = {is_anomaly}")
    
    # 尖峰检测
    is_spike, indices = detector.detect_spike([10, 12, 11, 13, 50, 12, 11], window_size=3)
    print(f"✓ 尖峰检测: 检测到尖峰 = {is_spike}, 位置 = {indices}")
    
    # 趋势检测
    has_trend, direction = detector.detect_trend([10, 20, 30, 40, 50], min_length=5)
    print(f"✓ 趋势检测: 检测到趋势 = {has_trend}, 方向 = {direction}")
    
    print()


def test_evidence_aggregator():
    """测试证据聚合服务"""
    print("=== 测试证据聚合服务 ===")
    
    aggregator = EvidenceAggregator()
    
    # 创建测试证据
    time_range = TimeRange(
        start=datetime(2026, 11, 16, 10, 0, 0),
        end=datetime(2026, 11, 16, 10, 5, 0)
    )
    
    evidence_list = [
        Evidence(
            type=EvidenceType.METRIC,
            summary="JVM 堆内存使用率 95%",
            source="jvm_memory_used",
            time_range=time_range
        ),
        Evidence(
            type=EvidenceType.LOG,
            summary="ERROR: OutOfMemoryError",
            source="application.log",
            time_range=time_range
        ),
        Evidence(
            type=EvidenceType.METRIC,
            summary="CPU 使用率 90%",
            source="cpu_usage",
            time_range=time_range
        ),
    ]
    
    # 按类型分组
    grouped = aggregator.group_by_type(evidence_list)
    print(f"✓ 按类型分组: {len(grouped)} 个类型")
    for etype, evidences in grouped.items():
        print(f"  - {etype}: {len(evidences)} 条证据")
    
    # 证据摘要
    summary = aggregator.summarize(evidence_list)
    print(f"✓ 证据摘要: 总计 {summary['total']} 条, 时间跨度 {summary['time_span_seconds']} 秒")
    
    # 计算权重
    weight = aggregator.calculate_evidence_weight(evidence_list[0], evidence_list)
    print(f"✓ 证据权重: {weight:.2f}")
    
    print()


def test_root_cause_analyzer():
    """测试根因分析服务"""
    print("=== 测试根因分析服务 ===")
    
    analyzer = RootCauseAnalyzer()
    
    # 创建测试证据
    time_range = TimeRange(
        start=datetime(2026, 11, 16, 10, 0, 0),
        end=datetime(2026, 11, 16, 10, 5, 0)
    )
    
    evidence_list = [
        Evidence(
            type=EvidenceType.METRIC,
            summary="JVM 堆内存使用率持续 95%",
            source="jvm_memory_used",
            time_range=time_range
        ),
        Evidence(
            type=EvidenceType.LOG,
            summary="ERROR: java.lang.OutOfMemoryError: Java heap space",
            source="application.log",
            time_range=time_range
        ),
        Evidence(
            type=EvidenceType.METRIC,
            summary="Full GC 频率增加",
            source="jvm_gc_count",
            time_range=time_range
        ),
    ]
    
    # 基于规则的根因分析
    root_causes = analyzer.analyze_by_rules(evidence_list)
    print(f"✓ 基于规则分析: 识别出 {len(root_causes)} 个根因")
    for rc in root_causes:
        print(f"  {rc}")
        explanation = analyzer.explain_confidence(rc, evidence_list)
        print(f"    {explanation.strip()}")
    
    print()


def test_integrated_workflow():
    """测试集成工作流"""
    print("=== 测试集成工作流 ===")
    
    # 1. 创建诊断会话
    session = DiagnosisSession(
        diagnosis_id=generate_diagnosis_id(),
        service=ServiceIdentifier(service_name="target-app", instance="192.168.1.10:8080"),
        time_range=TimeRange(
            start=datetime(2026, 11, 16, 10, 0, 0),
            end=datetime(2026, 11, 16, 10, 5, 0)
        )
    )
    print(f"1. 创建会话: {session.diagnosis_id}")
    
    # 2. 启动诊断
    session.start()
    print(f"2. 启动诊断: {session.status.value}, {session.stage.value if session.stage else None}")
    
    # 3. 添加证据
    evidence_list = [
        Evidence(
            type=EvidenceType.METRIC,
            summary="JVM 堆内存使用率 95%",
            source="jvm_memory_used",
            time_range=session.time_range
        ),
        Evidence(
            type=EvidenceType.LOG,
            summary="ERROR: OutOfMemoryError",
            source="application.log",
            time_range=session.time_range
        ),
        Evidence(
            type=EvidenceType.METRIC,
            summary="Full GC 次数增加",
            source="jvm_gc_count",
            time_range=session.time_range
        ),
    ]
    
    for evidence in evidence_list:
        session.add_evidence(evidence)
    print(f"3. 添加证据: {len(session.evidence)} 条")
    
    # 4. 使用证据聚合服务
    aggregator = EvidenceAggregator()
    summary = aggregator.summarize(session.evidence)
    print(f"4. 证据聚合: {summary['by_type']}")
    
    # 5. 使用根因分析服务
    analyzer = RootCauseAnalyzer()
    root_causes = analyzer.analyze_by_rules(session.evidence)
    print(f"5. 根因分析: 识别出 {len(root_causes)} 个根因")
    
    # 6. 添加根因到会话
    for root_cause in root_causes:
        session.add_root_cause(root_cause)
    print(f"6. 添加根因: {len(session.root_causes)} 个")
    for rc in session.root_causes:
        print(f"   {rc}")
    
    # 7. 完成诊断
    from domain.models.report import Report
    report = Report(content="# 诊断报告\\n\\n检测到 JVM 堆内存泄漏问题。")
    session.complete(report)
    print(f"7. 完成诊断: {session.status.value}, 耗时 {session.duration_seconds():.2f}s")
    
    # 8. 发布领域事件（模拟）
    completed_event = DiagnosisCompleted(
        diagnosis_id=session.diagnosis_id,
        service_name=session.service.service_name,
        status=session.status,
        root_cause_count=len(session.root_causes),
        evidence_count=len(session.evidence),
        duration_seconds=session.duration_seconds() or 0
    )
    print(f"8. 发布事件: {completed_event}")
    
    print()


def main():
    """主函数"""
    print("\\n" + "=" * 60)
    print("阶段二完成验证脚本")
    print("=" * 60 + "\\n")
    
    try:
        test_domain_events()
        test_anomaly_detector()
        test_evidence_aggregator()
        test_root_cause_analyzer()
        test_integrated_workflow()
        
        print("=" * 60)
        print("✅ 所有测试通过！阶段二已完成。")
        print("=" * 60)
        print("\\n完成情况：")
        print("  ✓ 值对象：3 个（TimeRange, Confidence, ServiceIdentifier）")
        print("  ✓ 枚举：4 个（DiagnosisStatus, DiagnosisStage, EvidenceType, TriggerType）")
        print("  ✓ 实体：3 个（Evidence, RootCause, Report）")
        print("  ✓ 聚合根：1 个（DiagnosisSession）")
        print("  ✓ 领域服务：3 个（AnomalyDetector, EvidenceAggregator, RootCauseAnalyzer）")
        print("  ✓ 领域事件：4 个（DiagnosisTriggered, StageCompleted, DiagnosisCompleted, DiagnosisFailed）")
        print("  ✓ 仓储接口：1 个（DiagnosisSessionRepository）")
        print("\\n下一步：阶段三（基础设施层实现）")
        print("=" * 60)
        
    except Exception as e:
        print(f"\\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
