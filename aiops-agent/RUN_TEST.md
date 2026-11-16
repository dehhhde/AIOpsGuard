# 测试模式快速启动指南

## 前提条件

由于 PowerShell 执行会话存在问题，请手动按以下步骤操作。

## 步骤一：安装依赖（首次运行）

```powershell
# 方案 A：使用 Poetry（推荐）
cd d:\code\AIOpsGuard\aiops-agent
poetry install

# 方案 B：使用 pip
cd d:\code\AIOpsGuard\aiops-agent
pip install -r requirements.txt

# 如果没有 requirements.txt，可以从 pyproject.toml 生成：
# poetry export -f requirements.txt --output requirements.txt --without-hashes
```

## 步骤二：验证语法

```powershell
cd d:\code\AIOpsGuard\aiops-agent
python quick_test.py
```

**预期输出**：
```
================================================================================
快速语法检查
================================================================================

✓ config.settings
✓ infrastructure.external.mock_data
✓ application.agents.tools
✓ infrastructure.llm.llm_client
✓ domain.models.diagnosis_session

================================================================================
✓ 所有模块导入成功！

下一步：
1. 确保 .env 文件中设置了 TEST_MODE=true
2. 启动服务: python -m uvicorn main:app --reload --port 8000
3. 运行集成测试: python test_integration.py
```

## 步骤三：启动服务（测试模式）

```powershell
cd d:\code\AIOpsGuard\aiops-agent

# 使用 Poetry
poetry run uvicorn main:app --reload --port 8000

# 或直接使用 Python
python -m uvicorn main:app --reload --port 8000
```

**预期日志**：
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

保持此窗口运行。

## 步骤四：运行集成测试（新开终端）

```powershell
cd d:\code\AIOpsGuard\aiops-agent

# 使用 Poetry
poetry run python test_integration.py

# 或直接使用 Python
python test_integration.py
```

**预期输出**：
```
================================================================================
AIOpsGuard 集成测试（测试模式）
================================================================================

[1/6] 健康检查...
   ✓ 状态码: 200
   ✓ 响应: {'status': 'healthy', ...}

[2/6] 就绪检查...
   ✓ 状态码: 200
   ✓ 状态: ready

[3/6] 触发诊断...
   ✓ 状态码: 200
   ✓ 诊断会话 ID: diag_xxxxx

[4/6] 等待诊断完成（最多 60 秒）...
   ✓ 诊断完成，状态: completed

[5/6] 获取诊断报告...
   ✓ 状态码: 200
   ✓ 根因数量: 3

[6/6] 验证 Mock 数据...
   ✓ 找到根因：数据库连接池耗尽
   ✓ 找到根因：内存泄漏导致频繁 Full GC

================================================================================
✓ 集成测试通过！
================================================================================
```

## 步骤五：手动 API 测试（可选）

### 健康检查
```powershell
curl http://localhost:8000/api/v1/health/
```

### 触发诊断
```powershell
$body = @{
    service_name = "test-service"
    time_range = @{
        start = "2024-01-20T10:00:00Z"
        end = "2024-01-20T11:00:00Z"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/diagnosis/trigger" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

### 查询诊断状态
```powershell
# 替换 <session_id> 为上一步返回的 ID
curl http://localhost:8000/api/v1/diagnosis/<session_id>/status
```

### 获取诊断报告
```powershell
# 等待 10-20 秒后查询
curl http://localhost:8000/api/v1/diagnosis/<session_id>/report
```

## 故障排查

### 问题 1：ModuleNotFoundError

**原因**：依赖未安装

**解决**：
```powershell
cd d:\code\AIOpsGuard\aiops-agent
poetry install
# 或
pip install fastapi uvicorn pydantic httpx structlog langgraph langchain openai
```

### 问题 2：端口 8000 被占用

**解决**：更换端口
```powershell
python -m uvicorn main:app --reload --port 8001
# 然后在 test_integration.py 中将 base_url 改为 http://localhost:8001
```

### 问题 3：TEST_MODE 未生效

**检查**：
```powershell
# 确认 .env 文件存在
Get-Content .env | Select-String "TEST_MODE"

# 应输出：TEST_MODE=true
```

### 问题 4：诊断卡在 analyzing 状态

**原因**：LangGraph 执行失败

**调试**：
1. 查看服务端日志（uvicorn 窗口）
2. 检查 `infrastructure/llm/llm_client.py` 的 `_generate_mock_response()` 是否正常
3. 确认 `TEST_MODE=true` 已设置

## 切换到生产模式

**时机**：外部依赖（Prometheus/Loki/Tempo/LLM）部署完成后

**步骤**：

1. 修改 `.env`：
```
TEST_MODE=false

# 配置真实地址
PROMETHEUS_ENABLED=true
PROMETHEUS_URL=http://your-prometheus:9090

LOKI_ENABLED=true
LOKI_URL=http://your-loki:3100

TEMPO_ENABLED=true
TEMPO_URL=http://your-tempo:3200

LLM_ENABLED=true
LLM_API_KEY=sk-your-real-key
LLM_BASE_URL=https://api.openai.com/v1
```

2. 重启服务

3. 重新运行集成测试（此时会查询真实数据）

## 测试数据说明

测试模式下会模拟以下故障场景：

- **性能异常**：CPU 95%、内存泄漏（1.0GB→1.6GB）、延迟 2.5s、错误率 15%
- **日志异常**：10x OutOfMemoryError、5x SQL 超时、8x GC 告警
- **链路异常**：数据库查询 3.2s、支付服务超时 30s
- **根因分析**：3 个根因，置信度 92%/85%/75%

详细信息见 [TEST_MODE.md](TEST_MODE.md)。

## 验收标准

测试模式下，以下接口应正常工作：

- ✅ `GET /api/v1/health/` → 200
- ✅ `GET /api/v1/health/ready` → 200
- ✅ `POST /api/v1/diagnosis/trigger` → 200，返回 session_id
- ✅ `GET /api/v1/diagnosis/{id}/status` → 200，状态最终变为 `completed`
- ✅ `GET /api/v1/diagnosis/{id}/report` → 200，返回包含 3 个根因的报告

如果以上全部通过，说明测试模式配置成功！
