#!/bin/bash

# 启动 AIOps Diagnosis Agent

echo "Starting AIOps Diagnosis Agent..."

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Please run 'poetry install' first."
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 启动服务
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
