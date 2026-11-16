# 下一步行动计划

**更新日期**：2026-11-16  
**当前状态**：阶段九（前端实现）已完成 96%  
**优先目标**：启动阶段二（领域模型实现）

---

## 🎯 立即行动（1-2 天）

### 1. 前端浏览器验收 ✅

**目标**：确认前端所有交互功能正常

**步骤**：
```bash
cd frontend
npm run dev
# 访问 http://localhost:5173/dashboard
```

**验收清单**：
- [ ] 工作台可展示概览指标（今日诊断数、成功率、平均耗时、进行中）
- [ ] 工作台展示最近诊断表格，可点击查看详情
- [ ] 可触发诊断（打开对话框、选择服务、填写时间窗）
- [ ] 详情页展示会话信息、阶段时间线、根因排行、证据链、报告
- [ ] 进度可实时更新（Mock 模式每 2 秒推进一个阶段）
- [ ] 历史记录页支持筛选（时间、服务、状态）与分页
- [ ] 证据卡片"查看原始数据"按钮可跳转 Grafana（需先配置 VITE_GRAFANA_BASE_URL）
- [ ] 无控制台错误、无白屏、加载/空/错误态正常

**问题记录**：
- 如发现问题，记录在 `frontend/ISSUES.md`，标注优先级

---

## 🚀 短期目标（1-2 周）

### 2. 阅读后端开发路线图 📖

**目标**：理解后端开发全貌与任务分解

**必读文档**：
1. **[后端开发路线图.md](./任务文档/后端开发路线图.md)**（🔥 新创建）
   - 89 个任务详细分解
   - 8-12 周时间线
   - 每周目标与验收标准
2. [架构设计文档.md](./架构设计文档.md) - 第四节"领域模型设计"
3. [诊断Agent设计文档.md](./诊断Agent设计文档.md) - 第二节"核心概念与术语"
4. [AGENTS.md](./AGENTS.md) - 第二节"目录职责与依赖方向"

**关键概念**：
- 聚合根：`DiagnosisSession`（诊断会话）
- 实体：`RootCause`（根因）、`Evidence`（证据）、`Report`（报告）
- 值对象：`TimeRange`、`Confidence`、`ServiceIdentifier`
- 领域服务：`AnomalyDetector`、`EvidenceAggregator`、`RootCauseAnalyzer`

**理解要点**：
- 聚合根的生命周期与不变量
- 实体的唯一性标识
- 值对象的不可变性
- 领域服务的无状态特性

### 3. 创建阶段二任务文档 📝

**目标**：明确领域模型实现的范围与验收标准

**参考模板**：`任务文档/09-前端实现.md`

**任务文档结构**：
```markdown
# 阶段二：领域模型实现

## 一、任务概述
## 二、状态说明
## 三、总体进度
## 四、2.1 聚合根实现
## 五、2.2 实体实现
## 六、2.3 值对象实现
## 七、2.4 领域服务实现
## 八、2.5 领域事件实现
## 九、2.6 仓储接口定义
## 十、2.7 单元测试
## 十一、验收清单
## 十二、变更记录
```

**关键任务**：
- 2.1.1：实现 `DiagnosisSession` 聚合根
- 2.2.1-2.2.3：实现 `RootCause`、`Evidence`、`Report` 实体
- 2.3.1-2.3.3：实现 `TimeRange`、`Confidence`、`ServiceIdentifier` 值对象
- 2.4.1-2.4.3：实现 `AnomalyDetector`、`EvidenceAggregator`、`RootCauseAnalyzer` 领域服务
- 2.5.1：定义领域事件（`DiagnosisTriggered`、`StageCompleted`、`DiagnosisCompleted`）
- 2.6.1：定义 `DiagnosisSessionRepository` 接口
- 2.7.1-2.7.4：编写单元测试（聚合根、实体、值对象、领域服务）

### 4. 实现核心聚合根 💻

**目标**：完成 `DiagnosisSession` 聚合根实现

**文件位置**：`aiops-agent/domain/models/diagnosis_session.py`

**关键方法**：
```python
class DiagnosisSession:
    def __init__(self, diagnosis_id: str, service_name: str, time_range: TimeRange)
    def start(self) -> None
    def advance_stage(self, stage: DiagnosisStage) -> None
    def add_evidence(self, evidence: Evidence) -> None
    def add_root_cause(self, root_cause: RootCause) -> None
    def complete(self, report: Report) -> None
    def fail(self, reason: str) -> None
    def is_terminal(self) -> bool
```

