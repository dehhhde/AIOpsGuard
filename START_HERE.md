# 🚀 AIOpsGuard 测试模式 - 快速开始

> **状态**: 后端开发完成 90%，测试模式已就绪，等待验证

## ⚡ 30 秒快速开始

```powershell
# 1. 进入项目目录
cd d:\code\AIOpsGuard\aiops-agent

# 2. 运行快速测试脚本
.\test_quick.bat
```

脚本会自动完成：
- ✅ 检查配置（TEST_MODE=true）
- ✅ 验证语法（导入关键模块）
- ✅ 启动服务（端口 8000）

然后**新开一个终端**运行：
```powershell
cd d:\code\AIOpsGuard\aiops-agent
python test_integration.py
```

**预期**: 显示 `✓ 集成测试通过！`

---

## 📋 如果自动脚本失败

### 方案 A：逐步手动验证

#### 步骤 1：检查配置
```powershell
cd d:\code\AIOpsGuard\aiops-agent
Get-Content .env | Select-String "TEST_MODE"
# 应输出：TEST_MODE=true
```

#### 步骤 2：验证语法
```powershell
python quick_test.py
# 应显示 5 个 ✓
```

如果报错 `ModuleNotFoundError`：
```powershell
pip install fastapi uvicorn pydantic httpx structlog langgraph langchain openai
```

#### 步骤 3：启动服务
```powershell
python -m uvicorn main:app --reload --port 8000
# 保持运行
```

#### 步骤 4：运行测试（新终端）
```powershell
cd d:\code\AIOpsGuard\aiops-agent
python test_integration.py
```

---

### 方案 B：手动 API 测试

如果 Python 脚本有问题，可以用 PowerShell 手动测试：

```powershell
# 1. 健康检查
curl http://localhost:8000/api/v1/health/

# 2. 触发诊断
$body = @{
    service_name = "test-service"
    time_range = @{
        start = "2024-01-20T10:00:00Z"
        end = "2024-01-20T11:00:00Z"
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/diagnosis/trigger" -Method Post -ContentType "application/json" -Body $body
$sessionId = $response.diagnosis_id
Write-Host "诊断会话 ID: $sessionId"

# 3. 等待 10 秒
Start-Sleep -Seconds 10

# 4. 查询报告
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/diagnosis/$sessionId/report" | ConvertTo-Json -Depth 10
```

**预期**: 返回包含 3 个根因的 JSON

---

## 📚 详细文档

| 文档 | 用途 |
|------|------|
| **[TEST_CHECKLIST.md](TEST_CHECKLIST.md)** | 验收清单（推荐阅读） |
| **[RUN_TEST.md](aiops-agent/RUN_TEST.md)** | 完整测试指南 |
| **[测试模式实施总结.md](测试模式实施总结.md)** | 技术实现细节 |
| **[TEST_MODE.md](aiops-agent/TEST_MODE.md)** | 测试模式说明 |

---

## ✅ 验收标准

运行 `test_integration.py` 后应看到：

```
================================================================================
AIOpsGuard 集成测试（测试模式）
================================================================================

[1/6] 健康检查...
   ✓ 状态码: 200

[2/6] 就绪检查...
   ✓ 状态码: 200

[3/6] 触发诊断...
   ✓ 诊断会话 ID: diag_xxxxx

[4/6] 等待诊断完成...
   ✓ 诊断完成，状态: completed

[5/6] 获取诊断报告...
   ✓ 根因数量: 3

[6/6] 验证 Mock 数据...
   ✓ 找到根因：数据库连接池耗尽
   ✓ 找到根因：内存泄漏导致频繁 Full GC

================================================================================
✓ 集成测试通过！
================================================================================
```

---

## 🔄 下一步

### 测试通过后

1. **部署外部依赖**（可选，生产环境需要）
   - Prometheus（指标采集）
   - Loki（日志聚合）
   - Tempo（链路追踪）
   - LLM API（智能诊断）

2. **切换到生产模式**
   ```powershell
   # 修改 aiops-agent\.env
   TEST_MODE=false
   
   PROMETHEUS_URL=http://your-prometheus:9090
   LOKI_URL=http://your-loki:3100
   TEMPO_URL=http://your-tempo:3200
   LLM_API_KEY=sk-your-real-key
   ```

3. **继续开发**
   - 阶段七：Docker 容器化
   - 阶段八：完善测试
   - 前端开发（44/46 任务已完成）

---

## ❓ 常见问题

### Q1: 模块导入失败？
```powershell
pip install fastapi uvicorn pydantic httpx structlog langgraph langchain openai
```

### Q2: 端口 8000 被占用？
```powershell
# 换个端口
python -m uvicorn main:app --port 8001

# 然后修改 test_integration.py 第 15 行：
# base_url = "http://localhost:8001"
```

### Q3: 诊断一直是 analyzing 状态？
- 检查服务端日志（uvicorn 窗口）
- 确认 `.env` 中 `TEST_MODE=true`
- 查看是否有 Python 异常

### Q4: 需要安装 Poetry 吗？
不需要，用 `pip` 即可。

### Q5: 测试数据从哪来？
`infrastructure/external/mock_data.py` 自动生成模拟故障数据。

---

## 🎯 当前进度

```
后端开发: ████████████████████░ 90% (80/89 任务)

✅ 阶段一：项目初始化 (11/11)
✅ 阶段二：领域模型 (15/15)
✅ 阶段三：基础设施层 (18/18)
✅ 阶段四：应用层 (11/11)
✅ 阶段五：Agent 引擎 (16/16)
✅ 阶段六：API 层 (9/9)
✅ 测试模式：Mock 数据 + 集成测试
⏳ 阶段七：部署配置 (0/4)
⏳ 阶段八：集成测试 (0/5)
```

---

## 💡 提示

- 测试模式下**无需**真实的 Prometheus/Loki/Tempo/LLM
- Mock 数据模拟了完整的故障场景（CPU 飙升、内存泄漏、SQL 超时等）
- 切换到生产模式只需修改 `.env`，无需改代码

---

**准备好了吗？运行 `.\test_quick.bat` 开始吧！** 🚀
