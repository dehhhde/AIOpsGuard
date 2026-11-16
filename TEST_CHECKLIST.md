# AIOpsGuard 测试模式验证清单

## 当前状态

✅ 后端代码开发完成（90%，80/89 任务）
✅ 测试模式实现完成
✅ Mock 数据生成器完成
✅ 集成测试脚本完成
✅ 配置文件就绪（.env）

## 测试前准备

由于自动执行遇到问题，请按以下步骤手动验证：

### 1. 确认文件存在

```powershell
cd d:\code\AIOpsGuard\aiops-agent

# 检查关键文件
ls .env                                          # 配置文件
ls test_integration.py                            # 集成测试
ls quick_test.py                                  # 快速验证
ls infrastructure\external\mock_data.py           # Mock 数据
ls RUN_TEST.md                                    # 详细测试指南
```

### 2. 验证配置

```powershell
# 查看 .env 内容
Get-Content .env | Select-String "TEST_MODE"
# 应输出：TEST_MODE=true
```

### 3. 检查 Python 环境

```powershell
python --version
# 应输出：Python 3.11+ 或 Python 3.14（本机）
```

## 快速验证（3 步）

### 第 1 步：语法检查

```powershell
cd d:\code\AIOpsGuard\aiops-agent
python quick_test.py
```

**预期**：所有模块显示 ✓

**如果失败**：
- 运行 `pip install fastapi uvicorn pydantic httpx structlog`
- 或运行 `poetry install`（如果已安装 Poetry）

---

### 第 2 步：启动服务

```powershell
cd d:\code\AIOpsGuard\aiops-agent
python -m uvicorn main:app --reload --port 8000
```

**预期**：
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**保持此窗口运行，不要关闭！**

---

### 第 3 步：运行测试（新开终端）

```powershell
cd d:\code\AIOpsGuard\aiops-agent
python test_integration.py
```

**预期**：显示 `✓ 集成测试通过！`

## 验收标准

| 检查项 | 状态 | 说明 |
|-------|------|------|
| [ ] `.env` 文件存在 | | `TEST_MODE=true` |
| [ ] 语法检查通过 | | `python quick_test.py` 无错误 |
| [ ] 服务启动成功 | | 端口 8000 监听 |
| [ ] 健康检查通过 | | `GET /health/` 返回 200 |
| [ ] 诊断触发成功 | | 返回 session_id |
| [ ] 诊断完成 | | 状态变为 `completed` |
| [ ] 报告包含根因 | | 3 个根因，置信度 >70% |

## 详细测试指南

完整步骤、API 示例、故障排查请见：[RUN_TEST.md](aiops-agent/RUN_TEST.md)

## 下一步

测试通过后：

1. **部署外部依赖**
   - Prometheus（指标）
   - Loki（日志）
   - Tempo（链路）
   - LLM API（诊断）

2. **切换到生产模式**
   - 修改 `.env`：`TEST_MODE=false`
   - 配置真实连接地址
   - 重启服务
   - 重新测试

3. **继续开发**
   - 阶段七：容器化部署
   - 阶段八：完善集成测试
   - 前端开发（44/46 任务）

## 关键文件说明

| 文件 | 作用 |
|------|------|
| `aiops-agent/.env` | 测试模式配置（TEST_MODE=true） |
| `aiops-agent/quick_test.py` | 快速语法检查 |
| `aiops-agent/test_integration.py` | 完整集成测试 |
| `aiops-agent/RUN_TEST.md` | 详细测试指南 |
| `aiops-agent/TEST_MODE.md` | 测试模式说明 |
| `aiops-agent/infrastructure/external/mock_data.py` | Mock 数据生成器 |
| `AGENTS.md` | 开发规范（必读） |
| `后端开发路线图.md` | 任务清单 |

## 常见问题

### Q1: 模块导入失败？
**A**: 运行 `pip install fastapi uvicorn pydantic httpx structlog langgraph langchain openai`

### Q2: 端口被占用？
**A**: 更换端口 `python -m uvicorn main:app --port 8001`

### Q3: 诊断一直处于 analyzing？
**A**: 检查服务端日志，确认 `TEST_MODE=true`

### Q4: 需要安装 Poetry 吗？
**A**: 不是必须的，可以用 `pip` 安装依赖

### Q5: 测试数据是什么？
**A**: 模拟故障场景（CPU 95%、内存泄漏、SQL 超时等），详见 TEST_MODE.md

---

**准备好了吗？开始第 1 步！** 👆
