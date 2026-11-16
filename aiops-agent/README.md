# AIOps Diagnosis Agent

智能诊断服务 - 基于 LangGraph 多 Agent 协同诊断

## 🚀 快速开始

### 1. 安装依赖

```bash
# 使用 Poetry 安装
poetry install

# 或使用 pip（在虚拟环境中）
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并修改配置：

```bash
cp .env.example .env
```

关键配置项：
- `PROMETHEUS_URL`: Prometheus 地址（必需）
- `LLM_ENABLED`: 是否启用 LLM（可选，默认 false）
- `LLM_API_KEY`: LLM API 密钥（如果启用 LLM）
- `REDIS_ENABLED`: 是否启用 Redis（可选，默认 false）
- `DATABASE_ENABLED`: 是否启用数据库（可选，默认 false）

### 3. 启动服务

**Linux/Mac:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

**手动启动:**
```bash
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问 API 文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 📚 API 端点

### 健康检查

- `GET /api/v1/health/` - 健康检查
- `GET /api/v1/health/ready` - 就绪检查（含依赖检查）

### 诊断服务

- `POST /api/v1/diagnosis/trigger` - 触发诊断
- `GET /api/v1/diagnosis/sessions` - 查询诊断会话
- `GET /api/v1/diagnosis/sessions/{session_id}` - 获取诊断详情
- `GET /api/v1/diagnosis/sessions/{session_id}/report` - 获取诊断报告
- `POST /api/v1/diagnosis/sessions/{session_id}/cancel` - 取消诊断
- `POST /api/v1/diagnosis/sessions/{session_id}/retry` - 重新诊断

### WebSocket

- `WS /ws/diagnosis/{session_id}` - 实时诊断进度推送

## 🧪 测试

### API 测试

```bash
python test_api.py
```

### 验证安装

```bash
python verify_stage6.py
```

### 单元测试

```bash
poetry run pytest
```

## 📖 使用示例

### 触发诊断

```bash
curl -X POST "http://localhost:8000/api/v1/diagnosis/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "user-service",
    "environment": "prod",
    "time_range_minutes": 60,
    "trigger_source": "manual"
  }'
```

响应：
```json
{
  "session_id": "diag-20250110120000-user-service",
  "status": "triggered",
  "message": "Diagnosis for user-service has been triggered"
}
```

### 查询诊断状态

```bash
curl "http://localhost:8000/api/v1/diagnosis/sessions/diag-20250110120000-user-service"
```

### WebSocket 连接

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/diagnosis/diag-20250110120000-user-service');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Progress:', data);
};

// 发送 ping
ws.send(JSON.stringify({ type: 'ping' }));
```

## 🏗️ 架构

```
aiops-agent/
├── adapters/              # 适配器层（API）
│   └── rest/
│       ├── routes/        # 路由
│       ├── middleware/    # 中间件
│       └── app.py         # FastAPI 应用
├── application/           # 应用层
│   ├── agents/            # Agent 实现
│   ├── services/          # 应用服务
│   ├── use_cases/         # 用例
│   └── dto/               # DTO
├── domain/                # 领域层
│   ├── models/            # 聚合根、实体、值对象
│   ├── services/          # 领域服务
│   └── repositories/      # 仓储接口
├── infrastructure/        # 基础设施层
│   ├── external/          # 外部服务客户端
│   ├── persistence/       # 持久化
│   ├── cache/             # 缓存
│   ├── messaging/         # 消息队列
│   ├── llm/               # LLM 客户端
│   └── monitoring/        # 监控
├── config/                # 配置
├── main.py                # 主入口
└── tests/                 # 测试

```

## 🔧 配置说明

### 外部依赖

| 依赖 | 默认状态 | 说明 |
|---|---|---|
| Prometheus | 启用 | 指标数据源（必需） |
| Redis | 禁用 | 缓存和分布式锁（可选） |
| PostgreSQL | 禁用 | 持久化存储（可选） |
| Loki | 禁用 | 日志数据源（可选） |
| Tempo | 禁用 | 链路数据源（可选） |
| Kafka | 禁用 | 事件发布（可选） |
| LLM | 禁用 | AI 分析（可选） |

### 降级策略

- 外部依赖未启用或不可用时，服务不会崩溃
- LLM 禁用时，返回占位响应
- 数据库禁用时，跳过持久化
- 缓存禁用时，直接查询数据源

## 🐛 故障排查

### 服务启动失败

1. 检查依赖是否安装：`poetry install`
2. 检查配置文件：`.env`
3. 检查端口占用：`lsof -i :8000` (Linux/Mac)

### API 调用失败

1. 检查服务是否启动：访问 http://localhost:8000/api/v1/health/
2. 检查日志输出
3. 检查外部依赖状态：访问 http://localhost:8000/api/v1/health/ready

### LLM 相关错误

1. 确认 `LLM_ENABLED=true`
2. 确认 `LLM_API_KEY` 已设置
3. 确认 `LLM_BASE_URL` 正确（如使用 Ollama）
4. 检查网络连接

## 📝 开发

### 添加新的 API 端点

1. 在 `adapters/rest/routes/` 创建路由文件
2. 在 `adapters/rest/app.py` 注册路由
3. 更新 API 文档

### 添加新的 Agent

1. 在 `application/agents/` 创建 Agent 文件
2. 在 `application/agents/prompts.py` 添加提示词
3. 在 `application/agents/diagnosis_graph.py` 注册节点
4. 更新容器依赖注入

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

---

**版本**: 0.1.0  
**最后更新**: 2025-01-10
