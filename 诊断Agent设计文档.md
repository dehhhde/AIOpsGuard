# 诊断 Agent（AIOps Agent）详细设计文档

## 1. 项目概述

### 1.1 项目定位
诊断 Agent 是一个基于多 Agent 协作的智能运维诊断平台，通过采集被测应用的指标、日志、链路数据，自动检测异常、定位根因并输出诊断报告。

### 1.2 核心能力
- **自动感知**: 实时采集 Prometheus、Loki、Tempo 的可观测数据
- **异常检测**: 基于规则和 AI 识别指标/日志/链路异常
- **多 Agent 协作**: Metric/Log/Trace/RCA Agent 分工协作
- **根因分析**: 综合多源证据，输出根因排序和置信度
- **报告生成**: 结构化诊断报告，包含证据链和修复建议

### 1.3 技术栈
- **框架**: FastAPI 0.104+ / Python 3.11+
- **AI 编排**: LangGraph 0.2+ / LangChain 0.1+
- **大模型**: 通义千问 Qwen / DeepSeek / OpenAI
- **数据源**: Prometheus + Loki + Tempo
- **消息队列**: Kafka 3.x（kafka-python / aiokafka）
- **数据库**: PostgreSQL 15+（存储诊断报告）/ SQLAlchemy 2.0
- **缓存**: Redis 7.0（redis-py / aioredis）
- **异步框架**: asyncio / uvicorn
- **数据处理**: pandas / numpy / scikit-learn
- **前端**: Vue 3 + TypeScript + Element Plus + ECharts

---

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Dashboard│  │ Diagnosis│  │  History │  │  Config  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │         API Layer (REST Routers)                    │    │
│  │  /diagnosis/trigger  /diagnosis/{id}  /history      │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Orchestrator Agent (LangGraph)              │    │
│  │   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐        │    │
│  │   │Metric│-->│ Log  │-->│Trace │-->│ RCA  │        │    │
│  │   │Agent │   │Agent │   │Agent │   │Agent │        │    │
│  │   └──────┘   └──────┘   └──────┘   └──────┘        │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Data Collector Layer                        │    │
│  │   PromQL    LogQL     TraceQL      Kafka            │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Storage Layer                               │    │
│  │      PostgreSQL (Reports)    Redis (Cache)          │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
   Prometheus          Loki              Tempo
        ↑                 ↑                 ↑
        └─────────────────┴─────────────────┘
                   Target App
```

### 2.2 模块划分

```
aiops-agent/
├── app/
│   ├── main.py                   # FastAPI 应用入口
│   ├── config.py                 # 配置管理
│   └── dependencies.py           # 依赖注入
│
├── api/                          # API 层
│   ├── __init__.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── diagnosis.py          # 诊断相关接口
│   │   ├── history.py            # 历史记录接口
│   │   └── config.py             # 配置接口
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── diagnosis.py          # 请求/响应模型
│   │   ├── report.py             # 报告模型
│   │   └── common.py             # 通用模型
│   └── websocket/
│       ├── __init__.py
│       └── diagnosis_ws.py       # WebSocket 处理
│
├── engine/                       # Agent 引擎
│   ├── __init__.py
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── diagnosis_orchestrator.py
│   │   └── agent_graph.py        # LangGraph 定义
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py         # Agent 基类
│   │   ├── metric_agent.py
│   │   ├── log_agent.py
│   │   ├── trace_agent.py
│   │   └── rca_agent.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── prometheus_tool.py
│   │   ├── loki_tool.py
│   │   └── tempo_tool.py
│   └── state/
│       ├── __init__.py
│       └── diagnosis_state.py    # 状态定义
│
├── collector/                    # 数据采集
│   ├── __init__.py
│   ├── prometheus/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── query_builder.py
│   ├── loki/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── query_builder.py
│   └── tempo/
│       ├── __init__.py
│       ├── client.py
│       └── query_builder.py
│
├── detector/                     # 异常检测
│   ├── __init__.py
│   ├── metric/
│   │   ├── __init__.py
│   │   ├── baseline_detector.py
│   │   ├── threshold_detector.py
│   │   └── anomaly_detector.py
│   ├── log/
│   │   ├── __init__.py
│   │   ├── pattern_detector.py
│   │   └── error_detector.py
│   └── trace/
│       ├── __init__.py
│       ├── slow_trace_detector.py
│       └── error_trace_detector.py
│
├── analyzer/                     # 智能分析
│   ├── __init__.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── llm_service.py
│   │   ├── prompt_template.py
│   │   ├── qwen_client.py
│   │   └── deepseek_client.py
│   ├── rca/
│   │   ├── __init__.py
│   │   ├── root_cause_analyzer.py
│   │   └── evidence_aggregator.py
│   └── recommender/
│       ├── __init__.py
│       └── fix_recommender.py
│
├── storage/                      # 数据存储
│   ├── __init__.py
│   ├── database.py               # SQLAlchemy 配置
│   ├── models/
│   │   ├── __init__.py
│   │   ├── diagnosis_report.py
│   │   ├── diagnosis_history.py
│   │   └── alert.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── diagnosis_repository.py
│   │   └── alert_repository.py
│   └── cache/
│       ├── __init__.py
│       └── redis_service.py
│
├── alert/                        # 告警处理
│   ├── __init__.py
│   ├── listener/
│   │   ├── __init__.py
│   │   └── prometheus_alert_listener.py
│   ├── processor/
│   │   ├── __init__.py
│   │   └── alert_processor.py
│   └── trigger/
│       ├── __init__.py
│       └── diagnosis_trigger.py
│
├── common/                       # 公共模块
│   ├── __init__.py
│   ├── constants.py              # 常量定义
│   ├── enums.py                  # 枚举类型
│   ├── exceptions.py             # 自定义异常
│   └── utils/
│       ├── __init__.py
│       ├── time_util.py
│       └── json_util.py
│
├── tests/                        # 测试
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── conftest.py
│
├── requirements.txt              # 依赖列表
├── pyproject.toml                # 项目配置
├── Dockerfile
└── docker-compose.yml
```

---

## 3. 核心流程设计

### 3.1 诊断触发流程

```mermaid
sequenceDiagram
    participant User as 用户/告警系统
    participant API as API Layer
    participant Orchestrator as Orchestrator Agent
    participant MA as Metric Agent
    participant LA as Log Agent
    participant TA as Trace Agent
    participant RCA as RCA Agent
    participant DB as MySQL

    User->>API: POST /diagnosis/trigger
    API->>Orchestrator: 启动诊断流程
    
    par 并行采集数据
        Orchestrator->>MA: 分析指标
        MA->>Prometheus: 查询时序数据
        Prometheus-->>MA: 返回指标
        
        Orchestrator->>LA: 分析日志
        LA->>Loki: 查询日志
        Loki-->>LA: 返回日志
        
        Orchestrator->>TA: 分析链路
        TA->>Tempo: 查询链路
        Tempo-->>TA: 返回链路
    end
    
    MA-->>Orchestrator: 指标分析结果
    LA-->>Orchestrator: 日志分析结果
    TA-->>Orchestrator: 链路分析结果
    
    Orchestrator->>RCA: 综合分析
    RCA->>LLM: 根因推理
    LLM-->>RCA: 根因结论
    RCA-->>Orchestrator: 诊断报告
    
    Orchestrator->>DB: 持久化报告
    Orchestrator-->>API: 返回诊断结果
    API-->>User: 返回诊断报告
```

### 3.2 LangGraph 状态流转

```python
from typing import TypedDict, List, Optional
from datetime import datetime
from enum import Enum

class DiagnosisStatus(str, Enum):
    INIT = "init"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"

class DiagnosisState(TypedDict):
    """诊断状态"""
    diagnosis_id: str
    target_service: str
    start_time: datetime
    end_time: datetime
    
    # 数据采集结果
    metric_anomalies: List[dict]
    log_anomalies: List[dict]
    trace_anomalies: List[dict]
    
    # 分析结果
    root_causes: List[dict]
    evidences: List[dict]
    confidence: float
    
    # 诊断报告
    report: Optional[dict]
    
    # 状态标记
    status: DiagnosisStatus
```

**LangGraph 节点定义**:

```python
from langgraph.graph import StateGraph, END
from engine.agents import MetricAgent, LogAgent, TraceAgent, RCAAgent