**不变量约束**：
- 诊断一旦开始，不能更改服务名与时间窗
- 阶段只能按顺序推进（采集 → 指标 → 日志 → 链路 → RCA → 报告）
- 完成或失败后不能再添加证据或根因
- 根因按置信度自动排序

**单元测试**：
- 测试聚合根创建
- 测试阶段推进逻辑
- 测试证据添加
- 测试根因排序
- 测试完成与失败状态转换
- 测试不变量约束（负向测试）

**验收标准**：
- ✅ 所有单元测试通过
- ✅ `mypy` 类型检查无错误
- ✅ `black` 与 `isort` 格式化通过
- ✅ 代码覆盖率 > 90%

---

## 📅 中期目标（3-6 周）

### 5. 完成领域模型全部实现（阶段二）

**预计时间**：5-7 天

**里程碑**：
- ✅ 4 个聚合根/实体实现（`DiagnosisSession`、`RootCause`、`Evidence`、`Report`）
- ✅ 3 个值对象实现（`TimeRange`、`Confidence`、`ServiceIdentifier`）
- ✅ 3 个领域服务实现（`AnomalyDetector`、`EvidenceAggregator`、`RootCauseAnalyzer`）
- ✅ 3 个领域事件定义
- ✅ 1 个仓储接口定义
- ✅ 单元测试覆盖率 > 80%

**验收标准**：
- 领域层无任何基础设施依赖（FastAPI、SQLAlchemy、Redis）
- 所有领域逻辑可独立单元测试
- 领域事件定义完整，包含必要字段

### 6. 实现基础设施层（阶段三）

**预计时间**：7-10 天

**关键任务**：
- PostgreSQL ORM 模型（`infrastructure/persistence/models/`）
- 仓储实现（`infrastructure/persistence/repositories/`）
- Redis 缓存客户端（`infrastructure/cache/`）
- Prometheus 客户端（`infrastructure/external/prometheus_client.py`）
- Loki 客户端（`infrastructure/external/loki_client.py`）
- Tempo 客户端（`infrastructure/external/tempo_client.py`）
- 健康检查增强（真实依赖检测）

**环境准备**：
- 使用 Docker Compose 启动 PostgreSQL、Redis
- 配置 `.env` 文件，填写连接串
- 编写数据库迁移脚本（Alembic）

### 7. 实现数据采集与检测器（阶段四）

**预计时间**：7-10 天

**关键任务**：
- Prometheus PromQL 查询封装（JVM、HTTP、连接池指标）
- Loki LogQL 查询封装（ERROR、WARN 日志）
- Tempo TraceQL 查询封装（慢链路、异常链路）
- 异常检测算法实现（阈值检测、3-sigma、环比检测）
- 日志模式匹配（正则表达式、关键词）

**验收标准**：
- 可从 Prometheus 查询到指标数据（返回时间序列）
- 可从 Loki 查询到日志条目
- 可从 Tempo 查询到 Trace 数据
- 异常检测算法可识别已知故障模式

### 8. 实现 Agent 引擎（阶段五）

**预计时间**：10-14 天

**关键任务**：
- Metric Agent（指标异常检测与摘要）
- Log Agent（日志模式识别与关联）
- Trace Agent（链路分析与瓶颈定位）
- RCA Agent（根因推理与置信度计算）
- LangGraph 状态图编排（6 个阶段状态流转）
- LLM 调用封装（OpenAI / Anthropic）

**技术难点**：
- LangGraph 状态图设计（如何传递中间结果）
- LLM Prompt 工程（如何引导准确推理）
- Agent 超时与重试机制
- 中间结果缓存策略

**验收标准**：
- 可执行完整 6 阶段诊断流程（Mock 数据）
- 每个 Agent 输出格式符合预期
- LangGraph 状态转换日志清晰可追溯
- LLM 调用有超时与错误处理

### 9. 实现应用服务与 API（阶段六）

**预计时间**：5-7 天

**关键任务**：
- Use Case：`TriggerDiagnosisUseCase`、`GetDiagnosisDetailUseCase`
- REST API：`POST /api/v1/diagnosis`、`GET /api/v1/diagnosis/{id}` 等
- WebSocket 推送：`/ws/diagnosis/{id}` 进度推送
- DTO 映射器（领域模型 → API 响应）
- 事务边界管理

**联调准备**：
- 确保 API 响应字段与前端 `types/diagnosis.ts` 一致
- WebSocket 事件格式与前端 `api/ws.ts` 一致
- 修改前端 `.env.development` 中 `VITE_USE_MOCK=false`

