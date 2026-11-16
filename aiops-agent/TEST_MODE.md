# 测试模式说明

## 📋 概述

测试模式允许在**没有外部依赖**的情况下运行和测试 AIOpsGuard 后端服务。

所有外部数据源（Prometheus、Loki、Tempo）和 LLM 都会使用预设的 Mock 数据，模拟真实的诊断场景。

---

## 🚀 快速开始

### 1. 启用测试模式

编辑 `.env` 文件，设置：

```bash
TEST_MODE=true
```

或者复制测试配置：

```bash
cp .env.example .env
# .env.example 中 TEST_MODE 默认为 true
```

### 2. 启动服务

```bash
./start.sh  # Linux/Mac
# 或
start.bat   # Windows
```

### 3. 运行集成测试

```bash
python test_integration.py
```

---

## 🎭 Mock 数据说明

### 模拟场景

测试模式会生成一个典型的故障场景，包含以下异常：

#### 1. 指标异常（Prometheus Mock 数据）

| 指标 | 正常值 | 异常值 | 时间点 | 说明 |
|---|---|---|---|---|
| **CPU 使用率** | 75% | 95% | 30-40 分钟 | CPU 突增 |
| **内存使用量** | 1.0GB | 1.6GB | 持续增长 | 疑似内存泄漏 |
| **请求延迟 P99** | 150ms | 2.5s | 30-45 分钟 | 延迟飙升 |
| **错误率** | 0.5% | 15% | 35 分钟后 | 错误率突增 |

#### 2. 日志异常（Loki Mock 数据）

| 日志级别 | 错误类型 | 出现次数 | 说明 |
|---|---|---|---|
| ERROR | OutOfMemoryError: Java heap space | 10 次 | JVM 堆内存不足 |
| ERROR | SQLException: Connection timeout | 5 次 | 数据库连接超时 |
| WARN | GC overhead limit exceeded | 8 次 | GC 频繁 |

#### 3. 链路异常（Tempo Mock 数据）

| Trace ID | 总耗时 | 慢 Span | 说明 |
|---|---|---|---|
| trace-001-slow-request | 3.5s | SELECT * FROM users (3.2s) | 数据库查询慢 |
| trace-002-timeout | 30.5s | payment-service.charge (30s) | 支付服务超时 |

#### 4. 根因分析（LLM Mock 数据）

| 根因 | 置信度 | 推理依据 |
|---|---|---|
| **JVM 堆内存不足** | 92% | 内存持续增长 + OutOfMemoryError + GC 告警 |
| **数据库性能问题** | 85% | 查询耗时 3.2s + 连接超时错误 |
| **支付服务不稳定** | 75% | 支付服务调用超时 30s |

---

## 🔄 工作原理

### 架构图

```
┌─────────────────────────────────────────────────┐
│              API 请求（触发诊断）                 │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│           应用层（检测 TEST_MODE）                │
└─────────────────────────────────────────────────┘
                      ↓
        TEST_MODE = true ? ───┐
                ↓             ↓
              YES            NO
                ↓             ↓
        ┌──────────┐   ┌──────────┐
        │ Mock 数据 │   │ 真实服务 │
        └──────────┘   └──────────┘
                ↓             ↓
        ┌──────────────────────────┐
        │    Agent 引擎分析         │
        └──────────────────────────┘
                      ↓
        ┌──────────────────────────┐
        │    生成诊断报告           │
        └──────────────────────────┘
```

### 代码实现

#### 1. Agent 工具集（tools.py）

```python
async def query_metrics(...):
    # 检测测试模式
    if settings.test_mode:
        mock_data = self.mock_generator.generate_prometheus_metrics(...)
        return json.dumps(mock_data)
    
    # 正常模式：查询 Prometheus
    ...
```

#### 2. LLM 客户端（llm_client.py）

```python
async def chat(...):
    # 检测测试模式
    if app_settings.test_mode:
        return self._generate_mock_response(messages)
    
    # 正常模式：调用 OpenAI API
    ...
```

#### 3. Mock 数据生成器（mock_data.py）

```python
class MockDataGenerator:
    @staticmethod
    def generate_prometheus_metrics(...):
        """生成模拟指标数据"""
        
    @staticmethod
    def generate_loki_logs(...):
        """生成模拟日志数据"""
        
    @staticmethod
    def generate_tempo_traces(...):
        """生成模拟链路数据"""
        
    @staticmethod
    def generate_llm_*_analysis(...):
        """生成模拟 LLM 分析结果"""
```

---

## 📊 测试流程

### 完整测试步骤

```bash
# 1. 启动服务（测试模式）
./start.sh

# 2. 运行集成测试
python test_integration.py
```

### 测试输出示例