class AgentGraph:
    """Agent 编排图"""
    
    def __init__(
        self,
        metric_agent: MetricAgent,
        log_agent: LogAgent,
        trace_agent: TraceAgent,
        rca_agent: RCAAgent
    ):
        self.metric_agent = metric_agent
        self.log_agent = log_agent
        self.trace_agent = trace_agent
        self.rca_agent = rca_agent
    
    def build_graph(self) -> StateGraph:
        """构建状态图"""
        workflow = StateGraph(DiagnosisState)
        
        # 添加节点
        workflow.add_node("metric_analysis", self.metric_agent.analyze)
        workflow.add_node("log_analysis", self.log_agent.analyze)
        workflow.add_node("trace_analysis", self.trace_agent.analyze)
        workflow.add_node("rca_analysis", self.rca_agent.analyze)
        
        # 设置入口点（并行）
        workflow.set_entry_point("metric_analysis")
        workflow.set_entry_point("log_analysis")
        workflow.set_entry_point("trace_analysis")
        
        # 添加边（汇聚到 RCA）
        workflow.add_edge("metric_analysis", "rca_analysis")
        workflow.add_edge("log_analysis", "rca_analysis")
        workflow.add_edge("trace_analysis", "rca_analysis")
        
        # 设置结束点
        workflow.add_edge("rca_analysis", END)
        
        return workflow.compile()
```

---

## 4. Agent 详细设计

### 4.1 Metric Agent（指标分析 Agent）

**职责**: 分析时序指标，识别资源异常（CPU、内存、线程、连接池等）

**实现**:

```python
from typing import List, Dict, Optional
from datetime import datetime
import asyncio
from dataclasses import dataclass

from collector.prometheus.client import PrometheusClient
from detector.metric.anomaly_detector import AnomalyDetector
from analyzer.llm.llm_service import LLMService


@dataclass
class MetricAnomaly:
    """指标异常"""
    metric_name: str
    anomaly_type: str  # SPIKE, DROP, STEADY_INCREASE
    current_value: float
    baseline: float
    deviation: float  # 0-1
    detected_at: datetime
    llm_insight: Optional[str] = None


class MetricAgent:
    """指标分析 Agent"""
    
    def __init__(
        self,
        prometheus_client: PrometheusClient,
        anomaly_detector: AnomalyDetector,
        llm_service: LLMService
    ):
        self.prometheus_client = prometheus_client
        self.anomaly_detector = anomaly_detector
        self.llm_service = llm_service
    
    async def analyze(self, state: Dict) -> Dict:
        """分析指标异常"""
        service = state["target_service"]
        start_time = state["start_time"]
        end_time = state["end_time"]
        
        # 1. 查询关键指标
        metrics = await self._query_key_metrics(service, start_time, end_time)
        
        # 2. 异常检测
        anomalies = []
        for metric_name, points in metrics.items():
            anomaly = await self.anomaly_detector.detect(metric_name, points)
            if anomaly:
                anomalies.append(anomaly)
        
        # 3. LLM 增强分析
        if anomalies:
            prompt = self._build_metric_analysis_prompt(anomalies)
            llm_analysis = await self.llm_service.analyze(prompt)
            
            # 将 LLM 分析结果附加到异常
            for anomaly in anomalies:
                anomaly.llm_insight = llm_analysis
        
        state["metric_anomalies"] = [vars(a) for a in anomalies]
        return state
    
    async def _query_key_metrics(
        self,
        service: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, List]:
        """查询关键指标"""
        queries = {
            # JVM 内存
            "jvm_memory_used": f"jvm_memory_used_bytes{{application='{service}'}}",
            
            # JVM 线程
            "jvm_threads_live": f"jvm_threads_live{{application='{service}'}}",
            
            # CPU 使用率
            "process_cpu_usage": f"process_cpu_usage{{application='{service}'}}",
            
            # HTTP 错误率
            "http_error_rate": f"rate(http_server_requests_seconds_count{{application='{service}',status=~'5..'}}[5m])",
            
            # HTTP P99 延迟
            "http_p99_latency": f"histogram_quantile(0.99, rate(http_server_requests_seconds_bucket{{application='{service}'}}[5m]))",
            
            # 数据库连接池
            "hikaricp_connections_active": f"hikaricp_connections_active{{application='{service}'}}"
        }
        
        # 并行查询
        tasks = [
            self.prometheus_client.query_range(query, start_time, end_time, step="30s")
            for query in queries.values()
        ]
        
        results = await asyncio.gather(*tasks)
        
        return dict(zip(queries.keys(), results))
    
    def _build_metric_analysis_prompt(self, anomalies: List[MetricAnomaly]) -> str:
        """构建分析提示词"""
        prompt_parts = ["作为运维专家，请分析以下指标异常：\n"]
        
        for anomaly in anomalies:
            prompt_parts.append(
                f"\n指标: {anomaly.metric_name}\n"
                f"异常类型: {anomaly.anomaly_type}\n"
                f"当前值: {anomaly.current_value:.2f}, "
                f"基线: {anomaly.baseline:.2f}, "
                f"偏离: {anomaly.deviation * 100:.1f}%\n"
            )
        
        prompt_parts.append(
            "\n请判断可能的问题类型（内存泄漏/线程泄漏/CPU飙高/连接池耗尽等）及严重程度。"
        )
        
        return "".join(prompt_parts)
```

---

### 4.2 Log Agent（日志分析 Agent）

**职责**: 分析日志模式，识别错误堆栈、异常关键词

**实现**:

```java
@Component
public class LogAgent {
    
    @Autowired
    private LokiClient lokiClient;
    
    @Autowired
    private LogPatternDetector patternDetector;
    
    @Autowired
    private LLMService llmService;
    
    public DiagnosisState analyze(DiagnosisState state) {
        String service = state.getTargetService();
        Instant start = state.getStartTime();
        Instant end = state.getEndTime();
        
        // 1. 查询错误日志
        String logQuery = String.format("{app=\"%s\", level=\"ERROR\"}", service);
        List<LogEntry> errorLogs = lokiClient.query(logQuery, start, end);
        
        // 2. 模式聚类
        Map<String, List<LogEntry>> patterns = patternDetector.cluster(errorLogs);
        
        // 3. 识别关键异常
        List<LogAnomaly> anomalies = new ArrayList<>();
        for (Map.Entry<String, List<LogEntry>> entry : patterns.entrySet()) {
            String pattern = entry.getKey();
            List<LogEntry> logs = entry.getValue();
            
            if (logs.size() >= 10) { // 频率阈值
                LogAnomaly anomaly = new LogAnomaly();
                anomaly.setPattern(pattern);
                anomaly.setCount(logs.size());
                anomaly.setSampleLog(logs.get(0).getMessage());
                anomaly.setFirstOccurrence(logs.get(0).getTimestamp());
                
                // 提取堆栈
                Optional<String> stackTrace = extractStackTrace(logs.get(0).getMessage());
                stackTrace.ifPresent(anomaly::setStackTrace);
                
                anomalies.add(anomaly);
            }
        }
        
        // 4. LLM 增强分析
        if (!anomalies.isEmpty()) {
            String prompt = buildLogAnalysisPrompt(anomalies);
            String llmAnalysis = llmService.analyze(prompt);
            
            for (LogAnomaly anomaly : anomalies) {
                anomaly.setLlmInsight(llmAnalysis);
            }
        }
        
        state.setLogAnomalies(anomalies);
        return state;
    }
    
    private Optional<String> extractStackTrace(String logMessage) {
        // 正则提取 Java 堆栈
        Pattern pattern = Pattern.compile("(\\w+\\.\\w+Exception[\\s\\S]*?at [\\s\\S]*?)\\n\\n");
        Matcher matcher = pattern.matcher(logMessage);
        
        if (matcher.find()) {
            return Optional.of(matcher.group(1));
        }
        return Optional.empty();
    }
    
    private String buildLogAnalysisPrompt(List<LogAnomaly> anomalies) {
        StringBuilder prompt = new StringBuilder();
        prompt.append("作为运维专家，请分析以下错误日志模式：\n\n");
        
        for (LogAnomaly anomaly : anomalies) {
            prompt.append(String.format("模式: %s\n", anomaly.getPattern()));
            prompt.append(String.format("出现次数: %d\n", anomaly.getCount()));
            prompt.append(String.format("示例日志: %s\n", anomaly.getSampleLog()));
            if (anomaly.getStackTrace() != null) {
                prompt.append(String.format("堆栈: %s\n", anomaly.getStackTrace()));
            }
            prompt.append("\n");
        }
        
        prompt.append("请判断错误类型和可能的根因。");
        return prompt.toString();
    }
}
```

**输出**:
```java
public class LogAnomaly {
    private String pattern;             // 日志模式（聚类后的代表性模式）
    private int count;                  // 出现次数
    private String sampleLog;           // 示例日志
    private String stackTrace;          // 堆栈信息（如有）
    private Instant firstOccurrence;    // 首次出现时间
    private String llmInsight;          // LLM 分析结论
}
```

---

### 4.3 Trace Agent（链路分析 Agent）

**职责**: 分析调用链，定位慢节点和错误传播路径

**实现**:

```java
@Component
public class TraceAgent {
    
