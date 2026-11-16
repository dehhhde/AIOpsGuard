# 前端与 Grafana 数据展示划分

## 1. 文档目的

明确 AIOpsGuard 中哪些数据由**自研前端（Vue 3）**展示、哪些由 **Grafana** 展示，避免重复建设、重复查询和数据口径不一致。

适用对象：前端开发、后端开发、运维、测试。

---

## 2. 核心原则

1. **原始时序与检索用 Grafana，诊断业务与结论用自研前端。**
2. **前端不直接连接 Prometheus、Loki、Tempo**，统一经 `aiops-agent` 后端封装查询。
3. **通用可视化不重复造轮子**，Grafana 已具备的能力（变量、时间对齐、告警、导出）不自行实现。
4. **诊断结论必须自研**，根因、置信度、证据链、报告等业务对象无法用通用 Dashboard 表达。
5. **同一数据只设一个主展示位**，另一端仅做摘要或深链跳转。

---

## 3. 数据归属总表

| 数据 | 自研前端（Vue） | Grafana | 说明 |
|---|---|---|---|
| 诊断会话列表、状态、进度 | 主 | — | 实时进度走 WebSocket |
| 根因排序、置信度 | 主 | — | 业务结论，Grafana 无法表达 |
| 证据链（指标/日志/链路证据） | 主 | — | 前端展示摘要和时间窗，附跳转链接 |
| 诊断报告、修复建议、导出 | 主 | — | 结构化文档，存 PostgreSQL |
| 历史记录、筛选、对比 | 主 | — | REST 分页查询 |
| 手动触发诊断、参数选择 | 主 | — | 表单与表单校验 |
| Agent 配置（数据源、LLM、开关） | 主 | — | 配置类页面 |
| JVM 堆内存、GC、线程、CPU 曲线 | 次（摘要图） | 主 | 原始时序看 Grafana |
| HTTP QPS、P50/P90/P99、错误率 | 次（摘要图） | 主 | 支持按 uri 维度下钻 |
| HikariCP 连接池曲线 | 次 | 主 | 排障时看原始曲线 |
| 主机 CPU/内存/磁盘/网络 | — | 主 | 与诊断无直接关联时不进前端 |
| 容器资源指标 | — | 主 | cAdvisor 数据 |
| Kafka lag、PG、Redis 指标 | — | 主 | 属于基础设施健康 |
| 日志全文检索（LogQL） | — | 主 | Loki Explore |
| Trace 检索与调用链（TraceQL） | 次（单条链路卡片） | 主 | 前端只展示诊断命中的链路 |
| 告警规则、通知渠道 | — | 主 | Alertmanager + Grafana Alerting |
| 长期容量趋势 | — | 主 | 时间跨度大，前端不适合 |
| Agent 自身运行指标（诊断耗时、失败率、LLM 成本） | — | 主 | 运维视角 |
| 业务指标（成功率、转化率） | 视需求 | 主 | 先做 Grafana 面板 |
| 端到端拨测结果 | 次 | 主 | 可用性总览 |

图例：**主** = 主要展示位置；**次** = 仅展示摘要或入口；**—** = 不展示。

---

## 4. 自研前端页面规划

| 页面 | 路由 | 数据来源 | 核心内容 |
|---|---|---|---|
| 诊断工作台 | `/dashboard` | `GET /api/v1/diagnosis`、WebSocket | 进行中诊断、最近结果、快捷触发 |
| 诊断详情 | `/diagnosis/:id` | `GET /api/v1/diagnosis/{id}`、`/report` | 进度、各 Agent 输出、根因排序、证据链 |
| 历史记录 | `/history` | `GET /api/v1/diagnosis/history` | 时间范围筛选、服务筛选、报告导出 |
| 配置页 | `/settings` | Agent 配置接口 | 数据源地址、LLM provider、阈值开关 |

展示要求：

- 证据卡片必须包含：证据类型、来源（指标名 / 日志查询 / Trace ID）、时间窗、原文摘要、置信度影响。
- 每张证据卡片提供“查看原始数据”深链，跳到 Grafana 对应 Dashboard 并携带时间范围与服务变量。
- 前端图表数据由后端裁剪（降采样到 100~300 点），禁止透传 Prometheus 原始响应。
- 实时进度用 WebSocket，断线重连后用 REST 补拉最新状态。

