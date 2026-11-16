# AIOpsGuard - 智能运维诊断平台

<div align="center">

**AI 驱动的自动化故障诊断与根因分析系统**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/vue-3.5%2B-green)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.104%2B-teal)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/langgraph-0.2%2B-purple)](https://github.com/langchain-ai/langgraph)

</div>

---

## 📖 项目简介

AIOpsGuard 是一个企业级 AIOps 智能诊断平台，通过多源数据融合（指标、日志、链路）与 AI Agent 协作，实现从告警到根因定位的全自动化诊断流程。

### 核心特性

- 🤖 **AI Agent 协作**：基于 LangGraph 的多 Agent 编排，自动化推理与决策
- 📊 **多源数据融合**：综合 Prometheus 指标、Loki 日志、Tempo 链路数据
- 🎯 **智能根因分析**：利用 LLM 进行关联分析与根因定位
- 🔍 **实时进度追踪**：WebSocket 推送诊断进度，可视化阶段状态
- 📈 **可视化报告**：Markdown 格式诊断报告，支持证据链追溯
- 🏗️ **企业级架构**：六边形架构 + DDD，清晰的领域边界与分层

### 技术亮点

- 采用**领域驱动设计（DDD）**，核心业务逻辑与基础设施解耦
- 基于 **LangGraph** 实现复杂 Agent 状态流转与决策编排
- **六边形架构**保证高可测试性与可扩展性
- 完整的**可观测性**体系，诊断平台本身也可被监控
- **TypeScript 全栈类型安全**，前后端接口契约清晰

---

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    前端（Vue 3 + TypeScript）                 │
│          工作台 | 诊断详情 | 历史记录 | 配置管理               │
└─────────────────────────────────────────────────────────────┘
                           ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│              诊断 Agent（FastAPI + LangGraph）               │
├─────────────────────────────────────────────────────────────┤
│  adapters/      → REST API、WebSocket、事件监听              │
│  application/   → Use Cases、Agent 编排、DTO 映射            │
│  domain/        → 聚合根、实体、值对象、领域服务【核心逻辑】    │
│  infrastructure/→ 仓储实现、缓存、消息队列、外部 API          │
└─────────────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────┴──────────────────┐
        │                                     │
┌───────▼──────┐  ┌──────────┐  ┌───────▼────┐
│ Prometheus   │  │   Loki   │  │   Tempo    │
│ (指标存储)    │  │(日志存储) │  │(链路存储)   │
└──────┬───────┘  └────┬─────┘  └─────┬──────┘
       │               │               │
       └───────────────┴───────────────┘
                       ↓
              ┌────────────────┐
              │  Target App    │
              │(被测 Spring Boot)│
              └────────────────┘
```

---

## 🚀 快速开始

> **重要提示**：后端已实现测试模式，无需外部依赖即可运行完整诊断流程！

### 前置要求

| 工具 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 后端运行（必需） |
| Node.js | 18+ | 前端开发（可选） |
| Java | 21 | 被测应用（可选） |
| Docker | 24.x | 生产部署（可选） |

### 方案 A：测试模式（推荐）⚡

**无需 Prometheus/Loki/Tempo/LLM，使用 Mock 数据快速验证**

#### 1️⃣ 快速启动（30 秒）

```powershell
cd d:\code\AIOpsGuard\aiops-agent
.\test_quick.bat
```

脚本会自动：
- ✅ 检查配置（`TEST_MODE=true`）
- ✅ 验证语法
- ✅ 启动服务（http://localhost:8000）

#### 2️⃣ 运行集成测试（新终端）

```powershell
cd d:\code\AIOpsGuard\aiops-agent
python test_integration.py
```

**预期输出**：
```
✓ 集成测试通过！
- 健康检查通过
- 诊断触发成功
- 3 个根因已生成（数据库连接池耗尽、内存泄漏、第三方服务降级）
```

#### 📚 详细指南
- 完整步骤：[START_HERE.md](START_HERE.md)
- 验收清单：[TEST_CHECKLIST.md](TEST_CHECKLIST.md)
- 技术细节：[测试模式实施总结.md](测试模式实施总结.md)

---

### 方案 B：生产模式（需外部依赖）

#### 1️⃣ 部署外部依赖

```bash
# 启动 Prometheus + Loki + Tempo
docker-compose -f infrastructure/docker-compose.yml up -d
```

#### 2️⃣ 配置后端

```bash
cd aiops-agent
pip install fastapi uvicorn pydantic httpx structlog langgraph langchain openai

# 配置环境变量
cp .env.example .env
# 编辑 .env，设置：
# - TEST_MODE=false
# - PROMETHEUS_URL=http://localhost:9090
# - LOKI_URL=http://localhost:3100
# - TEMPO_URL=http://localhost:3200
# - LLM_API_KEY=sk-your-key
```

#### 3️⃣ 启动服务

```bash
python -m uvicorn main:app --reload --port 8000
```

访问 http://localhost:8000/docs（Swagger UI）

#### 4️⃣ 启动被测应用（可选）

```bash
cd target-app
mvn spring-boot:run
```

#### 5️⃣ 启动前端（可选）

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

---

## 📂 项目结构

```
AIOpsGuard/
├── aiops-agent/          # 诊断 Agent 后端
│   ├── domain/           # 领域层（聚合根、实体、领域服务）
│   ├── application/      # 应用服务层（Use Cases、Agent 编排）
│   ├── infrastructure/   # 基础设施层（仓储、缓存、外部 API）
│   ├── adapters/         # 适配器层（REST、WebSocket、事件监听）
│   ├── config/           # 配置管理
│   └── shared/           # 共享内核（DTO、异常、工具）
├── frontend/             # Vue 3 前端
│   ├── src/
│   │   ├── views/        # 页面视图
│   │   ├── components/   # 可复用组件
│   │   ├── api/          # API 客户端
│   │   ├── stores/       # Pinia 状态管理
│   │   ├── mock/         # Mock 数据服务
│   │   └── utils/        # 工具函数
│   └── dist/             # 构建产物
├── target-app/           # 被测 Spring Boot 应用
│   ├── src/main/java/    # Java 源码
│   └── src/main/resources/ # 配置文件
├── infrastructure/       # 基础设施配置
│   ├── docker-compose.yml
│   ├── prometheus/
│   ├── grafana/
│   └── loki/
├── 任务文档/              # 分阶段实施文档
│   ├── 00-总览与规划.md
│   ├── 01-项目初始化与环境准备.md
│   ├── 09-前端实现.md
│   └── 项目进度总结.md
├── 架构设计文档.md        # 整体架构设计
├── 诊断Agent设计文档.md   # Agent 详细设计
├── 监控数据分类说明.md    # 数据流向规则
├── 外部依赖配置清单.md    # 依赖管理
├── AGENTS.md             # AI Agent 协作规范
└── README.md             # 本文档
```

---

## 🎯 功能特性

### 已完成功能 ✅

#### 前端（阶段九）

- ✅ **工作台**：概览指标、最近诊断、进行中任务、触发诊断对话框
- ✅ **诊断详情页**：阶段时间线、根因排行榜、证据链卡片、指标图表、诊断报告
- ✅ **历史记录页**：筛选条件（时间、服务、状态）、分页表格、导出功能
- ✅ **配置页**：数据源展示、功能开关状态
- ✅ **实时进度**：WebSocket Mock 推送，每 2 秒推进一个阶段
- ✅ **Grafana 深链**：证据卡片可跳转 Grafana 对应时间窗与面板
- ✅ **Mock 数据服务**：完整诊断案例 + 进行中案例

#### 后端（阶段一）

- ✅ **工程骨架**：FastAPI 应用、分层目录结构、配置管理
- ✅ **健康检查**：`GET /health` 接口（基础版）
- ✅ **配置预留**：PostgreSQL、Redis、Kafka、Prometheus、Loki、Tempo、LLM

### 待实现功能 ⏸️

#### 核心功能（P0）

- ⏸️ **领域模型**（阶段二）：聚合根、实体、值对象、领域服务
- ⏸️ **基础设施层**（阶段三）：数据库仓储、缓存、外部 API 客户端
- ⏸️ **数据采集**（阶段四）：Prometheus/Loki/Tempo 查询封装、异常检测
- ⏸️ **Agent 引擎**（阶段五）：Metric/Log/Trace/RCA Agent、LangGraph 编排
- ⏸️ **应用服务与 API**（阶段六）：Use Cases、REST API、WebSocket 推送
- ⏸️ **被测应用**（阶段七）：故障注入接口、可观测性完善
- ⏸️ **集成测试**（阶段八）：端到端测试、性能测试

#### 增强功能（P1）

- ⏸️ **告警集成**（阶段十）：Alertmanager Webhook、自动触发
- ⏸️ **历史记录管理**（阶段十一）：高级查询、报告导出
- ⏸️ **监控与可观测性**（阶段十二）：Agent 自身监控、告警
- ⏸️ **性能优化**（阶段十三）：缓存策略、并发优化

#### 生产就绪（P2）

- ⏸️ **认证与权限**（阶段十四）：JWT、RBAC
- ⏸️ **多租户支持**（阶段十五）：租户隔离、配额管理
- ⏸️ **高可用与灾备**（阶段十六）：多副本、故障切换
- ⏸️ **Kubernetes 部署**（阶段十七）：Helm Charts、自动扩缩容
- ⏸️ **CI/CD 流水线**（阶段十八）：GitHub Actions
- ⏸️ **文档与运维手册**（阶段十九）：API 文档、运维手册

---

## 📊 当前进度

### 后端开发（90% 完成）

```
后端开发: ████████████████████░ 90% (80/89 任务)

✅ 阶段一：项目初始化 (11/11) - 包骨架、配置、健康检查
✅ 阶段二：领域模型 (15/15) - 聚合根、实体、值对象、领域服务
✅ 阶段三：基础设施层 (18/18) - 仓储、缓存、外部 API 客户端
✅ 阶段四：应用层 (11/11) - DTO、Use Cases、依赖注入
✅ 阶段五：Agent 引擎 (16/16) - 4 个 Agent、LangGraph 编排
✅ 阶段六：API 层 (9/9) - REST API、WebSocket、CORS
✅ 测试模式：Mock 数据生成器 + 集成测试脚本
⏳ 阶段七：部署配置 (0/4) - Docker、K8s
⏳ 阶段八：集成测试 (0/5) - 端到端测试
```

### 前端开发（96% 完成）

```
前端开发: ███████████████████▓ 96% (44/46 任务)

✅ 工作台、诊断详情、历史记录、配置页
✅ WebSocket Mock、Grafana 深链
⏸️ 2 项阻塞于后端 REST + WebSocket API（现已解除）
```

### 测试模式状态

| 组件 | 测试模式 | 生产模式 |
|------|---------|---------|
| **Prometheus** | ✅ Mock 数据（CPU 95%、内存泄漏） | ⏳ 需部署 |
| **Loki** | ✅ Mock 日志（OOM、SQL 超时） | ⏳ 需部署 |
| **Tempo** | ✅ Mock 链路（慢查询 3.2s） | ⏳ 需部署 |
| **LLM** | ✅ Mock 根因分析（3 个根因） | ⏳ 需 API Key |
| **数据库** | ⚪ 禁用（内存存储） | ⏳ 需部署 PostgreSQL |
| **Redis** | ⚪ 禁用 | ⏳ 需部署 Redis |
| **Kafka** | ⚪ 禁用 | ⏳ 需部署 Kafka |

**当前可用**：测试模式下，完整诊断流程可运行，无需任何外部依赖！

---

## 🚧 下一步计划

### 短期（1-2 周）

1. ✅ **验证测试模式**：运行集成测试，确保 Mock 数据流程正常
2. ⏳ **部署外部依赖**：Prometheus、Loki、Tempo、LLM
3. ⏳ **切换生产模式**：修改配置，连接真实服务
4. ⏳ **端到端测试**：使用真实数据验证诊断准确性

### 中期（2-4 周）

5. ⏳ **阶段七：部署配置** - Docker Compose、Kubernetes
6. ⏳ **阶段八：完善测试** - 单元测试、集成测试、性能测试
7. ⏳ **前端对接后端** - 替换 Mock 数据为真实 API
8. ⏳ **被测应用完善** - 故障注入场景扩充

### 长期（1-2 月）

9. ⏳ **告警集成** - Alertmanager Webhook 自动触发
10. ⏳ **认证授权** - JWT、RBAC
11. ⏳ **多租户支持** - 租户隔离、配额管理
12. ⏳ **生产部署** - 高可用、监控告警、CI/CD

---

## 🛠️ 开发指南

### 代码规范

#### Python（后端）

- ✅ 全量类型注解，`mypy` 严格模式
- ✅ I/O 操作使用 `async def`
- ✅ 配置通过 `settings` 读取，禁止直接读环境变量
- ✅ 日志使用 `structlog`，禁止 `print`
- ✅ 代码格式化：`black` + `isort`

#### TypeScript（前端）

- ✅ 全量类型注解，`strict` 模式
- ✅ 组件使用 `<script setup lang="ts">`
- ✅ 代码格式化：`prettier` + `eslint`
- ✅ 命名：组件 PascalCase，工具函数 camelCase

#### Java（被测应用）

- ✅ 构造器注入，禁止字段注入
- ✅ 配置写入 `application.yml`
- ✅ Lombok `@RequiredArgsConstructor`

### 分层架构约束

```
adapters  →  application  →  domain
                 ↑
          infrastructure（实现 domain 接口）
shared 被所有层引用
```

**严格规则**：
- ❌ `domain/` 禁止依赖 FastAPI、SQLAlchemy、Redis、Kafka
- ✅ `domain/` 只能依赖标准库与 `shared/`
- ✅ `infrastructure/` 实现 `domain/repositories` 接口
- ✅ `adapters/` 只做协议转换，不写业务逻辑

详见 [AGENTS.md](./AGENTS.md)

### 常用命令

```bash
# 后端
cd aiops-agent
poetry install           # 安装依赖
uvicorn main:app --reload  # 启动开发服务器
pytest                   # 运行测试
black .; isort .         # 代码格式化
py -m compileall -q .    # 语法检查

# 前端
cd frontend
npm install              # 安装依赖
npm run dev              # 启动开发服务器
npm run build            # 生产构建
npm run lint             # 代码检查
npm run test             # 运行测试

# 被测应用
cd target-app
mvn spring-boot:run      # 启动应用
mvn test                 # 运行测试
```

---

## 📖 文档导航

### 架构设计

- [架构设计文档](./架构设计文档.md)：整体架构、分层设计、领域模型
- [诊断Agent设计文档](./诊断Agent设计文档.md)：Agent 职责、LangGraph 状态流转
- [前端与Grafana数据展示划分](./前端与Grafana数据展示划分.md)：展示边界与职责
- [监控数据分类说明](./监控数据分类说明.md)：Push/Pull 决策规则

### 实施指南

- [00-总览与规划](./任务文档/00-总览与规划.md)：路线图、技术栈、学习目标
- [01-项目初始化与环境准备](./任务文档/01-项目初始化与环境准备.md)：环境搭建、工程创建
- [后端开发路线图](./任务文档/后端开发路线图.md)：8-12 周后端任务分解、89 个任务清单
- [09-前端实现](./任务文档/09-前端实现.md)：前端任务清单、验收标准
- [项目进度总结](./任务文档/项目进度总结.md)：整体进度、里程碑、风险

### 协作规范

- [AGENTS.md](./AGENTS.md)：AI Agent 与开发者协作约束、禁止事项
- [外部依赖配置清单](./外部依赖配置清单.md)：依赖状态、配置位置、启用步骤

---

## 🧪 测试

### 单元测试

```bash
# 后端
cd aiops-agent
pytest tests/ -v --cov=.

# 前端
cd frontend
npm run test
```

### 集成测试

⏸️ 待阶段八实现

### 性能测试

⏸️ 待阶段八实现

---

## 🤝 贡献指南

### 开发流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 代码审查标准

- ✅ 通过所有单元测试
- ✅ 代码格式化通过（black/prettier）
- ✅ 无 ESLint/mypy 错误
- ✅ 更新相关文档
- ✅ 遵循分层架构约束

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

本项目使用了以下优秀的开源项目：

- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Python Web 框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - AI Agent 编排框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Element Plus](https://element-plus.org/) - Vue 3 UI 组件库
- [ECharts](https://echarts.apache.org/) - 强大的图表库
- [Prometheus](https://prometheus.io/) - 监控与告警系统
- [Grafana](https://grafana.com/) - 可观测性平台

---

## 📞 联系方式

- **项目主页**：https://github.com/your-org/AIOpsGuard
- **问题反馈**：https://github.com/your-org/AIOpsGuard/issues
- **文档**：https://aiopsguard.readthedocs.io（待建设）

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个 Star！**

Made with ❤️ by AIOpsGuard Team

</div>