    @Autowired
    private TempoClient tempoClient;
    
    @Autowired
    private SlowTraceDetector slowTraceDetector;
    
    @Autowired
    private LLMService llmService;
    
    public DiagnosisState analyze(DiagnosisState state) {
        String service = state.getTargetService();
        Instant start = state.getStartTime();
        Instant end = state.getEndTime();
        
        // 1. 查询慢链路
        List<Trace> traces = tempoClient.querySlowTraces(service, start, end, Duration.ofSeconds(5));
        
        // 2. 分析慢节点
        List<TraceAnomaly> anomalies = new ArrayList<>();
        for (Trace trace : traces) {
            Optional<Span> slowestSpan = findSlowestSpan(trace);
            if (slowestSpan.isPresent()) {
                Span span = slowestSpan.get();
                
                TraceAnomaly anomaly = new TraceAnomaly();
                anomaly.setTraceId(trace.getTraceId());
                anomaly.setOperation(span.getOperationName());
                anomaly.setDuration(span.getDuration());
                anomaly.setService(span.getServiceName());
                anomaly.setTimestamp(span.getStartTime());
                
                // 提取错误信息
                if (span.hasError()) {
                    anomaly.setErrorMessage(span.getErrorMessage());
                }
                
                anomalies.add(anomaly);
            }
        }
        
        // 3. LLM 增强分析
        if (!anomalies.isEmpty()) {
            String prompt = buildTraceAnalysisPrompt(anomalies);
            String llmAnalysis = llmService.analyze(prompt);
            
            for (TraceAnomaly anomaly : anomalies) {
                anomaly.setLlmInsight(llmAnalysis);
            }
        }
        
        state.setTraceAnomalies(anomalies);
        return state;
    }
    
    private Optional<Span> findSlowestSpan(Trace trace) {
        return trace.getSpans().stream()
            .max(Comparator.comparing(Span::getDuration));
    }
    
    private String buildTraceAnalysisPrompt(List<TraceAnomaly> anomalies) {
        StringBuilder prompt = new StringBuilder();
        prompt.append("作为运维专家，请分析以下慢链路：\n\n");
        
        for (TraceAnomaly anomaly : anomalies) {
            prompt.append(String.format("Trace ID: %s\n", anomaly.getTraceId()));
            prompt.append(String.format("操作: %s\n", anomaly.getOperation()));
            prompt.append(String.format("耗时: %d ms\n", anomaly.getDuration().toMillis()));
            prompt.append(String.format("服务: %s\n", anomaly.getService()));
            if (anomaly.getErrorMessage() != null) {
                prompt.append(String.format("错误: %s\n", anomaly.getErrorMessage()));
            }
            prompt.append("\n");
        }
        
        prompt.append("请判断性能瓶颈在哪个环节（数据库查询/外部调用/业务逻辑等）。");
        return prompt.toString();
    }
}
```

**输出**:
```java
public class TraceAnomaly {
    private String traceId;             // 链路 ID
    private String operation;           // 操作名称
    private Duration duration;          // 耗时
    private String service;             // 服务名
    private Instant timestamp;          // 时间戳
    private String errorMessage;        // 错误信息（如有）
    private String llmInsight;          // LLM 分析结论
}
```

---

### 4.4 RCA Agent（根因分析 Agent）

**职责**: 综合多源证据，输出根因排序、置信度、修复建议

**实现**:

```java
@Component
public class RCAAgent {
    
    @Autowired
    private LLMService llmService;
    
    @Autowired
    private FixRecommender fixRecommender;
    
    public DiagnosisState analyze(DiagnosisState state) {
        // 1. 收集证据
        List<Evidence> evidences = collectEvidences(state);
        
        // 2. 构建 RCA Prompt
        String rcaPrompt = buildRCAPrompt(evidences);
        
        // 3. LLM 推理
        String llmResponse = llmService.analyze(rcaPrompt);
        
        // 4. 解析根因
        List<RootCause> rootCauses = parseRootCauses(llmResponse);
        
        // 5. 生成修复建议
        for (RootCause rootCause : rootCauses) {
            List<String> recommendations = fixRecommender.recommend(rootCause.getProblemType());
            rootCause.setRecommendations(recommendations);
        }
        
        // 6. 排序（按置信度）
        rootCauses.sort(Comparator.comparing(RootCause::getConfidence).reversed());
        
        // 7. 生成报告
        DiagnosisReport report = buildReport(state, rootCauses, evidences);
        
        state.setRootCauses(rootCauses);
        state.setEvidences(evidences);
        state.setReport(report);
        state.setStatus(DiagnosisStatus.COMPLETED);
        
        return state;
    }
    
    private List<Evidence> collectEvidences(DiagnosisState state) {
        List<Evidence> evidences = new ArrayList<>();
        
        // 指标证据
        for (MetricAnomaly anomaly : state.getMetricAnomalies()) {
            Evidence evidence = new Evidence();
            evidence.setType(EvidenceType.METRIC);
            evidence.setSource(anomaly.getMetricName());
            evidence.setDescription(String.format("%s 异常: 当前值 %.2f, 偏离基线 %.1f%%", 
                anomaly.getMetricName(), anomaly.getCurrentValue(), anomaly.getDeviation() * 100));
            evidence.setWeight(calculateWeight(anomaly.getDeviation()));
            evidences.add(evidence);
        }
        
        // 日志证据
        for (LogAnomaly anomaly : state.getLogAnomalies()) {
            Evidence evidence = new Evidence();
            evidence.setType(EvidenceType.LOG);
            evidence.setSource("Error Log");
            evidence.setDescription(String.format("错误日志出现 %d 次: %s", 
                anomaly.getCount(), anomaly.getPattern()));
            evidence.setDetail(anomaly.getStackTrace());
            evidence.setWeight(calculateWeight(anomaly.getCount() / 100.0));
            evidences.add(evidence);
        }
        
        // 链路证据
        for (TraceAnomaly anomaly : state.getTraceAnomalies()) {
            Evidence evidence = new Evidence();
            evidence.setType(EvidenceType.TRACE);
            evidence.setSource(anomaly.getOperation());
            evidence.setDescription(String.format("慢链路 %s 耗时 %d ms", 
                anomaly.getOperation(), anomaly.getDuration().toMillis()));
            evidence.setDetail(anomaly.getTraceId());
            evidence.setWeight(0.8);
            evidences.add(evidence);
        }
        
        return evidences;
    }
    
    private String buildRCAPrompt(List<Evidence> evidences) {
        StringBuilder prompt = new StringBuilder();
        prompt.append("你是一位资深的 AIOps 工程师，请根据以下多源证据进行根因分析：\n\n");
        
        prompt.append("=== 证据列表 ===\n");
        for (int i = 0; i < evidences.size(); i++) {
            Evidence e = evidences.get(i);
            prompt.append(String.format("%d. [%s] %s\n", i + 1, e.getType(), e.getDescription()));
            if (e.getDetail() != null) {
                prompt.append(String.format("   详情: %s\n", e.getDetail()));
            }
        }
        
        prompt.append("\n=== 分析要求 ===\n");
        prompt.append("1. 综合以上证据，判断最可能的根因（可能有多个）\n");
        prompt.append("2. 对每个根因给出置信度（0-100%）\n");
        prompt.append("3. 解释推理过程和证据链\n");
        prompt.append("4. 问题类型必须从以下选择: MEMORY_LEAK, THREAD_LEAK, SLOW_SQL, POOL_EXHAUST, CPU_SPIKE, DEADLOCK, UNKNOWN\n");
        prompt.append("\n请按以下 JSON 格式输出：\n");
        prompt.append("{\n");
        prompt.append("  \"rootCauses\": [\n");
        prompt.append("    {\n");
        prompt.append("      \"problemType\": \"MEMORY_LEAK\",\n");
        prompt.append("      \"description\": \"内存泄漏，疑似静态集合未清理\",\n");
        prompt.append("      \"confidence\": 0.92,\n");
        prompt.append("      \"reasoning\": \"证据 1、2、3 表明...\"\n");
        prompt.append("    }\n");
        prompt.append("  ]\n");
        prompt.append("}\n");
        
        return prompt.toString();
    }
    
