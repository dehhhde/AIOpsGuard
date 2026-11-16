@echo off
chcp 65001 >nul
echo ================================================================================
echo AIOpsGuard 快速测试脚本
echo ================================================================================
echo.

echo [1/3] 检查配置...
if not exist .env (
    echo    × .env 文件不存在
    echo    提示: 应该已自动创建，请检查 aiops-agent 目录
    pause
    exit /b 1
)
findstr /C:"TEST_MODE=true" .env >nul
if errorlevel 1 (
    echo    × TEST_MODE 未设置为 true
    pause
    exit /b 1
)
echo    √ TEST_MODE=true

echo.
echo [2/3] 语法检查...
python quick_test.py
if errorlevel 1 (
    echo.
    echo    × 语法检查失败，请先安装依赖：
    echo      pip install fastapi uvicorn pydantic httpx structlog langgraph langchain openai
    pause
    exit /b 1
)

echo.
echo [3/3] 准备启动服务...
echo.
echo ================================================================================
echo 下一步操作：
echo ================================================================================
echo.
echo 1. 启动服务（保持运行）：
echo    python -m uvicorn main:app --reload --port 8000
echo.
echo 2. 新开终端运行测试：
echo    cd d:\code\AIOpsGuard\aiops-agent
echo    python test_integration.py
echo.
echo 按任意键启动服务...
pause >nul

python -m uvicorn main:app --reload --port 8000