---

## 🎯 长期目标（7-12 周）

### 10. 完成 P0 阶段剩余任务

- 阶段七：被测应用实现（故障注入、可观测性完善）
- 阶段八：集成测试与调试（端到端测试、性能测试）

### 11. 完成 P1 阶段功能

- 阶段十：告警集成与自动诊断
- 阶段十一：历史记录与报告管理
- 阶段十二：监控与可观测性
- 阶段十三：性能优化

### 12. 完成 P2 阶段生产就绪

- 阶段十四至十九：认证、多租户、高可用、K8s、CI/CD、文档

---

## 📋 任务看板（Kanban）

### To Do（待开始）

- [ ] 阶段二：领域模型实现
- [ ] 阶段三：基础设施层实现
- [ ] 阶段四：数据采集与检测器实现
- [ ] 阶段五：Agent 引擎实现
- [ ] 阶段六：应用服务与 API 实现
- [ ] 阶段七：被测应用实现
- [ ] 阶段八：集成测试与调试

### In Progress（进行中）

- [ ] 前端浏览器验收（阶段九收尾）

### Done（已完成）

- [x] 阶段一：项目初始化与环境准备
- [x] 阶段九：前端实现（96%，Mock 数据演示可用）

---

## 🚨 注意事项

### 依赖关系

**严格按顺序执行**：
1. 阶段二（领域模型）必须完成后才能进行阶段三
2. 阶段五（Agent 引擎）依赖阶段二、三、四
3. 阶段六（应用服务与 API）依赖阶段五
4. 前端真实联调依赖阶段六

**可并行执行**：
- 阶段七（被测应用）可与阶段六并行
- 阶段九（前端浏览器验收）可立即进行

### 外部依赖准备

在启动阶段三前，确保以下依赖可用：

| 依赖 | 准备方式 | 验证命令 |
|------|---------|---------|
| PostgreSQL | `docker-compose up -d postgres` | `psql -h localhost -U aiops` |
| Redis | `docker-compose up -d redis` | `redis-cli ping` |
| Prometheus | 使用外部实例或 `docker-compose up -d prometheus` | `curl http://localhost:9090/-/healthy` |
| Loki | 使用外部实例或 `docker-compose up -d loki` | `curl http://localhost:3100/ready` |
| Tempo | 使用外部实例或 `docker-compose up -d tempo` | `curl http://localhost:3200/ready` |

### 配置管理

所有外部依赖配置更新后，必须同步更新：
- [外部依赖配置清单.md](./外部依赖配置清单.md) - 状态从"预留"改为"已配置"
- `.env.example` - 补充配置项示例值
- `README.md` - 更新快速开始章节

---

## 📞 遇到问题？

### 技术问题

1. **查阅文档**：
   - [AGENTS.md](./AGENTS.md) - 协作规范与禁止事项
   - [架构设计文档.md](./架构设计文档.md) - 架构决策理由
   - [诊断Agent设计文档.md](./诊断Agent设计文档.md) - Agent 详细设计

2. **检查已知问题**：
   - `frontend/ISSUES.md`（如有）
   - `aiops-agent/ISSUES.md`（如有）

3. **创建 Issue**：
   - 标题格式：`[模块] 简短描述`
   - 标签：`bug` / `question` / `enhancement`
   - 内容：复现步骤、预期行为、实际行为、环境信息

### 架构疑问

如果对分层架构、DDD 实践、LangGraph 使用有疑问：
1. 先阅读相关设计文档
2. 查看现有代码示例（阶段一已完成的部分）
3. 提出具体场景的设计问题

---

## 🎉 完成标志

**阶段二完成后**：
- ✅ 领域模型代码实现完整
- ✅ 单元测试覆盖率 > 80%
- ✅ 无基础设施依赖泄漏
- ✅ 更新 `任务文档/02-领域模型实现.md` 状态
- ✅ 更新 `任务文档/项目进度总结.md` 整体进度

**P0 阶段完成后**：
- ✅ 可从 Prometheus/Loki/Tempo 采集真实数据
- ✅ LangGraph Agent 可执行完整诊断流程
- ✅ 前后端真实数据联调通过
- ✅ 端到端集成测试通过
- ✅ 性能指标达标（诊断 < 60s，API < 500ms）

---

**开始时间**：现在  
**预计完成 P0**：3-4 个月后  
**让我们开始吧！** 🚀