    private List<RootCause> parseRootCauses(String llmResponse) {
        // 解析 LLM 返回的 JSON
        try {
            ObjectMapper mapper = new ObjectMapper();
            JsonNode root = mapper.readTree(llmResponse);
            JsonNode rootCausesNode = root.get("rootCauses");
            
            List<RootCause> rootCauses = new ArrayList<>();
            for (JsonNode node : rootCausesNode) {
                RootCause rc = new RootCause();
                rc.setProblemType(ProblemType.valueOf(node.get("problemType").asText()));
                rc.setDescription(node.get("description").asText());
                rc.setConfidence(node.get("confidence").asDouble());
                rc.setReasoning(node.get("reasoning").asText());
                rootCauses.add(rc);
            }
            
            return rootCauses;
        } catch (Exception e) {
            log.error("Failed to parse LLM response", e);
            // 降级：返回默认根因
            RootCause fallback = new RootCause();
            fallback.setProblemType(ProblemType.UNKNOWN);
            fallback.setDescription("分析失败，请人工介入");
            fallback.setConfidence(0.0);
            return List.of(fallback);
        }
    }
    
    private DiagnosisReport buildReport(DiagnosisState state, List<RootCause> rootCauses, List<Evidence> evidences) {
        DiagnosisReport report = new DiagnosisReport();
        report.setDiagnosisId(state.getDiagnosisId());
        report.setTargetService(state.getTargetService());
        report.setStartTime(state.getStartTime());
        report.setEndTime(state.getEndTime());
        report.setRootCauses(rootCauses);
        report.setEvidences(evidences);
        report.setGeneratedAt(Instant.now());
        
        // 取置信度最高的根因
        if (!rootCauses.isEmpty()) {
            RootCause primary = rootCauses.get(0);
            report.setPrimaryProblemType(primary.getProblemType());
            report.setConfidence(primary.getConfidence());
        }
        
        return report;
    }
    
    private double calculateWeight(double factor) {
        return Math.min(1.0, Math.max(0.1, factor));
    }
}
```

**输出**:
```java
public class RootCause {
    private ProblemType problemType;    // 问题类型
    private String description;         // 根因描述
    private double confidence;          // 置信度 (0-1)
    private String reasoning;           // 推理过程
    private List<String> recommendations; // 修复建议
}

public class Evidence {
    private EvidenceType type;          // METRIC, LOG, TRACE
    private String source;              // 证据来源
    private String description;         // 证据描述
    private String detail;              // 详细信息
    private double weight;              // 权重 (0-1)
}
```

---

## 5. 数据采集设计

### 5.1 Prometheus 客户端

```python
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import quote
import httpx
from pydantic import BaseModel


class MetricPoint(BaseModel):
    """指标数据点"""
    timestamp: datetime
    value: float


class PrometheusClient:
    """Prometheus 客户端"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "30s"
    ) -> List[MetricPoint]:
        """范围查询"""
        url = f"{self.base_url}/api/v1/query_range"
        
        params = {
            "query": query,
            "start": int(start.timestamp()),
            "end": int(end.timestamp()),
            "step": step
        }
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return self._parse_response(data)
    
    async def query(self, query: str) -> Optional[float]:
        """即时查询"""
        url = f"{self.base_url}/api/v1/query"
        
        params = {"query": query}
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data["status"] == "success" and data["data"]["result"]:
            result = data["data"]["result"][0]
            return float(result["value"][1])
        
        return None
    
    def _parse_response(self, response_data: Dict) -> List[MetricPoint]:
        """解析响应"""
        points = []
        
        if response_data["status"] == "success":
            results = response_data.get("data", {}).get("result", [])
            
            for result in results:
                values = result.get("values", [])
                
                for timestamp, value in values:
                    points.append(
                        MetricPoint(
                            timestamp=datetime.fromtimestamp(timestamp),
                            value=float(value)
                        )
                    )
        
        return points
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
```

### 5.2 Loki 客户端

```python
from typing import List, Dict
from datetime import datetime
import httpx
from pydantic import BaseModel


class LogEntry(BaseModel):
    """日志条目"""
    timestamp: datetime
    message: str
    labels: Dict[str, str]


class LokiClient:
    """Loki 客户端"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        limit: int = 1000
    ) -> List[LogEntry]:
        """范围查询日志"""
        url = f"{self.base_url}/loki/api/v1/query_range"
        
        params = {
            "query": query,
            "start": int(start.timestamp() * 1e9),  # 纳秒
            "end": int(end.timestamp() * 1e9),
            "limit": limit
        }
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return self._parse_response(data)
    
    def _parse_response(self, response_data: Dict) -> List[LogEntry]:
        """解析响应"""
        entries = []
        
        if response_data["status"] == "success":
            results = response_data.get("data", {}).get("result", [])
            
            for result in results:
                labels = result.get("stream", {})
                values = result.get("values", [])
                
                for timestamp_ns, message in values:
                    entries.append(
                        LogEntry(
                            timestamp=datetime.fromtimestamp(int(timestamp_ns) / 1e9),
                            message=message,
                            labels=labels
                        )
                    )
        
        return entries
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
```

### 5.3 Tempo 客户端

```java
@Service
public class TempoClient {
    
    @Value("${tempo.url}")
    private String tempoUrl;
    
    private final RestTemplate restTemplate = new RestTemplate();
    
    public List<Trace> querySlowTraces(String service, Instant start, Instant end, Duration threshold) {
        String url = String.format("%s/api/search?tags=service.name=%s&start=%d&end=%d&minDuration=%dms",
            tempoUrl,
            service,
            start.toEpochMilli() * 1000000, // 纳秒
            end.toEpochMilli() * 1000000,
            threshold.toMillis());
        
        TempoResponse response = restTemplate.getForObject(url, TempoResponse.class);
        
        return parseResponse(response);
    }
}
```

---

## 6. 异常检测设计

### 6.1 基于阈值的检测

```python
from typing import Optional, Dict, List
from datetime import datetime
from dataclasses import dataclass

from collector.prometheus.client import MetricPoint


@dataclass
class MetricAnomaly:
    """指标异常"""
    metric_name: str
    anomaly_type: str
    current_value: float
    baseline: float
    deviation: float
    detected_at: datetime


class ThresholdDetector:
    """基于阈值的检测器"""
    
    # 阈值配置
    THRESHOLDS: Dict[str, float] = {
        "jvm_memory_used": 0.9,        # 内存使用率 > 90%
        "process_cpu_usage": 0.8,      # CPU 使用率 > 80%
        "jvm_threads_live": 200.0,     # 线程数 > 200
        "http_error_rate": 0.05        # 错误率 > 5%
    }
    
    async def detect(
        self,
        metric_name: str,
        points: List[MetricPoint]
    ) -> Optional[MetricAnomaly]:
        """检测指标异常"""
        threshold = self.THRESHOLDS.get(metric_name)
        if not threshold:
            return None
        
        # 检查最后 5 个点是否持续超过阈值
        recent_points = sorted(points, key=lambda p: p.timestamp, reverse=True)[:5]
        
        exceed_count = sum(1 for p in recent_points if p.value > threshold)
        
        if exceed_count >= 3:
            current_value = recent_points[0].value
            
            return MetricAnomaly(
                metric_name=metric_name,
                anomaly_type="SPIKE",
                current_value=current_value,
                baseline=threshold,
                deviation=(current_value - threshold) / threshold,
                detected_at=datetime.now()
            )
        
        return None
```

### 6.2 基于动态基线的检测

```python
from typing import Optional, List
from datetime import datetime, timedelta
import numpy as np

from collector.prometheus.client import MetricPoint, PrometheusClient
from storage.cache.redis_service import RedisService


class BaselineDetector:
    """基于动态基线的检测器"""
    
    def __init__(
        self,
        prometheus_client: PrometheusClient,
        redis_service: RedisService
    ):
        self.prometheus_client = prometheus_client
        self.redis_service = redis_service
    
    async def detect(
        self,
        metric_name: str,
        points: List[MetricPoint]
    ) -> Optional[MetricAnomaly]:
        """检测指标异常"""
        # 1. 获取历史基线（过去 7 天同时段）
        baseline = await self._get_historical_baseline(metric_name)
        
        # 2. 计算当前均值
        values = [p.value for p in points]
        current_avg = np.mean(values)
        
        # 3. 检测偏离
        deviation = abs(current_avg - baseline) / baseline
        
        if deviation > 0.3:  # 偏离 > 30%
            return MetricAnomaly(
                metric_name=metric_name,
                anomaly_type=self._determine_anomaly_type(current_avg, baseline),
                current_value=current_avg,
                baseline=baseline,
                deviation=deviation,
                detected_at=datetime.now()
            )
        
        return None
    
    async def _get_historical_baseline(self, metric_name: str) -> float:
        """获取历史基线"""
        cache_key = f"baseline:{metric_name}"
        
        # 尝试从缓存获取
        cached = await self.redis_service.get(cache_key)
        if cached:
            return float(cached)
        
        # 从 Prometheus 查询历史数据并计算基线
        now = datetime.now()
        start = now - timedelta(days=7)
        
        # 这里简化处理，实际应该查询同时段数据
        points = await self.prometheus_client.query_range(
            metric_name,
            start,
            now,
            step="1h"
        )
        
        if points:
            values = [p.value for p in points]
            baseline = np.median(values)  # 使用中位数作为基线
            
            # 缓存 1 小时
            await self.redis_service.set(cache_key, baseline, ex=3600)
            
            return baseline
        
        return 100.0  # 默认值
    
    def _determine_anomaly_type(self, current: float, baseline: float) -> str:
        """判断异常类型"""
        if current > baseline * 1.5:
            return "SPIKE"
        elif current < baseline * 0.5:
            return "DROP"
        else:
            return "STEADY_INCREASE"
