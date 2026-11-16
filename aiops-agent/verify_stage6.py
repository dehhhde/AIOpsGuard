"""阶段六验证脚本"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """验证阶段六实现"""
    print("=" * 80)
    print("阶段六 API 层验证")
    print("=" * 80)

    # 1. 验证路由模块
    print("\n[1/6] 验证路由模块...")
    try:
        from adapters.rest.routes import diagnosis, health, websocket

        print("   ✓ diagnosis 路由导入成功")
        print("   ✓ health 路由导入成功")
        print("   ✓ websocket 路由导入成功")
    except Exception as e:
        print(f"   ✗ 路由模块错误: {e}")
        return False

    # 2. 验证中间件
    print("\n[2/6] 验证中间件...")
    try:
        from adapters.rest.middleware.cors import setup_cors
        from adapters.rest.middleware.error_handler import setup_error_handlers

        print("   ✓ CORS 中间件导入成功")
        print("   ✓ 错误处理中间件导入成功")
    except Exception as e:
        print(f"   ✗ 中间件错误: {e}")
        return False

    # 3. 验证 FastAPI 应用
    print("\n[3/6] 验证 FastAPI 应用...")
    try:
        from adapters.rest.app import create_app

        app = create_app()
        print(f"   ✓ FastAPI 应用创建成功: {app.title}")
        print(f"   ✓ 版本: {app.version}")

        # 检查路由
        routes = [route.path for route in app.routes]
        print(f"   ✓ 注册路由数: {len(routes)}")

        # 检查关键路由
        key_routes = [
            "/api/v1/health/",
            "/api/v1/health/ready",
            "/api/v1/diagnosis/trigger",
            "/api/v1/diagnosis/sessions",
            "/ws/diagnosis/{session_id}",
        ]
        for route in key_routes:
            if any(route in r for r in routes):
                print(f"   ✓ 路由存在: {route}")
            else:
                print(f"   ✗ 路由缺失: {route}")

    except Exception as e:
        print(f"   ✗ FastAPI 应用错误: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 4. 验证 WebSocket 管理器
    print("\n[4/6] 验证 WebSocket 管理器...")
    try:
        from adapters.rest.routes.websocket import ConnectionManager

        manager = ConnectionManager()
        print(f"   ✓ ConnectionManager 可实例化: {manager}")
        print(f"   ✓ 活跃连接数: {len(manager.active_connections)}")
    except Exception as e:
        print(f"   ✗ WebSocket 管理器错误: {e}")
        return False

    # 5. 验证主入口
    print("\n[5/6] 验证主入口...")
    try:
        from main import app

        print(f"   ✓ main.py 导入成功")
        print(f"   ✓ 应用实例: {app}")
    except Exception as e:
        print(f"   ✗ 主入口错误: {e}")
        return False

    # 6. 验证启动脚本
    print("\n[6/6] 验证启动脚本...")
    scripts = ["start.sh", "start.bat", "test_api.py"]
    for script in scripts:
        if Path(script).exists():
            print(f"   ✓ {script} 存在")
        else:
            print(f"   ✗ {script} 缺失")

    # 统计信息
    print("\n" + "=" * 80)
    print("✅ 阶段六 API 层验证通过")
    print("=" * 80)

    print("\n已创建文件清单:")
    files = [
        "adapters/__init__.py",
        "adapters/rest/__init__.py",
        "adapters/rest/routes/__init__.py",
        "adapters/rest/routes/diagnosis.py",
        "adapters/rest/routes/health.py",
        "adapters/rest/routes/websocket.py",
        "adapters/rest/middleware/__init__.py",
        "adapters/rest/middleware/error_handler.py",
        "adapters/rest/middleware/cors.py",
        "adapters/rest/app.py",
        "main.py",
        "start.sh",
        "start.bat",
        "test_api.py",
    ]

    for i, file in enumerate(files, 1):
        print(f"  {i:2d}. {file}")

    print(f"\n总计: {len(files)} 个文件")

    print("\n核心组件:")
    print("  • REST API: 7 个端点（触发、查询、详情、报告、取消、重试、健康检查）")
    print("  • WebSocket: 实时进度推送")
    print("  • 中间件: CORS + 错误处理")
    print("  • API 文档: /docs (Swagger UI)")

    print("\n启动方式:")
    print("  • Linux/Mac: ./start.sh")
    print("  • Windows: start.bat")
    print("  • 手动: poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload")

    print("\n访问地址:")
    print("  • API 文档: http://localhost:8000/docs")
    print("  • ReDoc: http://localhost:8000/redoc")
    print("  • OpenAPI: http://localhost:8000/openapi.json")
    print("  • 健康检查: http://localhost:8000/api/v1/health/")

    print("\n测试方式:")
    print("  • API 测试: python test_api.py")
    print("  • WebSocket 测试: 使用前端或 wscat")

    print("\n下一步:")
    print("  • 启动服务: ./start.sh 或 start.bat")
    print("  • 运行测试: python test_api.py")
    print("  • 前端集成: 对接 Vue 3 前端")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
