"""阶段四验证脚本"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """验证阶段四实现"""
    print("=" * 80)
    print("阶段四应用层验证")
    print("=" * 80)

    # 1. 验证 DTO 定义
    print("\n[1/7] 验证 DTO 定义...")
    try:
        from application.dto.requests import (
            QueryDiagnosisRequest,
            TriggerDiagnosisRequest,
        )
        from application.dto.responses import (
            DiagnosisReportResponse,
            DiagnosisSessionResponse,
            EvidenceResponse,
            RootCauseResponse,
            TriggerDiagnosisResponse,
        )

        # 测试请求 DTO
        request = TriggerDiagnosisRequest(
            service_name="test-service",
            environment="prod",
            time_range_minutes=60,
            trigger_source="manual",
        )
        assert request.service_name == "test-service"
        assert request.time_range_minutes == 60

        query_request = QueryDiagnosisRequest(session_id="test-session", limit=10)
        assert query_request.session_id == "test-session"
        assert query_request.limit == 10

        print("   ✓ 请求 DTO 正常")
        print("   ✓ 响应 DTO 正常")
    except Exception as e:
        print(f"   ✗ DTO 定义错误: {e}")
        return False

    # 2. 验证 DTO 映射器
    print("\n[2/7] 验证 DTO 映射器...")
    try:
        from application.mappers.diagnosis_dto_mapper import DiagnosisDTOMapper

        mapper = DiagnosisDTOMapper()
        print(f"   ✓ DiagnosisDTOMapper 可实例化: {mapper}")
    except Exception as e:
        print(f"   ✗ 映射器错误: {e}")
        return False

    # 3. 验证触发诊断用例
    print("\n[3/7] 验证触发诊断用例...")
    try:
        from application.use_cases.trigger_diagnosis_use_case import (
            DiagnosisAlreadyInProgressError,
            TriggerDiagnosisUseCase,
        )

        print("   ✓ TriggerDiagnosisUseCase 导入成功")
        print("   ✓ DiagnosisAlreadyInProgressError 导入成功")
    except Exception as e:
        print(f"   ✗ 触发诊断用例错误: {e}")
        return False

    # 4. 验证查询诊断用例
    print("\n[4/7] 验证查询诊断用例...")
    try:
        from application.use_cases.query_diagnosis_use_case import QueryDiagnosisUseCase

        print("   ✓ QueryDiagnosisUseCase 导入成功")
    except Exception as e:
        print(f"   ✗ 查询诊断用例错误: {e}")
        return False

    # 5. 验证其他用例
    print("\n[5/7] 验证其他用例...")
    try:
        from application.use_cases.cancel_diagnosis_use_case import (
            CancelDiagnosisUseCase,
        )
        from application.use_cases.get_diagnosis_report_use_case import (
            GetDiagnosisReportUseCase,
        )
        from application.use_cases.retry_diagnosis_use_case import RetryDiagnosisUseCase

        print("   ✓ GetDiagnosisReportUseCase 导入成功")
        print("   ✓ CancelDiagnosisUseCase 导入成功")
        print("   ✓ RetryDiagnosisUseCase 导入成功")
    except Exception as e:
        print(f"   ✗ 其他用例错误: {e}")
        return False

    # 6. 验证应用服务
    print("\n[6/7] 验证应用服务...")
    try:
        from application.services.diagnosis_application_service import (
            DiagnosisApplicationService,
        )
        from application.services.event_handler_service import EventHandlerService

        print("   ✓ DiagnosisApplicationService 导入成功")
        print("   ✓ EventHandlerService 导入成功")
    except Exception as e:
        print(f"   ✗ 应用服务错误: {e}")
        return False

    # 7. 验证依赖注入容器
    print("\n[7/7] 验证依赖注入容器...")
    try:
        from application.container import Container, container

        test_container = Container()
        print(f"   ✓ Container 可实例化: {test_container}")
        print(f"   ✓ 全局 container 实例存在: {container}")
    except Exception as e:
        print(f"   ✗ 依赖注入容器错误: {e}")
        return False

    # 统计信息
    print("\n" + "=" * 80)
    print("✅ 阶段四应用层验证通过")
    print("=" * 80)

    print("\n已创建文件清单:")
    files = [
        "application/dto/requests.py",
        "application/dto/responses.py",
        "application/dto/__init__.py",
        "application/mappers/diagnosis_dto_mapper.py",
        "application/mappers/__init__.py",
        "application/use_cases/trigger_diagnosis_use_case.py",
        "application/use_cases/query_diagnosis_use_case.py",
        "application/use_cases/get_diagnosis_report_use_case.py",
        "application/use_cases/cancel_diagnosis_use_case.py",
        "application/use_cases/retry_diagnosis_use_case.py",
        "application/use_cases/__init__.py",
        "application/services/diagnosis_application_service.py",
        "application/services/event_handler_service.py",
        "application/services/__init__.py",
        "application/container.py",
    ]

    for i, file in enumerate(files, 1):
        print(f"  {i:2d}. {file}")

    print(f"\n总计: {len(files)} 个文件")

    print("\n核心组件:")
    print("  • DTO: 2 个请求 DTO + 5 个响应 DTO")
    print("  • 映射器: 1 个 DTO 映射器（4 个映射方法）")
    print("  • 用例: 5 个用例（触发、查询、报告、取消、重试）")
    print("  • 应用服务: 2 个服务（诊断服务、事件处理服务）")
    print("  • 容器: 1 个依赖注入容器")

    print("\n下一步:")
    print("  • 阶段五: Agent 引擎实现（LangGraph 集成）")
    print("  • 阶段六: API 层实现（REST + WebSocket）")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