```

---

## 7. LLM 集成设计

### 7.1 LLM 服务接口

```python
from typing import Protocol, Dict
from abc import ABC, abstractmethod

from app.config import get_settings


class LLMProvider(ABC):
    """LLM 提供者抽象基类"""
    
    @abstractmethod
    async def chat(self, prompt: str, **kwargs) -> str:
        """聊天接口"""
        pass


class LLMService:
    """LLM 服务"""
    
    def __init__(self):
        self.settings = get_settings()
        self.provider = self._init_provider()
    
    def _init_provider(self) -> LLMProvider:
        """初始化提供者"""
        provider_name = self.settings.llm_provider
        
        if provider_name == "qwen":
            from analyzer.llm.qwen_client import QwenClient
            return QwenClient(
                api_key=self.settings.qwen_api_key,
                model=self.settings.qwen_model,
                base_url=self.settings.qwen_base_url
            )
        elif provider_name == "deepseek":
            from analyzer.llm.deepseek_client import DeepSeekClient
            return DeepSeekClient(
                api_key=self.settings.deepseek_api_key,
                model=self.settings.deepseek_model,
                base_url=self.settings.deepseek_base_url
            )
        elif provider_name == "openai":
            from analyzer.llm.openai_client import OpenAIClient
            return OpenAIClient(
                api_key=self.settings.openai_api_key,
                model=self.settings.openai_model,
                base_url=self.settings.openai_base_url
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
    
    async def analyze(self, prompt: str, **kwargs) -> str:
        """分析"""
        return await self.provider.chat(prompt, **kwargs)
```

### 7.2 通义千问客户端

```python
import httpx
from typing import Dict, Any

from analyzer.llm.llm_service import LLMProvider


class QwenClient(LLMProvider):
    """通义千问客户端"""
    
    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def chat(self, prompt: str, **kwargs) -> str:
        """聊天"""
        url = f"{self.base_url}/services/aigc/text-generation/generation"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": {
                "prompt": prompt
            },
            "parameters": {
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2000),
                "top_p": kwargs.get("top_p", 0.8)
            }
        }
        
        response = await self.client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # 提取响应文本
        if data.get("output") and data["output"].get("text"):
            return data["output"]["text"]
        
        raise ValueError(f"Invalid response from Qwen API: {data}")
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
```

### 7.3 DeepSeek 客户端

```python
import httpx
from typing import Dict, Any

from analyzer.llm.llm_service import LLMProvider


