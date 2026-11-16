# AGENTS.md

本文件约束 AI Agent 与开发者在本仓库（AIOpsGuard）中的工作方式。修改代码前先阅读本文件和相关设计文档。

---

## 1. 项目认知

| 模块 | 目录 | 技术栈 | 角色 |
|---|---|---|---|
| 被测应用 | `target-app/` | Java 21、Spring Boot 3.2、Micrometer、OpenTelemetry | 故障注入与可观测数据生产方 |
| 诊断服务 | `aiops-agent/` | Python 3.11+、FastAPI、LangGraph、SQLAlchemy、Redis | 多 Agent 诊断与报告服务 |
| 实施任务 | `任务文档/` | Markdown | 阶段一至阶段的实施指南与验收标准 |
| 设计文档 | 根目录 `*.md` | Markdown | 架构、被测应用、诊断 Agent、监控数据分类 |

关键文档：

- [架构设计文档](架构设计文档.md)：分层、领域模型、设计模式、部署
- [诊断 Agent 设计文档](诊断Agent设计文档.md)：Agent 职责、LangGraph 状态流转、API
- [监控数据分类说明](监控数据分类说明.md)：Push / Pull / 内部流转的判定规则
- [外部依赖配置清单](外部依赖配置清单.md)：每个外部依赖的配置位置与状态

当前进度：阶段一已完成（`aiops-agent` 包骨架、配置、健康检查），领域模型尚未实现。

---

## 2. 目录职责与依赖方向

### 2.1 依赖方向（强制）

```
adapters  →  application  →  domain
                  ↑
           infrastructure（实现 domain 的接口）
shared 被所有层引用，但不得包含业务逻辑
```

| 规则 | 说明 |
|---|---|
| `domain/` 只能依赖标准库与 `shared/` | 禁止 import fastapi、sqlalchemy、httpx、redis |
| `application/` 可依赖 `domain/` | 负责用例编排、事务边界、DTO 映射 |
| `infrastructure/` 实现 `domain/repositories` 中的接口 | 不得反向依赖 `adapters/` |
| `adapters/` 只做协议转换 | 不写业务规则，不直接访问数据库 |
| `config/` 只提供配置对象 | 不在此处初始化长连接或执行业务 |

### 2.2 新代码放置位置

| 要写的内容 | 放置位置 |
|---|---|
| 聚合根、实体、值对象 | `aiops-agent/domain/models/` |
| 领域服务（检测、聚合、推理） | `aiops-agent/domain/services/` |
| 仓储接口 | `aiops-agent/domain/repositories/` |
| 领域事件 | `aiops-agent/domain/events/` |
| 用例（触发诊断、查询报告） | `aiops-agent/application/use_cases/` |
| Metric / Log / Trace / RCA Agent、LangGraph 图 | `aiops-agent/application/agents/` |
| DTO 与映射器 | `aiops-agent/application/dto/`、`application/mappers/` |
| Prometheus / Loki / Tempo / LLM 客户端 | `aiops-agent/infrastructure/external/` |
| ORM 模型与仓储实现 | `aiops-agent/infrastructure/persistence/` |
| Redis、Kafka、监控埋点 | `aiops-agent/infrastructure/cache|messaging|monitoring/` |
| REST 路由、WebSocket | `aiops-agent/adapters/rest/` |
| 配置项 | `aiops-agent/config/settings.py` |

---

## 3. 常用命令

```powershell
# 诊断 Agent
cd aiops-agent
poetry install                      # 依赖尚未安装
uvicorn main:app --reload --port 8000
pytest
black .; isort .
py -m compileall -q .               # 快速语法校验

# 被测应用
cd target-app
mvn spring-boot:run
mvn test
```

注意：本机通过 `py` 启动的是 Python 3.14，项目要求 3.11+，可运行；但依赖版本以 `pyproject.toml` 为准。

---

## 4. 编码规范

### 4.1 Python（aiops-agent）

- 全量类型注解，`disallow_untyped_defs = true`
- I/O 一律使用 `async def`，禁止在协程内调用阻塞库
- 配置只能通过 `config.settings.settings` 读取，禁止直接读 `os.environ`
- 日志使用 `structlog`，禁止 `print`
- 行长 100，格式化用 black + isort，导入顺序按 isort 配置
- 注释与 docstring 使用中文，标识符使用英文
- 异常定义在 `domain/exceptions/`，路由层统一转换，不吞异常

### 4.2 Java（target-app）

- 构造器注入（配合 Lombok `@RequiredArgsConstructor`），禁止字段注入
- 配置写入 `application.yml`，禁止硬编码地址与端口
- 新增指标通过 `MeterRegistry` 注册，禁止自造暴露端点
- 故障注入开关统一放在 `problem.switches` 下，默认 `false`

### 4.3 命名

| 对象 | 规范 | 示例 |
|---|---|---|
| Prometheus 指标 | `域.对象.状态` | `problem.memory_leak.triggered` |
| Kafka Topic | `类别.子类` | `events.problems`、`metrics.jvm` |
| 事件类型 | 大写下划线 | `PROBLEM_TRIGGERED`、`ERROR` |
| 诊断状态 | 小写 | `pending`、`analyzing`、`completed` |