```
================================================================================
AIOpsGuard 集成测试（测试模式）
================================================================================

[1/6] 健康检查...
   ✓ 状态码: 200
   ✓ 响应: {'status': 'healthy', 'service': 'AIOps Diagnosis Agent', ...}

[2/6] 就绪检查...
   ✓ 状态码: 200
   ✓ 状态: ready
   ✓ 检查项: []

[3/6] 触发诊断...
   ✓ 状态码: 202
   ✓ 诊断已触发
   ✓ 会话 ID: diag-20250110120000-test-service
   ✓ 状态: triggered
   ✓ 消息: Diagnosis for test-service has been triggered

[4/6] 等待诊断完成...
   诊断流程: Metric Agent → Log Agent → Trace Agent → RCA Agent
   进度: 25% | 状态: analyzing | 阶段: COLLECT
   进度: 50% | 状态: analyzing | 阶段: RCA
   进度: 100% | 状态: completed | 阶段: REPORT_GENERATION
   ✓ 诊断完成！

[5/6] 获取诊断会话详情...
   ✓ 会话 ID: diag-20250110120000-test-service
   ✓ 服务名称: test-service
   ✓ 状态: completed
   ✓ 进度: 100%

[6/6] 获取诊断报告...
   ✓ 报告获取成功

   【诊断摘要】
   诊断完成，发现 3 个根因

   【证据清单】
   共收集 9 条证据：
   1. [METRIC] CPU 使用率异常突增至 95%
   2. [METRIC] 内存持续增长，疑似内存泄漏
   3. [METRIC] P99 延迟飙升至 2.5 秒
   4. [LOG] 频繁出现 OutOfMemoryError，JVM 堆内存不足
   5. [LOG] 数据库连接超时，5 次连接失败
   ... 还有 4 条证据

   【根因分析】
   共发现 3 个根因：
   1. JVM 堆内存不足导致频繁 Full GC 和 OutOfMemoryError
      置信度: 92%
   2. 数据库查询性能问题导致请求延迟和连接池耗尽
      置信度: 85%
   3. 支付服务不稳定导致订单创建失败
      置信度: 75%

   ✓ 完整报告已生成

================================================================================
✅ 集成测试完成
================================================================================
```

---

## 🔀 切换到生产模式

### 1. 部署外部依赖

部署以下服务：

- ✅ **Prometheus**（必需）
- ⚪ **Loki**（可选）
- ⚪ **Tempo**（可选）
- ⚪ **LLM API**（可选，OpenAI / Ollama）
- ⚪ **PostgreSQL**（可选）
- ⚪ **Redis**（可选）

### 2. 修改配置

编辑 `.env` 文件：

```bash
# 关闭测试模式
TEST_MODE=false

# 配置外部服务地址
PROMETHEUS_ENABLED=true
PROMETHEUS_URL=http://prometheus:9090

# 如果启用 LLM
LLM_ENABLED=true
LLM_API_KEY=sk-your-openai-api-key
LLM_MODEL=gpt-4

# 其他可选依赖...
```

### 3. 重启服务

```bash
./start.sh
```

### 4. 重新测试

```bash
python test_integration.py
```

此时服务会使用真实的外部依赖进行诊断。

---

## 🧪 API 测试

### 使用 curl

```bash
# 触发诊断
curl -X POST "http://localhost:8000/api/v1/diagnosis/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "test-service",
    "environment": "prod",
    "time_range_minutes": 60,
    "trigger_source": "manual"
  }'

# 查询诊断状态
curl "http://localhost:8000/api/v1/diagnosis/sessions/diag-20250110120000-test-service"

# 获取诊断报告
curl "http://localhost:8000/api/v1/diagnosis/sessions/diag-20250110120000-test-service/report"
```

### 使用 Swagger UI

访问 http://localhost:8000/docs

---

## 📝 注意事项

### 优点

✅ **无需外部依赖**：可以在任何环境快速启动和测试  
✅ **可重复测试**：每次返回一致的 Mock 数据  
✅ **快速验证**：无需等待真实服务响应  
✅ **开发友好**：本地开发无需搭建完整环境

### 限制

⚠️ **Mock 数据固定**：无法测试真实的异常检测逻辑  
⚠️ **LLM 分析固定**：无法测试真实的 AI 推理能力  
⚠️ **性能不真实**：Mock 数据返回速度快，不反映真实性能

### 建议

1. **开发阶段**：使用测试模式快速迭代
2. **集成测试**：使用测试模式验证流程完整性
3. **功能验证**：部署外部依赖后使用生产模式
4. **性能测试**：必须使用生产模式和真实数据

---

## 🐛 故障排查

### 问题：服务启动失败

**检查**：
1. 端口 8000 是否被占用
2. Python 版本是否 >= 3.11
3. 依赖是否已安装（`poetry install`）

### 问题：测试模式不生效

**检查**：
1. `.env` 文件中 `TEST_MODE=true`
2. 重启服务使配置生效
3. 查看日志是否有 `test_mode_mock_*` 字样

### 问题：诊断一直不完成

**检查**：
1. 查看服务日志
2. 检查是否有错误抛出
3. 重新触发诊断

---

## 📚 相关文档

- `README.md` - 项目快速开始
- `test_integration.py` - 集成测试脚本
- `test_api.py` - API 测试脚本
- `infrastructure/external/mock_data.py` - Mock 数据生成器

---

**最后更新**：2025-01-10  
**维护者**：Kiro AI
