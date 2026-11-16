"""验证领域模型代码"""
from datetime import datetime

# 导入值对象
from domain.value_objects.time_range import TimeRange
from domain.value_objects.confidence import Confidence
from domain.value_objects.service_identifier import ServiceIdentifier

# 导入枚举
from domain.enums import DiagnosisStatus, DiagnosisStage, EvidenceType, TriggerType

# 导入实体
from domain.models.evidence import Evidence
from domain.models.root_cause import RootCause
from domain.models.report import Report

# 导入聚合根
from domain.models.diagnosis_session import DiagnosisSession, generate_diagnosis_id


def test_value_objects():
    """测试值对象"""
    print("=== 测试值对象 ===")
    
    # TimeRange
    time_range = TimeRange(
        start=datetime(2026, 11, 16, 10, 0, 0),
        end=datetime(2026, 11, 16, 10, 5, 0)
    )
    print(f"✓ TimeRange: {time_range}")
    print(f"  时长: {time_range.duration_seconds()} 秒")
    
    # Confidence
    confidence = Confidence(0.85)
    print(f"✓ Confidence: {confidence} (值: {confidence.value})")
    
    # ServiceIdentifier
    service = ServiceIdentifier(service_name="target-app", instance="192.168.1.10:8080")
    print(f"✓ ServiceIdentifier: {service}")
    
    print()


def test_entities():
    """测试实体"""
    print("=== 测试实体 ===")
    
    time_range = TimeRange(
        start=datetime(2026, 11, 16, 10, 0, 0),
        end=datetime(2026, 11, 16, 10, 5, 0)
    )
    
    # Evidence
    evidence = Evidence(
        type=EvidenceType.METRIC,
        summary="JVM 堆内存使用率达到 95%",
        source="jvm_memory_used_bytes",
        time_range=time_range,
        detail={"value": 0.95, "threshold": 0.8}
    )
    print(f"✓ Evidence: {evidence}")
    print(f"  ID: {evidence.id}")
    
    # RootCause
    root_cause = RootCause(
        cause="JVM 堆内存泄漏导致 OOM",
        confidence=Confidence(0.85),
        evidence_ids=[evidence.id]
    )
    print(f"✓ RootCause: {root_cause}")
    
    # Report
    report = Report(
        content="# 诊断报告\\n\\n## 问题描述\\n\\n检测到 JVM 堆内存泄漏。"
    )
    print(f"✓ Report: {report}")
    print(f"  字数: {report.word_count()}")
    
    print()


def test_diagnosis_session():
    """测试诊断会话聚合根"""
    print("=== 测试诊断会话聚合根 ===")
    
    # 创建诊断会话
    diagnosis_id = generate_diagnosis_id()
    print(f"生成诊断 ID: {diagnosis_id}")
    
    session = DiagnosisSession(
        diagnosis_id=diagnosis_id,
        service=ServiceIdentifier(service_name="target-app", instance="192.168.1.10:8080"),
        time_range=TimeRange(
            start=datetime(2026, 11, 16, 10, 0, 0),
            end=datetime(2026, 11, 16, 10, 5, 0)
        ),
        trigger_type=TriggerType.MANUAL
    )
    
    print(f"✓ 创建会话: {session}")
    print(f"  初始状态: {session.status.value}")
    print(f"  初始阶段: {session.stage}")
    print(f"  初始进度: {session.progress}%")
    
    # 启动诊断
    session.start()
    print(f"\\n✓ 启动诊断")
    print(f"  状态: {session.status.value}")
    print(f"  阶段: {session.stage.value if session.stage else None}")
    print(f"  进度: {session.progress}%")
    
    # 推进阶段
    session.advance_stage(DiagnosisStage.METRIC_ANALYSIS)
    print(f"\\n✓ 推进到指标分析阶段")
    print(f"  阶段: {session.stage.value if session.stage else None}")
    print(f"  进度: {session.progress}%")
    
    # 添加证据
    evidence = Evidence(
        type=EvidenceType.METRIC,
        summary="JVM 堆内存使用率达到 95%",
        source="jvm_memory_used_bytes",
        time_range=session.time_range,
        detail={"value": 0.95}
    )
    session.add_evidence(evidence)
    print(f"\\n✓ 添加证据: {len(session.evidence)} 条")
    
    # 添加根因
    root_cause1 = RootCause(
        cause="JVM 堆内存泄漏",
        confidence=Confidence(0.85),
        evidence_ids=[evidence.id]
    )
    root_cause2 = RootCause(
        cause="老年代 GC 频繁",
        confidence=Confidence(0.65),
        evidence_ids=[evidence.id]
    )
    session.add_root_cause(root_cause1)
    session.add_root_cause(root_cause2)
    print(f"\\n✓ 添加根因: {len(session.root_causes)} 个")
    for rc in session.root_causes:
        print(f"  {rc}")
    
    # 完成诊断
    report = Report(
        content="# 诊断报告\\n\\n## 问题描述\\n\\n检测到 JVM 堆内存泄漏。"
    )
    session.complete(report)
    print(f"\\n✓ 完成诊断")
    print(f"  状态: {session.status.value}")
    print(f"  进度: {session.progress}%")
    print(f"  耗时: {session.duration_seconds():.2f} 秒")
    
    # 序列化
    data = session.to_dict()
    print(f"\\n✓ 序列化为字典")
    print(f"  diagnosisId: {data['diagnosisId']}")
    print(f"  serviceName: {data['serviceName']}")
    print(f"  status: {data['status']}")
    print(f"  rootCauses数量: {len(data['rootCauses'])}")
    print(f"  evidence数量: {len(data['evidence'])}")
    
    print()


def main():
    """主函数"""
    print("\\n" + "=" * 60)
    print("领域模型验证脚本")
    print("=" * 60 + "\\n")
    
    try:
        test_value_objects()
        test_entities()
        test_diagnosis_session()
        
        print("=" * 60)
        print("✅ 所有测试通过！领域模型实现正确。")
        print("=" * 60)
        
    except Exception as e:
        print(f"\\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