class DeepSeekClient(LLMProvider):
    """DeepSeek 客户端"""
    
    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def chat(self, prompt: str, **kwargs) -> str:
        """聊天（兼容 OpenAI API 格式）"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2000)
        }
        
        response = await self.client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # 提取响应文本
        if data.get("choices") and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        
        raise ValueError(f"Invalid response from DeepSeek API: {data}")
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
```

---

## 8. 告警处理设计

### 8.1 Prometheus Alertmanager Webhook

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

from alert.trigger.diagnosis_trigger import DiagnosisTrigger


router = APIRouter()


class PrometheusAlert(BaseModel):
    """Prometheus 告警"""
    status: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    startsAt: datetime
    endsAt: datetime


class PrometheusAlertPayload(BaseModel):
    """Prometheus 告警负载"""
    alerts: List[PrometheusAlert]


@router.post("/api/webhook/prometheus")
async def handle_prometheus_alert(
    payload: PrometheusAlertPayload,
    diagnosis_trigger: DiagnosisTrigger
):
    """处理 Prometheus 告警"""
    for alert in payload.alerts:
        if alert.status == "firing":
            # 触发自动诊断
            service = alert.labels.get("application")
            
            if service:
                diagnosis_id = await diagnosis_trigger.trigger(
                    service=service,
                    source="prometheus_alert",
                    context=alert.dict()
                )
                
                print(f"Diagnosis triggered: {diagnosis_id}")
    
    return {"status": "ok", "message": "Alerts received"}
```

### 8.2 诊断触发器

```python
from typing import Any, Dict
from datetime import datetime, timedelta
import uuid

from aiokafka import AIOKafkaProducer
import json

from app.config import get_settings


class DiagnosisTrigger:
    """诊断触发器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.producer = None
    
    async def initialize(self):
        """初始化 Kafka 生产者"""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()
    
    async def trigger(
        self,
        service: str,
        source: str,
        context: Any = None
    ) -> str:
        """触发诊断"""
        diagnosis_id = str(uuid.uuid4())
        
        event = {
            "diagnosis_id": diagnosis_id,
            "target_service": service,
            "source": source,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        # 发送到 Kafka 异步处理
        await self.producer.send(
            "diagnosis-trigger",
            value=event,
            key=diagnosis_id.encode('utf-8')
        )
        
        print(f"Diagnosis triggered: {diagnosis_id}")
        return diagnosis_id
    
    async def close(self):
        """关闭生产者"""
        if self.producer:
            await self.producer.stop()
```

### 8.3 Kafka 消费者

```python
from aiokafka import AIOKafkaConsumer
import json
import asyncio
from datetime import datetime, timedelta

from engine.orchestrator.diagnosis_orchestrator import DiagnosisOrchestrator
from app.config import get_settings


class DiagnosisEventConsumer:
    """诊断事件消费者"""
    
    def __init__(self, orchestrator: DiagnosisOrchestrator):
        self.settings = get_settings()
        self.orchestrator = orchestrator
        self.consumer = None
    
    async def start(self):
        """启动消费者"""
        self.consumer = AIOKafkaConsumer(
            "diagnosis-trigger",
            bootstrap_servers=self.settings.kafka_bootstrap_servers,
            group_id=self.settings.kafka_group_id,
            auto_offset_reset=self.settings.kafka_auto_offset_reset,
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
        
        await self.consumer.start()
        
        try:
            async for message in self.consumer:
                await self._process_event(message.value)
        finally:
            await self.consumer.stop()
    
    async def _process_event(self, event: dict):
        """处理诊断事件"""
        print(f"Processing diagnosis event: {event['diagnosis_id']}")
        
        try:
            # 构建初始状态
            timestamp = datetime.fromisoformat(event["timestamp"])
            
            initial_state = {
                "diagnosis_id": event["diagnosis_id"],
                "target_service": event["target_service"],
                "start_time": timestamp - timedelta(minutes=15),
                "end_time": timestamp,
                "metric_anomalies": [],
                "log_anomalies": [],
                "trace_anomalies": [],
                "root_causes": [],
                "evidences": [],
                "confidence": 0.0,
                "report": None,
                "status": "init"
            }
            
            # 启动诊断流程
            await self.orchestrator.diagnose(initial_state)
            
        except Exception as e:
            print(f"Diagnosis failed: {event['diagnosis_id']}, error: {e}")
```

---

## 9. 数据存储设计

### 9.1 数据库模型

```python
from sqlalchemy import Column, String, DateTime, Float, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from enum import Enum

from common.enums import DiagnosisStatus, ProblemType


Base = declarative_base()


class DiagnosisReportModel(Base):
    """诊断报告模型"""
    __tablename__ = "diagnosis_reports"
    
    diagnosis_id = Column(String(36), primary_key=True)
    target_service = Column(String(100), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    primary_problem_type = Column(SQLEnum(ProblemType), nullable=True, index=True)
    confidence = Column(Float, nullable=True)
    
    root_causes_json = Column(JSON, nullable=True)
    evidences_json = Column(JSON, nullable=True)
    
    status = Column(SQLEnum(DiagnosisStatus), nullable=False, index=True)
    
    generated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class DiagnosisHistoryModel(Base):
    """诊断历史模型"""
    __tablename__ = "diagnosis_history"
    
    id = Column(String(36), primary_key=True)
    diagnosis_id = Column(String(36), nullable=False, index=True)
    target_service = Column(String(100), nullable=False, index=True)
    problem_type = Column(SQLEnum(ProblemType), nullable=True)
    confidence = Column(Float, nullable=True)
    generated_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
```

### 9.2 Repository

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime

from storage.models.diagnosis_report import DiagnosisReportModel
from common.enums import ProblemType


class DiagnosisReportRepository:
    """诊断报告仓储"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, report: DiagnosisReportModel) -> DiagnosisReportModel:
        """创建报告"""
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report
    
    async def get_by_id(self, diagnosis_id: str) -> Optional[DiagnosisReportModel]:
        """根据 ID 查询"""
        result = await self.session.execute(
            select(DiagnosisReportModel).where(
                DiagnosisReportModel.diagnosis_id == diagnosis_id
            )
        )
        return result.scalar_one_or_none()
    
    async def find_by_service(
        self,
        service: str,
        limit: int = 10
    ) -> List[DiagnosisReportModel]:
        """根据服务查询"""
        result = await self.session.execute(
            select(DiagnosisReportModel)
            .where(DiagnosisReportModel.target_service == service)
            .order_by(DiagnosisReportModel.generated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def find_by_problem_type(
        self,
        problem_type: ProblemType,
        limit: int = 10
    ) -> List[DiagnosisReportModel]:
        """根据问题类型查询"""
        result = await self.session.execute(
            select(DiagnosisReportModel)
            .where(DiagnosisReportModel.primary_problem_type == problem_type)
            .order_by(DiagnosisReportModel.generated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def find_by_time_range(
        self,
        start: datetime,
        end: datetime
    ) -> List[DiagnosisReportModel]:
        """根据时间范围查询"""
        result = await self.session.execute(
            select(DiagnosisReportModel)
            .where(
                and_(
                    DiagnosisReportModel.generated_at >= start,
                    DiagnosisReportModel.generated_at <= end
                )
            )
            .order_by(DiagnosisReportModel.generated_at.desc())
        )
        return list(result.scalars().all())
    
    async def find_high_confidence_reports(
        self,
        min_confidence: float = 0.7
    ) -> List[DiagnosisReportModel]:
        """查询高置信度报告"""
        result = await self.session.execute(
            select(DiagnosisReportModel)
            .where(DiagnosisReportModel.confidence >= min_confidence)
            .order_by(DiagnosisReportModel.generated_at.desc())
        )
        return list(result.scalars().all())
    
    async def update(self, report: DiagnosisReportModel) -> DiagnosisReportModel:
        """更新报告"""
        await self.session.commit()
        await self.session.refresh(report)
        return report
```

### 9.3 Redis 服务

```python
from typing import Optional, Any
import json
import redis.asyncio as aioredis

from app.config import get_settings


class RedisService:
    """Redis 服务"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
    
    async def initialize(self):
        """初始化连接"""
        self.client = await aioredis.from_url(
            self.settings.redis_url,
            decode_responses=self.settings.redis_decode_responses
        )
    
    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        return await self.client.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None
    ) -> bool:
        """设置值"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        return await self.client.set(key, value, ex=ex)
    
    async def delete(self, key: str) -> int:
        """删除键"""
        return await self.client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return await self.client.exists(key) > 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        return await self.client.expire(key, seconds)
    
    async def close(self):
        """关闭连接"""
        if self.client:
            await self.client.close()
```

---

## 10. API 设计

### 10.1 FastAPI 应用入口

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from api.routers import diagnosis, history, config
from storage.database import init_db
from storage.cache.redis_service import RedisService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """生命周期管理"""
    # 启动时初始化
    settings = get_settings()
    
    # 初始化数据库
    await init_db()
    
    # 初始化 Redis
    redis_service = RedisService()
    await redis_service.initialize()
    
    # 初始化 Kafka 消费者
    # ...
    
    print(f"{settings.app_name} started")
    
    yield
    
    # 关闭时清理
    await redis_service.close()
    print(f"{settings.app_name} stopped")


# 创建应用
app = FastAPI(
    title="AIOps Diagnosis Agent",
    description="AI-powered intelligent operations diagnosis platform",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(diagnosis.router, prefix="/api", tags=["diagnosis"])
app.include_router(history.router, prefix="/api", tags=["history"])
app.include_router(config.router, prefix="/api", tags=["config"])


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """根路径"""
    return {"message": "AIOps Diagnosis Agent API"}
```

### 10.2 诊断接口

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

from engine.orchestrator.diagnosis_orchestrator import DiagnosisOrchestrator
from storage.repositories.diagnosis_repository import DiagnosisReportRepository
from common.enums import DiagnosisStatus, ProblemType


router = APIRouter()


class DiagnosisRequest(BaseModel):
    """诊断请求"""
    target_service: str
    start_time: datetime
    end_time: datetime


class DiagnosisResponse(BaseModel):
    """诊断响应"""
    diagnosis_id: str
    status: str
    message: str


class RootCause(BaseModel):
    """根因"""
    problem_type: ProblemType
    description: str
    confidence: float
    reasoning: str
    recommendations: List[str]


class Evidence(BaseModel):
    """证据"""
    type: str
    source: str
    description: str
    detail: Optional[str] = None
    weight: float


class DiagnosisReport(BaseModel):
    """诊断报告"""
    diagnosis_id: str
    target_service: str
    start_time: datetime
    end_time: datetime
    primary_problem_type: Optional[ProblemType]
    confidence: Optional[float]
    root_causes: List[RootCause]
    evidences: List[Evidence]
    generated_at: datetime


@router.post("/diagnosis/trigger", response_model=DiagnosisResponse)
async def trigger_diagnosis(
    request: DiagnosisRequest,
    orchestrator: DiagnosisOrchestrator = Depends()
):
    """触发诊断"""
    try:
        diagnosis_id = await orchestrator.trigger(
            service=request.target_service,
            start_time=request.start_time,
            end_time=request.end_time
        )
        
        return DiagnosisResponse(
            diagnosis_id=diagnosis_id,
            status="processing",
            message="Diagnosis triggered successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diagnosis/{diagnosis_id}", response_model=DiagnosisReport)
async def get_diagnosis(
    diagnosis_id: str,
    repository: DiagnosisReportRepository = Depends()
):
    """查询诊断报告"""
    report = await repository.get_by_id(diagnosis_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    
    return DiagnosisReport(
        diagnosis_id=report.diagnosis_id,
        target_service=report.target_service,
        start_time=report.start_time,
        end_time=report.end_time,
        primary_problem_type=report.primary_problem_type,
        confidence=report.confidence,
        root_causes=report.root_causes_json or [],
        evidences=report.evidences_json or [],
        generated_at=report.generated_at
    )


@router.get("/diagnosis/history", response_model=dict)
async def get_history(
    service: Optional[str] = None,
    limit: int = 10,
    repository: DiagnosisReportRepository = Depends()
):
    """查询历史记录"""
    if service:
        reports = await repository.find_by_service(service, limit)
    else:
        reports = await repository.find_high_confidence_reports()
    
    items = [
        {
            "diagnosis_id": r.diagnosis_id,
            "target_service": r.target_service,
            "primary_problem_type": r.primary_problem_type,
            "confidence": r.confidence,
            "generated_at": r.generated_at
        }
        for r in reports
    ]
    
    return {
        "total": len(items),
        "items": items
    }
```

---

## 11. 前端设计

### 11.1 页面结构

```
├── Dashboard (仪表盘)
│   ├── 服务健康状态
│   ├── 实时告警
│   └── 最近诊断记录
│
├── Diagnosis (诊断详情)
│   ├── 诊断概览
│   ├── 根因分析
│   ├── 证据链展示
│   │   ├── 指标趋势图 (ECharts)
│   │   ├── 日志片段
│   │   └── 链路火焰图
│   └── 修复建议
│
├── History (历史记录)
│   ├── 诊断列表
│   ├── 筛选（服务/问题类型/时间范围）
│   └── 趋势统计
│
└── Config (配置管理)
    ├── 数据源配置 (Prometheus/Loki/Tempo)
    ├── LLM 配置
    └── 告警规则
```

### 11.2 核心组件

**诊断触发按钮**:
```vue
<template>
  <el-button type="primary" @click="triggerDiagnosis">
    <el-icon><VideoPlay /></el-icon>
    立即诊断
  </el-button>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { diagnosisApi } from '@/api/diagnosis'

const triggerDiagnosis = async () => {
  try {
    const res = await diagnosisApi.trigger({
      targetService: 'target-app',
      startTime: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      endTime: new Date().toISOString()
    })
    
    ElMessage.success(`诊断已触发: ${res.diagnosisId}`)
    
    // 跳转到诊断详情页
    router.push(`/diagnosis/${res.diagnosisId}`)
  } catch (error) {
    ElMessage.error('诊断触发失败')
  }
}
</script>
```

**指标趋势图**:
```vue
<template>
  <div ref="chartRef" style="width: 100%; height: 400px;"></div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  data: Array<{ timestamp: string; value: number }>
}>()

const chartRef = ref<HTMLDivElement>()

onMounted(() => {
  const chart = echarts.init(chartRef.value!)
  
  chart.setOption({
    title: { text: 'JVM 内存使用率' },
    xAxis: {
      type: 'time',
      data: props.data.map(d => d.timestamp)
    },
    yAxis: { type: 'value' },
    series: [{
      type: 'line',
      data: props.data.map(d => d.value),
      smooth: true
    }]
  })
})
</script>
```

---

## 12. 配置文件

### 12.1 config.py

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    app_name: str = "aiops-agent"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8081
    
    # 数据库配置
    database_url: str = "postgresql+asyncpg://aiops:aiops123@postgres:5432/aiops"
    database_echo: bool = False
    database_pool_size: int = 20
    database_max_overflow: int = 10
    
    # Redis 配置
    redis_url: str = "redis://redis:6379/0"
    redis_decode_responses: bool = True
    
    # Kafka 配置
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_group_id: str = "aiops-agent"
    kafka_auto_offset_reset: str = "earliest"
    
    # 可观测数据源配置
    prometheus_url: str = "http://prometheus:9090"
    loki_url: str = "http://loki:3100"
    tempo_url: str = "http://tempo:3200"
    
    # LLM 配置
    llm_provider: str = "qwen"  # qwen, deepseek, openai
    
    # 通义千问配置
    qwen_api_key: str = ""
    qwen_model: str = "qwen-max"
    qwen_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    
    # DeepSeek 配置
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    
    # OpenAI 配置
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_base_url: str = "https://api.openai.com/v1"
    
    # 诊断配置
    diagnosis_default_time_window: int = 1800  # 30分钟，单位秒
    diagnosis_max_concurrent: int = 5
    diagnosis_timeout: int = 300  # 5分钟
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
```

### 12.2 requirements.txt

```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Async
httpx==0.25.1
aioredis==2.0.1
aiokafka==0.10.0

# Database
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0
alembic==1.12.1

# Redis
redis==5.0.1

# Kafka
kafka-python==2.0.2

# AI & ML
langgraph==0.2.0
langchain==0.1.0
langchain-openai==0.0.2
openai==1.3.7

# Data Processing
pandas==2.1.3
numpy==1.26.2
scikit-learn==1.3.2

# Monitoring Client
prometheus-client==0.19.0

# Utilities
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dateutil==2.8.2

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.1

# Development
black==23.11.0
flake8==6.1.0
mypy==1.7.1
isort==5.12.0
```

### 12.3 pyproject.toml

```toml
[tool.poetry]
name = "aiops-agent"
version = "1.0.0"
description = "AI-powered intelligent operations diagnosis platform"
authors = ["AIOps Team <aiops@example.com>"]
readme = "README.md"
python = "^3.11"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.1"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
sqlalchemy = {extras = ["asyncio"], version = "^2.0.23"}
asyncpg = "^0.29.0"
redis = "^5.0.1"
aiokafka = "^0.10.0"
langgraph = "^0.2.0"
langchain = "^0.1.0"
pandas = "^2.1.3"
numpy = "^1.26.2"
pydantic = "^2.5.0"
pydantic-settings = "^2.1.0"
httpx = "^0.25.1"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
pytest-cov = "^4.1.0"
black = "^23.11.0"
flake8 = "^6.1.0"
mypy = "^1.7.1"
isort = "^5.12.0"

[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 100

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

---

## 13. 部署配置

### 13.1 Dockerfile

```dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8081

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
```

### 13.2 docker-compose.yml 片段

```yaml
services:
  aiops-agent:
    build:
      context: ./aiops-agent
      dockerfile: Dockerfile
    container_name: aiops-agent
    ports:
      - "8081:8081"
    environment:
      - DEBUG=false
      - DATABASE_URL=postgresql+asyncpg://aiops:aiops123@postgres:5432/aiops
      - REDIS_URL=redis://redis:6379/0
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - PROMETHEUS_URL=http://prometheus:9090
      - LOKI_URL=http://loki:3100
      - TEMPO_URL=http://tempo:3200
      - QWEN_API_KEY=${QWEN_API_KEY}
      - LLM_PROVIDER=qwen
    depends_on:
      - postgres
      - redis
      - kafka
      - prometheus
      - loki
      - tempo
    networks:
      - aiops-network
    volumes:
      - ./aiops-agent:/app
    restart: unless-stopped
  
  postgres:
    image: postgres:15-alpine
    container_name: aiops-postgres
    environment:
      - POSTGRES_USER=aiops
      - POSTGRES_PASSWORD=aiops123
      - POSTGRES_DB=aiops
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - aiops-network
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  aiops-network:
    driver: bridge
```

### 13.3 .env.example

```bash
# Application
DEBUG=false
APP_NAME=aiops-agent

# Database
DATABASE_URL=postgresql+asyncpg://aiops:aiops123@localhost:5432/aiops

# Redis
REDIS_URL=redis://localhost:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Observability
PROMETHEUS_URL=http://localhost:9090
LOKI_URL=http://localhost:3100
TEMPO_URL=http://localhost:3200

# LLM
LLM_PROVIDER=qwen
QWEN_API_KEY=your_qwen_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Diagnosis
DIAGNOSIS_DEFAULT_TIME_WINDOW=1800
DIAGNOSIS_MAX_CONCURRENT=5
```

---

## 14. 测试验证方案

### 14.1 单元测试

```python
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from engine.agents.metric_agent import MetricAgent, MetricAnomaly
from collector.prometheus.client import PrometheusClient, MetricPoint
from detector.metric.anomaly_detector import AnomalyDetector
from analyzer.llm.llm_service import LLMService


@pytest.mark.asyncio
async def test_memory_leak_detection():
    """测试内存泄漏检测"""
    # Mock 依赖
    prometheus_client = AsyncMock(spec=PrometheusClient)
    anomaly_detector = AsyncMock(spec=AnomalyDetector)
    llm_service = AsyncMock(spec=LLMService)
    
    # 模拟内存持续增长的指标
    now = datetime.now()
    points = [
        MetricPoint(timestamp=now - timedelta(seconds=300), value=500_000_000),
        MetricPoint(timestamp=now - timedelta(seconds=240), value=600_000_000),
        MetricPoint(timestamp=now - timedelta(seconds=180), value=700_000_000),
        MetricPoint(timestamp=now - timedelta(seconds=120), value=800_000_000),
        MetricPoint(timestamp=now - timedelta(seconds=60), value=900_000_000),
        MetricPoint(timestamp=now, value=1_000_000_000),
    ]
    
    prometheus_client.query_range.return_value = points
    
    # Mock 异常检测
    anomaly = MetricAnomaly(
        metric_name="jvm_memory_used",
        anomaly_type="STEADY_INCREASE",
        current_value=1_000_000_000,
        baseline=500_000_000,
        deviation=1.0,
        detected_at=now
    )
    anomaly_detector.detect.return_value = anomaly
    
    # 创建 Agent
    agent = MetricAgent(prometheus_client, anomaly_detector, llm_service)
    
    # 执行分析
    state = {
        "target_service": "target-app",
        "start_time": now - timedelta(seconds=300),
        "end_time": now,
        "metric_anomalies": []
    }
    
    result = await agent.analyze(state)
    
    # 验证
    assert len(result["metric_anomalies"]) > 0
    assert result["metric_anomalies"][0]["metric_name"] == "jvm_memory_used"
    assert result["metric_anomalies"][0]["anomaly_type"] == "STEADY_INCREASE"


@pytest.mark.asyncio
async def test_threshold_detector():
    """测试阈值检测器"""
    from detector.metric.threshold_detector import ThresholdDetector
    
    detector = ThresholdDetector()
    
    # 测试CPU超过阈值
    now = datetime.now()
    points = [
        MetricPoint(timestamp=now - timedelta(seconds=i*30), value=0.85)
        for i in range(5)
    ]
    
    anomaly = await detector.detect("process_cpu_usage", points)
    
    assert anomaly is not None
    assert anomaly.metric_name == "process_cpu_usage"
    assert anomaly.current_value > 0.8
```

### 14.2 集成测试

```python
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from app.main import app
from storage.database import get_db


@pytest.mark.asyncio
async def test_full_diagnosis_flow():
    """测试完整诊断流程"""
    
    # 启动测试容器
    with PostgresContainer("postgres:15-alpine") as postgres, \
         RedisContainer("redis:7-alpine") as redis:
        
        # 配置测试数据库
        db_url = postgres.get_connection_url()
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 1. 触发诊断
            now = datetime.now()
            request_data = {
                "target_service": "target-app",
                "start_time": (now - timedelta(minutes=30)).isoformat(),
                "end_time": now.isoformat()
            }
            
            response = await client.post("/api/diagnosis/trigger", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            diagnosis_id = data["diagnosis_id"]
            
            # 2. 等待诊断完成（轮询）
            import asyncio
            max_retries = 60
            for _ in range(max_retries):
                response = await client.get(f"/api/diagnosis/{diagnosis_id}")
                
                if response.status_code == 200:
                    report = response.json()
                    if report["status"] == "completed":
                        break
                
                await asyncio.sleep(1)
            
            # 3. 验证报告
            assert report["status"] == "completed"
            assert len(report["root_causes"]) > 0
            assert report["confidence"] > 0.7
            assert report["primary_problem_type"] is not None


@pytest.mark.asyncio
async def test_api_endpoints():
    """测试 API 端点"""
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 健康检查
        response = await client.get("/health")
        assert response.status_code == 200
        
        # 查询历史记录
        response = await client.get(
            "/api/diagnosis/history",
            params={"service": "target-app", "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
```

### 14.3 性能测试

```python
import pytest
import asyncio
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_concurrent_diagnosis():
    """测试并发诊断"""
    from engine.orchestrator.diagnosis_orchestrator import DiagnosisOrchestrator
    
    orchestrator = DiagnosisOrchestrator()
    
    # 创建 10 个并发诊断任务
    now = datetime.now()
    tasks = []
    
    for i in range(10):
        state = {
            "diagnosis_id": f"test-{i}",
            "target_service": "target-app",
            "start_time": now - timedelta(minutes=30),
            "end_time": now,
            "status": "init"
        }
        
        task = orchestrator.diagnose(state)
        tasks.append(task)
    
    # 并发执行
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 验证所有任务完成
    assert len(results) == 10
    
    # 统计成功率
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    assert success_count >= 8  # 至少 80% 成功率
```

---

## 15. 性能优化

### 15.1 并行化

```python
import asyncio
from typing import List, Coroutine, Any


async def parallel_execute(tasks: List[Coroutine]) -> List[Any]:
    """并行执行任务"""
    return await asyncio.gather(*tasks, return_exceptions=True)


# 在 Agent 中使用
async def collect_data_parallel(state: dict):
    """并行采集数据"""
    tasks = [
        metric_agent.analyze(state),
        log_agent.analyze(state),
        trace_agent.analyze(state)
    ]
    
    results = await parallel_execute(tasks)
    
    return results
```

### 15.2 缓存策略

```python
from functools import lru_cache
from datetime import timedelta

from storage.cache.redis_service import RedisService


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service
    
    async def cache_baseline(
        self,
        metric_name: str,
        value: float,
        ttl: int = 3600
    ):
        """缓存基线数据（TTL 1小时）"""
        key = f"baseline:{metric_name}"
        await self.redis.set(key, value, ex=ttl)
    
    async def cache_report(
        self,
        diagnosis_id: str,
        report: dict,
        ttl: int = 86400
    ):
        """缓存诊断报告（TTL 24小时）"""
        key = f"report:{diagnosis_id}"
        await self.redis.set(key, report, ex=ttl)
    
    async def get_cached_baseline(
        self,
        metric_name: str
    ) -> Optional[float]:
        """获取缓存的基线"""
        key = f"baseline:{metric_name}"
        value = await self.redis.get(key)
        
        return float(value) if value else None
```

### 15.3 限流保护

```python
import asyncio
from typing import Optional


class DiagnosisRateLimiter:
    """诊断限流器"""
    
    def __init__(self, max_concurrent: int = 5):
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def acquire(self, timeout: Optional[float] = None):
        """获取许可"""
        try:
            async with asyncio.timeout(timeout) if timeout else asyncio.nullcontext():
                await self.semaphore.acquire()
                return True
        except asyncio.TimeoutError:
            return False
    
    def release(self):
        """释放许可"""
        self.semaphore.release()
    
    async def __aenter__(self):
        await self.semaphore.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.semaphore.release()


# 使用示例
limiter = DiagnosisRateLimiter(max_concurrent=5)

async def diagnose_with_limit(state: dict):
    """带限流的诊断"""
    async with limiter:
        return await orchestrator.diagnose(state)
```

---

## 16. 监控和可观测性

### 16.1 Agent 自身指标

```python
from prometheus_client import Counter, Histogram, Gauge
import time


# 定义指标
diagnosis_total = Counter(
    'diagnosis_total',
    'Total number of diagnoses',
    ['service', 'status']
)

diagnosis_duration = Histogram(
    'diagnosis_duration_seconds',
    'Diagnosis duration in seconds',
    ['service']
)

diagnosis_success_rate = Gauge(
    'diagnosis_success_rate',
    'Diagnosis success rate',
    ['service']
)

llm_call_total = Counter(
    'llm_call_total',
    'Total number of LLM calls',
    ['provider', 'model']
)

llm_call_duration = Histogram(
    'llm_call_duration_seconds',
    'LLM call duration in seconds',
    ['provider', 'model']
)


# 使用示例
async def diagnose_with_metrics(state: dict):
    """带指标记录的诊断"""
    service = state['target_service']
    start_time = time.time()
    
    try:
        result = await orchestrator.diagnose(state)
        
        # 记录成功
        diagnosis_total.labels(service=service, status='success').inc()
        
        return result
    
    except Exception as e:
        # 记录失败
        diagnosis_total.labels(service=service, status='failed').inc()
        raise
    
    finally:
        # 记录耗时
        duration = time.time() - start_time
        diagnosis_duration.labels(service=service).observe(duration)
```

### 16.2 暴露 Prometheus 指标

```python
from fastapi import FastAPI
from prometheus_client import make_asgi_app


# 在 FastAPI 应用中挂载 Prometheus 指标端点
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

**关键指标**:
- `diagnosis_total` - 诊断总次数
- `diagnosis_duration_seconds` - 诊断耗时
- `diagnosis_success_rate` - 诊断成功率
- `llm_call_total` - LLM 调用次数
- `llm_call_duration_seconds` - LLM 响应时间

---

## 17. 安全设计

### 17.1 访问控制

- API 鉴权：Spring Security + JWT
- 数据源访问：只读权限
- 敏感数据脱敏：日志中隐藏 API Key

### 17.2 数据隔离

- 多租户支持：按 targetService 隔离
- 报告权限：只能查看自己服务的报告

---

## 18. 开发优先级

### P0（MVP）
- ✅ 数据采集（Prometheus/Loki/Tempo 客户端）
- ✅ 基础 Agent（Metric/Log/Trace）
- ✅ 简单 RCA（规则引擎）
- ✅ 手动触发诊断 API
- ✅ 报告存储

### P1（AI 增强）
- ✅ LLM 集成（Qwen）
- ✅ RCA Agent（多源证据综合分析）
- ✅ 前端诊断详情页

### P2（自动化）
- ✅ Prometheus 告警监听
- ✅ 自动触发诊断
- ✅ Kafka 异步处理

### P3（优化）
- ✅ 基于动态基线的异常检测
- ✅ WebSocket 实时推送
- ✅ 历史趋势分析

---

## 19. 交付物

1. **源代码**: 完整的 Python/FastAPI 项目（模块化结构）
2. **配置文件**: config.py、requirements.txt、pyproject.toml、docker-compose.yml、.env.example
3. **前端项目**: Vue 3 诊断控制台
4. **API 文档**: OpenAPI/Swagger 自动生成
5. **部署文档**: Docker 部署说明、依赖安装指南
6. **测试报告**: pytest 单元测试 + 集成测试覆盖率
7. **迁移脚本**: Alembic 数据库迁移文件

## 20. Python 生态技术栈总结

### 核心框架
- **FastAPI**: 现代化异步 Web 框架，自动生成 API 文档
- **SQLAlchemy 2.0**: 异步 ORM，支持 PostgreSQL
- **Pydantic**: 数据验证和序列化

### AI/ML 框架
- **LangGraph**: Agent 编排和状态管理
- **LangChain**: LLM 应用开发框架
- **pandas/numpy**: 数据处理和分析
- **scikit-learn**: 异常检测算法

### 异步生态
- **asyncio**: Python 原生异步框架
- **httpx**: 异步 HTTP 客户端
- **aioredis**: 异步 Redis 客户端
- **aiokafka**: 异步 Kafka 客户端
- **asyncpg**: 异步 PostgreSQL 驱动

### 优势对比 Java 方案
1. **开发效率**: Python 代码简洁，开发速度快
2. **AI 生态**: 丰富的机器学习库和 LLM 集成
3. **异步性能**: asyncio 提供高效的异步 I/O
4. **数据处理**: pandas/numpy 强大的数据分析能力
5. **社区活跃**: AI/ML 领域第一选择

### 性能考虑
- 使用 uvicorn 作为 ASGI 服务器
- 异步 I/O 处理高并发
- Redis 缓存减少重复计算
- Kafka 异步解耦诊断流程
- 连接池复用数据库连接

---

**设计版本**: v1.0  
**最后更新**: 2026-11-11  
**负责人**: AIOps Team
