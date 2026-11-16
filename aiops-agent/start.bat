@echo off
REM 启动 AIOps Diagnosis Agent (Windows)

echo Starting AIOps Diagnosis Agent...

REM 检查虚拟环境
if not exist ".venv" (
    echo Virtual environment not found. Please run 'poetry install' first.
    exit /b 1
)

REM 启动服务
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
