#!/usr/bin/env python
"""简单的测试运行脚本"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试所有模块导入"""
    print("=" * 60)
    print("测试模块导入...")
    print("=" * 60)
    
    try:
        # 值对象
        from domain.value_objects.time_range import TimeRange
        from domain.value_objects.confidence import Confidence
        from domain.value_objects.service_identifier import ServiceIdentifier
        print("✓ 值对象导入成功")
        
        # 枚举
        from domain.enums import DiagnosisStatus, DiagnosisStage, EvidenceType, TriggerType
        print("✓ 枚举导入成功")
        
        # 实体
        from domain.models.evidence import Evidence
        from domain.models.root_cause import RootCause
        from domain.models.report import Report
        print("✓ 实体导入成功")
        
        # 聚合根
        from domain.models.diagnosis_session import DiagnosisSession
        print("✓ 聚合根导入成功")
        
        # 领域服务
        from domain.services.anomaly_detector import AnomalyDetector
        from domain.services.evidence_aggregator import EvidenceAggregator
        from domain.services.root_cause_analyzer import RootCauseAnalyzer
        print("✓ 领域服务导入成功")
        
        # 领域事件
        from domain.events.diagnosis_events import (
            DiagnosisTriggered,
            StageCompleted,
            DiagnosisCompleted,
            DiagnosisFailed
        )
        print("✓ 领域事件导入成功")
        
        # 仓储接口
        from domain.repositories.diagnosis_session_repository import DiagnosisSessionRepository
        print("✓ 仓储接口导入成功")
        
        print("\n所有模块导入成功！\n")
        return True
    except Exception as e:
        print(f"\n❌ 导入失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_value_objects():
    """测试值对象"""
    print("=" * 60)
    print("测试值对象...")
    print("=" * 60)
    
    try:
        from datetime import datetime, timedelta
        from domain.value_objects.time_range import TimeRange
        from domain.value_objects.confidence import Confidence
        from domain.value_objects.service_identifier import ServiceIdentifier
        
        # TimeRange
        now = datetime.now()
        start = now - timedelta(hours=1)
        tr = TimeRange(start_time=start, end_time=now)
        assert tr.duration_minutes == 60
        print(f"✓ TimeRange: {tr.duration_minutes} 分钟")
        
        # Confidence
        conf = Confidence(value=0.85)
        assert conf.is_high()
        print(f"✓ Confidence: {conf.value} (高置信度)")
        
        # ServiceIdentifier
        sid = ServiceIdentifier(service_name="user-service", environment="prod")
        assert str(sid) == "user-service@prod"
        print(f"✓ ServiceIdentifier: {sid}")
        
        print("\n值对象测试通过！\n")
        return True
    except Exception as e:
        print(f"\n❌ 值对象测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_domain_services():
    """测试领域服务"""
    print("=" * 60)
    print("测试领域服务...")
    print("=" * 60)
    
    try:
        from datetime import datetime, timedelta
        from domain.services.anomaly_detector import AnomalyDetector
        from domain.services.evidence_aggregator import EvidenceAggregator
        from domain.services.root_cause_analyzer import RootCauseAnalyzer
        from domain.models.evidence import Evidence
        from domain.enums import EvidenceType
        
        # AnomalyDetector
        detector = AnomalyDetector()
        
        # 简单阈值检测
        is_anomaly = detector.simple_threshold_detect(value=150, threshold=100)
        assert is_anomaly
        print(f"✓ 简单阈值检测: 150 > 100 = {is_anomaly}")
        
        # 环比检测
        is_anomaly, detail = detector.compare_detect(current=150, baseline=100, threshold=0.3)
        assert is_anomaly
        print(f"✓ 环比检测: 变化率 = {detail['change_rate']:.1%}")
        
        # EvidenceAggregator
        aggregator = EvidenceAggregator()
        evidences = [
            Evidence(
                evidence_type=EvidenceType.METRIC,
                source="cpu_usage",
                description="CPU 使用率高",
                confidence=0.9,
                timestamp=datetime.now()
            ),
            Evidence(
                evidence_type=EvidenceType.LOG,
                source="error_logs",
                description="发现错误日志",
                confidence=0.6,
                timestamp=datetime.now()
            )
        ]
        
        filtered = aggregator.filter_by_confidence(evidences, min_confidence=0.7)
        assert len(filtered) == 1
        print(f"✓ 证据过滤: {len(evidences)} -> {len(filtered)} (置信度 >= 0.7)")
        
        grouped = aggregator.group_by_type(evidences)
        assert EvidenceType.METRIC in grouped
        assert EvidenceType.LOG in grouped
        print(f"✓ 证据分组: {len(grouped)} 个类型")
        
        # RootCauseAnalyzer
        analyzer = RootCauseAnalyzer()
        root_causes = analyzer.analyze(evidences)
        assert len(root_causes) > 0
        print(f"✓ 根因分析: 识别出 {len(root_causes)} 个根因")
        
        print("\n领域服务测试通过！\n")
        return True
    except Exception as e:
        print(f"\n❌ 领域服务测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_diagnosis_session():
    """测试诊断会话"""
    print("=" * 60)
    print("测试诊断会话聚合根...")
    print("=" * 60)
    
    try:
        from datetime import datetime, timedelta
        from domain.models.diagnosis_session import DiagnosisSession
        from domain.value_objects.time_range import TimeRange
        from domain.value_objects.service_identifier import ServiceIdentifier
        from domain.enums import DiagnosisStatus
        
        # 创建会话
        now = datetime.now()
        time_range = TimeRange(
            start_time=now - timedelta(hours=1),
            end_time=now
        )
        service = ServiceIdentifier(service_name="user-service", environment="prod")
        
        session = DiagnosisSession(
            session_id="test-001",
            service_identifier=service,
            time_range=time_range
        )
        
        assert session.status == DiagnosisStatus.PENDING
        print(f"✓ 创建会话: {session.session_id}")
        
        # 状态转换
        session.start_collecting()
        assert session.status == DiagnosisStatus.COLLECTING
        print(f"✓ 状态转换: {DiagnosisStatus.PENDING.value} -> {DiagnosisStatus.COLLECTING.value}")
        
        session.start_analyzing()
        assert session.status == DiagnosisStatus.ANALYZING
        print(f"✓ 状态转换: {DiagnosisStatus.COLLECTING.value} -> {DiagnosisStatus.ANALYZING.value}")
        
        # 领域事件
        events = session.collect_events()
        assert len(events) > 0
        print(f"✓ 领域事件: 收集到 {len(events)} 个事件")
        
        print("\n诊断会话测试通过！\n")
        return True
    except Exception as e:
        print(f"\n❌ 诊断会话测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "阶段二：领域模型验证" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    
    # 1. 导入测试
    results.append(("模块导入", test_imports()))
    
    # 2. 值对象测试
    results.append(("值对象", test_value_objects()))
    
    # 3. 领域服务测试
    results.append(("领域服务", test_domain_services()))
    
    # 4. 诊断会话测试
    results.append(("诊断会话", test_diagnosis_session()))
    
    # 汇总结果
    print("=" * 60)
    print("测试汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "❌ 失败"
        print(f"{name:20s}: {status}")
    
    print()
    print(f"总计: {passed}/{total} 通过")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 所有测试通过！阶段二领域模型实现完成。\n")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 项测试失败。\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
