"""快速语法检查脚本"""

import sys
from pathlib import Path

def check_imports():
    """检查关键模块是否可以导入"""
    errors = []
    
    modules_to_check = [
        "config.settings",
        "infrastructure.external.mock_data",
        "application.agents.tools",
        "infrastructure.llm.llm_client",
        "domain.models.diagnosis_session",
    ]
    
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"✓ {module}")
        except Exception as e:
            error_msg = f"✗ {module}: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
    
    return errors

def main():
    print("=" * 80)
    print("快速语法检查")
    print("=" * 80)
    print()
    
    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    errors = check_imports()
    
    print()
    print("=" * 80)
    if not errors:
        print("✓ 所有模块导入成功！")
        print()
        print("下一步：")
        print("1. 确保 .env 文件中设置了 TEST_MODE=true")
        print("2. 启动服务: python -m uvicorn main:app --reload --port 8000")
        print("3. 运行集成测试: python test_integration.py")
        return 0
    else:
        print(f"✗ 发现 {len(errors)} 个错误")
        print()
        print("错误详情:")
        for error in errors:
            print(f"  {error}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