---

## 5. Grafana Dashboard 规划

| Dashboard | 数据源 | 核心面板 | 主要使用人 |
|---|---|---|---|
| JVM | Prometheus | 堆/非堆内存、GC 次数与停顿、线程数、类加载 | 后端开发 |
| HTTP | Prometheus | QPS、P50/P99、5xx 比例、Top 慢接口 | 后端开发、测试 |
| 连接池 | Prometheus | active/idle/pending/max、等待时长 | 后端开发 |
| Host & Container | Prometheus | CPU、内存、磁盘、网络、容器工作集 | 运维 |
| Middleware | Prometheus | Kafka lag、PG 连接与慢查询、Redis 内存与命中率 | 运维 |
| Logs & Traces | Loki + Tempo | 错误日志趋势、慢链路 Top N、日志检索 | 全体 |
| AIOps Agent | Prometheus | 诊断任务数、耗时、失败率、LLM 调用与 Token | 运维、算法 |

命名建议：`{领域} - {服务} - {视角}`，例如 `AIOps - target-app - JVM`。

---

## 6. 两端衔接方式

| 方式 | 做法 | 注意事项 |
|---|---|---|
| 深链跳转 | 前端生成 Grafana URL，携带 `var-service`、`from`、`to`、`var-instance` | URL 参数名必须与 Dashboard 变量一致 |
| iframe 嵌入 | Grafana `kiosk` 模式只读面板 | 仅用于辅助展示，避免两套路由与权限冲突 |
| 报告留档 | 后端生成图片快照或前端导出 PNG，随报告存 PostgreSQL | 避免 Grafana 数据过期后报告失真 |
| 统一查询 | 前端 → Agent API → Prometheus/Loki/Tempo | Agent 负责鉴权、缓存、超时、重试、降采样 |

---

## 7. 边界情况处理

| 场景 | 处理方式 |
|---|---|
| Grafana 无法访问 | 前端证据卡片保留文字摘要与指标数值，不阻塞诊断查看 |
| 时间范围不一致 | 前端与 Grafana 使用同一时间窗，跳转时显式传入 `from`/`to` |
| 指标已过期 | 报告中保存快照，原始曲线跳转后由 Grafana 提示无数据 |
| 高基数查询 | 由 Agent 后端聚合，禁止前端拼接 PromQL |
| 权限差异 | 前端走 Agent 鉴权；Grafana 独立账号体系，按需只读账号 |
| 告警展示 | 前端只展示与当前诊断相关的告警摘要，完整规则在 Grafana / Alertmanager |

---

## 8. 实施顺序

| 阶段 | 动作 | 验收标准 |
|---|---|---|
| 1 | 落地 Grafana 数据源与 JVM/HTTP/连接池 Dashboard | 三个面板有数据、可切换时间窗 |
| 2 | 补齐 Host、Middleware、Logs & Traces Dashboard | 主机/容器/中间件指标可见 |
| 3 | Agent 提供诊断查询 API 与 WebSocket | `/diagnosis/{id}` 可返回进度与结果 |
| 4 | 前端实现工作台与详情页 | 可触发诊断、查看根因与证据链 |
| 5 | 打通前端到 Grafana 的深链 | 证据卡片可跳转到对应时间窗 |
| 6 | 报告导出与快照留档 | 历史报告脱离 Grafana 仍可阅读 |

---

## 9. 一句话总结

**“发生了什么、为什么”看前端；“资源用得怎么样、曲线长什么样”看 Grafana。**

---

## 10. 关联文档

- [AGENTS.md](AGENTS.md)：分层与编码约束
- [监控数据分类说明.md](监控数据分类说明.md)：Push / Pull 判定与指标清单
- [外部依赖配置清单.md](外部依赖配置清单.md)：Grafana、Prometheus 等配置状态
- [诊断Agent设计文档.md](诊断Agent设计文档.md)：诊断接口与状态流转
