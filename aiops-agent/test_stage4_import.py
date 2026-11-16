"""测试阶段四导入"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 测试所有导入
try:
    print("测试 DTO...")
    from application.dto import (
        QueryDiagnosisRequest,
        TriggerDiagnosisRequest,
        DiagnosisReportResponse,
        DiagnosisSessionResponse,
    )
    print("✓ DTO 导入成功")

    print("\n测试映射器...")
    from application.mappers import DiagnosisDTOMapper
    print("✓ 映射器导入成功")

    print("\n测试用例...")
    from application.use_cases import (
        TriggerDiagnosisUseCase,
        QueryDiagnosisUseCase,
        GetDiagnosisReportUseCase,
        CancelDiagnosisUseCase,
        RetryDiagnosisUseCase,
    )
    print("✓ 用例导入成功")

    print("\n测试服务...")
    from application.services import (
        DiagnosisApplicationService,
        EventHandlerService,
    )
    print("✓ 服务导入成功")

    print("\n测试容器...")
    from application.container import Container, container
    print("✓ 容器导入成功")

    print("\n✅ 所有导入成功！")
except Exception as e:
    print(f"\n❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