---

## 5. 可观测数据规则

1. **先判断 Push 还是 Pull**，依据 [监控数据分类说明](监控数据分类说明.md) 第 7 节决策表。
2. 已有 Micrometer 指标的数据，不得再通过 Kafka 重复上传。
3. 新增指标、事件、Topic 必须同步登记到 `监控数据分类说明.md`。
4. 事件报文必须包含：`serviceName`、`eventType`、`severity`、`timestamp`、`title`，以及可选的 `context`。
5. 禁止把 `trace_id`、`user_id`、`request_id` 作为指标标签。
6. 诊断报告、根因、证据链存 PostgreSQL，禁止写入 Prometheus / Loki。

---

## 6. 外部依赖管理（重点）

### 6.1 状态定义

| 状态 | 含义 |
|---|---|
| 预留 | 已确定选型，配置字段与文件位置已留空，功能默认关闭 |
| 部分配置 | 代码或配置已存在一部分，尚未联通 |
| 已配置 | 可启动、可联通、有验收方式 |

### 6.2 新增外部依赖的标准步骤

必须按以下顺序完成，缺一不可：

1. **声明依赖**：Python 写入 `aiops-agent/pyproject.toml`；Java 写入 `target-app/pom.xml`
2. **预留配置**：在 `aiops-agent/config/settings.py` 增加字段，默认值可为 `None` 或本地默认值；同步在 `.env.example` 增加空值/占位键
3. **预留部署配置**：在根目录 `docker-compose.yml`、`infrastructure/` 下添加注释块或占位，不默认启用
4. **登记清单**：在 [外部依赖配置清单](外部依赖配置清单.md) 中新增一行，状态写“预留”，补齐启用步骤
5. **功能降级**：未配置时功能默认关闭，不得导致应用启动失败
6. **禁止提交密钥**：`.env` 已被 gitignore，真实密钥不得进入仓库

### 6.3 客户端实现约定

| 约束 | 要求 |
|---|---|
| 初始化时机 | 延迟到首次使用或应用启动钩子，不在 import 阶段建连 |
| 超时 | 必须显式设置连接超时与读取超时 |
| 重试 | 使用 `tenacity`，有上限与退避，禁止无限重试 |
| 健康检查 | 每个外部依赖提供 `health()` 或 `ping()`，接入 `/health` |
| 连接池 | 大小从 `settings` 读取，禁止写死 |
| 降级 | 依赖不可用时返回明确错误或跳过该 Agent，而不是抛未捕获异常 |

### 6.4 尚未实现的外部依赖

Kafka、PostgreSQL、Redis、Loki、Tempo、LLM、Grafana 均处于“预留”状态，配置字段已存在但未联通。实现前先更新配置清单状态，不要直接写死连接信息。

---

## 7. 变更与验证

| 场景 | 必做验证 |
|---|---|
| 新增 Python 模块 | `py -m compileall -q aiops-agent` |
| 修改领域逻辑 | `pytest`，补充或更新单测 |
| 修改 Java 代码 | `mvn -f target-app/pom.xml test` |
| 新增外部依赖 | 更新 `外部依赖配置清单.md` 与 `.env.example` |
| 新增指标/事件 | 更新 `监控数据分类说明.md` |
| 修改接口 | 更新 `诊断Agent设计文档.md` 的接口章节 |

---

## 8. 未来演进方向（预留设计位）

| 方向 | 可能引入的依赖 | 预留点 |
|---|---|---|
| 多 Agent 编排增强 | LangGraph 新版本、checkpointer | `application/agents/`、Redis 状态存储 |
| 故障知识库 / RAG | pgvector、嵌入模型 | `domain/services/`、PostgreSQL 扩展 |
| 多租户 | 租户上下文、行级隔离 | `shared/kernel/`、ORM 模型字段 |
| 容器化部署 | Docker、K8s、Helm | 根目录 `docker-compose.yml`、`infrastructure/` |
| 可观测性完善 | OTel Collector、exporter | `infrastructure/monitoring/` |
| 前端 | Vue 3、Vite、ECharts | 新建 `frontend/` |
| 认证授权 | JWT、OIDC、RBAC | `config/settings.py` 已有 JWT 字段 |
| 报告导出 | MinIO / S3 | `infrastructure/external/` |
| CI/CD | GitHub Actions | `.github/workflows/` |

---

## 9. 禁止事项

- 禁止在 `domain/` 引入 Web、ORM、HTTP、消息队列依赖
- 禁止绕过 `settings` 直接读取环境变量或写死连接串
- 禁止提交 `.env`、密钥、证书
- 禁止重复上报已由 Prometheus 暴露的指标
- 禁止在未更新配置清单的情况下启用新的外部依赖
- 禁止为了通过测试而删除或弱化已有断言
- 禁止在未阅读设计文档的情况下重构分层结构
