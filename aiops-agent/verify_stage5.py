"""阶段五验证脚本"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """验证阶段五实现"""
    print("=" * 80)
    print("阶段五 Agent 引擎验证")
    print("=" * 80)

    # 1. 验证 LLM 客户端
    print("\n[1/9] 验证 LLM 客户端...")
    try:
        from infrastructure.llm import LLMClient, LLMClientError

        llm_client = LLMClient()
        print(f"   ✓ LLMClient 可实例化: {llm_client}")
        print(f"   ✓ 启用状态: {llm_client.enabled}")
        print(f"   ✓ 模型: {llm_client.model}")
    except Exception as e:
        print(f"   ✗ LLM 客户端错误: {e}")
        return False

    # 2. 验证 Prompt 模板
    print("\n[2/9] 验证 Prompt 模板...")
    try:
        from application.agents.prompts import PromptTemplate

        messages = PromptTemplate.format_metric_agent_prompt(
            service_name="test-service",
            time_range="2024-01-01 ~ 2024-01-02",
            metrics_data="{}",
        )
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        print("   ✓ Prompt 模板格式化正确")
    except Exception as e:
        print(f"   ✗ Prompt 模板错误: {e}")
        return False

    # 3. 验证 Agent 工具集
    print("\n[3/9] 验证 Agent 工具集...")
    try:
        from application.agents.tools import AgentTools

        print("   ✓ AgentTools 导入成功")
    except Exception as e:
        print(f"   ✗ Agent 工具集错误: {e}")
        return False

    # 4. 验证 Metric Agent
    print("\n[4/9] 验证 Metric Agent...")
    try:
        from application.agents.metric_agent import MetricAgent

        print("   ✓ MetricAgent 导入成功")
    except Exception as e:
        print(f"   ✗ Metric Agent 错误: {e}")
        return False

    # 5. 验证 Log Agent
    print("\n[5/9] 验证 Log Agent...")
    try:
        from application.agents.log_agent import LogAgent

        print("   ✓ LogAgent 导入成功")
    except Exception as e:
        print(f"   ✗ Log Agent 错误: {e}")
        return False

    # 6. 验证 Trace Agent
    print("\n[6/9] 验证 Trace Agent...")
    try:
        from application.agents.trace_agent import TraceAgent

        print("   ✓ TraceAgent 导入成功")
    except Exception as e:
        print(f"   ✗ Trace Agent 错误: {e}")
        return False

    # 7. 验证 RCA Agent
    print("\n[7/9] 验证 RCA Agent...")
    try:
        from application.agents.rca_agent import RCAAgent

        print("   ✓ RCAAgent 导入成功")
    except Exception as e:
        print(f"   ✗ RCA Agent 错误: {e}")
        return False

    # 8. 验证 LangGraph 状态和图
    print("\n[8/9] 验证 LangGraph...")
    try:
        from application.agents.diagnosis_state import DiagnosisState
        from application.agents.diagnosis_graph import build_diagnosis_graph

        print("   ✓ DiagnosisState 导入成功")
        print("   ✓ build_diagnosis_graph 导入成功")
    except Exception as e:
        print(f"   ✗ LangGraph 错误: {e}")
        return False

    # 9. 验证诊断引擎服务
    print("\n[9/9] 验证诊断引擎服务...")
    try:
        from application.services.diagnosis_engine_service import (
            DiagnosisEngineService,
        )

        print("   ✓ DiagnosisEngineService 导入成功")
    except Exception as e:
        print(f"   ✗ 诊断引擎服务错误: {e}")
        return False

    # 统计信息
    print("\n" + "=" * 80)
    print("✅ 阶段五 Agent 引擎验证通过")
    print("=" * 80)

    print("\n已创建文件清单:")
    files = [
        "infrastructure/llm/__init__.py",
        "infrastructure/llm/llm_client.py",
        "application/agents/__init__.py",
        "application/agents/prompts.py",
        "application/agents/tools.py",
        "application/agents/metric_agent.py",
        "application/agents/log_agent.py",
        "application/agents/trace_agent.py",
        "application/agents/rca_agent.py",
        "application/agents/diagnosis_state.py",
        "application/agents/diagnosis_graph.py",
        "application/services/diagnosis_engine_service.py",
    ]

    for i, file in enumerate(files, 1):
        print(f"  {i:2d}. {file}")

    print(f"\n总计: {len(files)} 个文件")

    print("\n核心组件:")
    print("  • LLM 客户端: OpenAI API 兼容")
    print("  • Prompt 模板: 4 个 Agent 的提示词")
    print("  • Agent 工具集: 查询 Prometheus/Loki/Tempo")
    print("  • 4 个 Agent: Metric/Log/Trace/RCA")
    print("  • LangGraph: 状态定义 + Graph 构建")
    print("  • 诊断引擎: 编排 Agent 执行")

    print("\n配置更新:")
    print("  • config/settings.py: 增加 LLM 配置")
    print("  • .env.example: 增加 LLM 环境变量")

    print("\n下一步:")
    print("  • 阶段六: API 层实现（REST + WebSocket）")
    print("  • 测试: 补充单元测试和集成测试")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
