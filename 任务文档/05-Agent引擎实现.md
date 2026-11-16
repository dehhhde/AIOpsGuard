# 阶段五：Agent 引擎实现

## 📋 任务概述

本阶段目标是实现基于 LangGraph 的多 Agent 协同诊断引擎，这是整个诊断服务的核心。

**预计时间**：5-7 天  
**优先级**：P0（必须完成）  
**依赖**：阶段二（领域模型）、阶段三（基础设施层）、阶段四（应用层）

---

## 🎯 核心目标

1. 实现 4 个专业 Agent（Metric、Log、Trace、RCA）
2. LangGraph 状态机与流转控制
3. LLM 客户端集成（OpenAI / Ollama）
4. Agent 工具集（查询外部数据源）
5. Prompt 模板管理
6. 错误处理与降级策略

---

## ✅ 任务清单

### 5.1 基础设施（3 个任务）

#### 5.1.1 LLM 客户端

**infrastructure/llm/llm_client.py**

```python
"""LLM 客户端"""
import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional

import structlog
from openai import AsyncOpenAI
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import settings

logger = structlog.get_logger(__name__)


class LLMClientError(Exception):
    """LLM 客户端错误"""
    pass


class LLMClient:
    """LLM 客户端
    
    支持：
    - OpenAI API（gpt-4, gpt-3.5-turbo）
    - Ollama 本地模型（兼容 OpenAI API）
    - 流式输出
    - 重试机制
    - 超时控制
    """
    
    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        self.enabled = settings.llm_enabled
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
    
    async def connect(self) -> None:
        """连接 LLM 服务"""
        if not self.enabled:
            logger.info("llm_disabled_skip_connect")
            return
        
        try:
            self.client = AsyncOpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                timeout=settings.llm_timeout,
            )
            logger.info(
                "llm_connected",
                model=self.model,
                base_url=settings.llm_base_url,
            )
        except Exception as e:
            logger.error("llm_connect_failed", error=str(e))
            raise LLMClientError(f"Failed to connect to LLM: {e}")
    
    async def close(self) -> None:
        """关闭连接"""
        if self.client:
            await self.client.close()
            logger.info("llm_closed")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """聊天补全（非流式）
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度（可选，默认使用配置）
            max_tokens: 最大 token 数（可选）
        
        Returns:
            LLM 响应内容
        
        Raises:
            LLMClientError: LLM 调用失败
        """
        if not self.enabled or not self.client:
            logger.warning("llm_disabled_return_placeholder")
            return "[LLM disabled] This is a placeholder response."
        
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=10),
                retry=retry_if_exception_type(Exception),
            ):
                with attempt:
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=temperature or self.temperature,
                        max_tokens=max_tokens or self.max_tokens,
                    )
                    
                    content = response.choices[0].message.content
                    
                    logger.info(
                        "llm_chat_completed",
                        model=self.model,
                        input_tokens=response.usage.prompt_tokens,
                        output_tokens=response.usage.completion_tokens,
                    )
                    
                    return content or ""
        
        except Exception as e:
            logger.error("llm_chat_failed", error=str(e), messages=messages)
            raise LLMClientError(f"LLM chat failed: {e}")
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
    ) -> AsyncIterator[str]:
        """聊天补全（流式输出）
        
        Args:
            messages: 消息列表
            temperature: 温度
        
        Yields:
            LLM 响应片段
        """
        if not self.enabled or not self.client:
            logger.warning("llm_disabled_stream_skipped")
            yield "[LLM disabled]"
            return
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            logger.error("llm_stream_failed", error=str(e))
            raise LLMClientError(f"LLM stream failed: {e}")
    
    async def health(self) -> bool:
        """健康检查"""
        if not self.enabled or not self.client:
            return False
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return bool(response.choices[0].message.content)
        except Exception as e:
            logger.warning("llm_health_check_failed", error=str(e))
            return False
```

**配置更新**：`config/settings.py`

```python
# LLM 配置
llm_enabled: bool = False
llm_provider: str = "openai"  # openai / ollama
llm_api_key: str = "sk-xxx"
llm_base_url: Optional[str] = None  # Ollama: http://localhost:11434/v1
llm_model: str = "gpt-4"
llm_temperature: float = 0.7
llm_max_tokens: int = 2000
llm_timeout: float = 60.0
```

#### 5.1.2 Prompt 模板管理器

**application/agents/prompts.py**

```python
"""Prompt 模板管理"""
from typing import Dict, List


class PromptTemplate:
    """Prompt 模板"""
    
    # Metric Agent 提示词
    METRIC_AGENT_SYSTEM = """你是一个专业的指标分析 Agent。

你的职责：
1. 分析 Prometheus 指标数据
2. 识别异常模式（突增、突降、抖动、超阈值）
3. 提取关键证据
4. 输出结构化分析结果

输出格式（JSON）：
{
  "anomalies": [
    {
      "metric": "指标名称",
      "pattern": "异常模式（spike/drop/fluctuation/threshold）",
      "severity": "严重程度（high/medium/low）",
      "summary": "简要描述",
      "timestamp": "异常时间点"
    }
  ],
  "evidence": [
    {
      "type": "METRIC",
      "source": "指标来源",
      "summary": "证据摘要",
      "detail": {}
    }
  ]
}

注意：只输出 JSON，不要其他内容。
"""
    
    METRIC_AGENT_USER = """请分析以下指标数据：

服务：{service_name}
时间范围：{time_range}

指标数据：
{metrics_data}

请识别异常并提取证据。
"""
    
    # Log Agent 提示词
    LOG_AGENT_SYSTEM = """你是一个专业的日志分析 Agent。

你的职责：
1. 分析应用日志
2. 识别错误、异常、警告
3. 提取关键错误信息和堆栈
4. 关联错误模式

输出格式（JSON）：
{
  "errors": [
    {
      "level": "ERROR/WARN",
      "message": "错误信息",
      "count": 出现次数,
      "first_seen": "首次出现时间",
      "last_seen": "最后出现时间",
      "stack_trace": "堆栈信息（可选）"
    }
  ],
  "evidence": [
    {
      "type": "LOG",
      "source": "日志来源",
      "summary": "证据摘要",
      "detail": {}
    }
  ]
}

注意：只输出 JSON，不要其他内容。
"""
    
    LOG_AGENT_USER = """请分析以下日志数据：

服务：{service_name}
时间范围：{time_range}

日志数据：
{logs_data}

请识别错误并提取证据。
"""
    
    # Trace Agent 提示词
    TRACE_AGENT_SYSTEM = """你是一个专业的链路追踪分析 Agent。

你的职责：
1. 分析分布式链路数据
2. 识别慢调用、超时、错误
3. 定位性能瓶颈
4. 分析依赖关系

输出格式（JSON）：
{
  "slow_spans": [
    {
      "span_name": "span 名称",
      "duration_ms": 耗时毫秒,
      "service": "所属服务",
      "summary": "描述"
    }
  ],
  "errors": [
    {
      "span_name": "span 名称",
      "error_message": "错误信息"
    }
  ],
  "evidence": [
    {
      "type": "TRACE",
      "source": "trace_id",
      "summary": "证据摘要",
      "detail": {}
    }
  ]
}

注意：只输出 JSON，不要其他内容。
"""
    
    TRACE_AGENT_USER = """请分析以下链路数据：

服务：{service_name}
时间范围：{time_range}

链路数据：
{traces_data}

请识别性能问题并提取证据。
"""
    
    # RCA Agent 提示词
    RCA_AGENT_SYSTEM = """你是一个专业的根因分析 Agent。

你的职责：
1. 综合分析指标、日志、链路证据
2. 推理根本原因
3. 给出置信度评分
4. 提供修复建议

输出格式（JSON）：
{
  "root_causes": [
    {
      "cause": "根因描述",
      "confidence": 置信度（0.0-1.0）,
      "evidence_ids": ["证据ID列表"],
      "reasoning": "推理过程",
      "recommendations": ["修复建议1", "修复建议2"]
    }
  ],
  "summary": "诊断总结"
}

注意：只输出 JSON，不要其他内容。
"""
    
    RCA_AGENT_USER = """请根据以下证据推理根本原因：

服务：{service_name}
时间范围：{time_range}

证据列表：
{evidence_list}

请分析根因并给出建议。
"""
    
    @classmethod
    def format_metric_agent_prompt(
        cls,
        service_name: str,
        time_range: str,
        metrics_data: str,
    ) -> List[Dict[str, str]]:
        """格式化 Metric Agent 提示词"""
        return [
            {"role": "system", "content": cls.METRIC_AGENT_SYSTEM},
            {
                "role": "user",
                "content": cls.METRIC_AGENT_USER.format(
                    service_name=service_name,
                    time_range=time_range,
                    metrics_data=metrics_data,
                ),
            },
        ]
    
    @classmethod
    def format_log_agent_prompt(
        cls,
        service_name: str,
        time_range: str,
        logs_data: str,
    ) -> List[Dict[str, str]]:
        """格式化 Log Agent 提示词"""
        return [
            {"role": "system", "content": cls.LOG_AGENT_SYSTEM},
            {
                "role": "user",
                "content": cls.LOG_AGENT_USER.format(
                    service_name=service_name,
                    time_range=time_range,
                    logs_data=logs_data,
                ),
            },
        ]
    
    @classmethod
    def format_trace_agent_prompt(
        cls,
        service_name: str,
        time_range: str,
        traces_data: str,
    ) -> List[Dict[str, str]]:
        """格式化 Trace Agent 提示词"""
        return [
            {"role": "system", "content": cls.TRACE_AGENT_SYSTEM},
            {
                "role": "user",
                "content": cls.TRACE_AGENT_USER.format(
                    service_name=service_name,
                    time_range=time_range,
                    traces_data=traces_data,
                ),
            },
        ]
    
    @classmethod
    def format_rca_agent_prompt(
        cls,
        service_name: str,
        time_range: str,
        evidence_list: str,
    ) -> List[Dict[str, str]]:
        """格式化 RCA Agent 提示词"""
        return [
            {"role": "system", "content": cls.RCA_AGENT_SYSTEM},
            {
                "role": "user",
                "content": cls.RCA_AGENT_USER.format(
                    service_name=service_name,
                    time_range=time_range,
                    evidence_list=evidence_list,
                ),
            },
        ]
```

#### 5.1.3 Agent 工具集

**application/agents/tools.py**

```python
"""Agent 工具集"""
import json
from datetime import datetime
from typing import Any, Dict, List

import structlog

from infrastructure.external.loki_client import LokiClient
from infrastructure.external.prometheus_client import PrometheusClient
from infrastructure.external.tempo_client import TempoClient

logger = structlog.get_logger(__name__)


class AgentTools:
    """Agent 工具集
    
    为 Agent 提供查询外部数据源的能力
    """
    
    def __init__(
        self,
        prometheus_client: PrometheusClient,
        loki_client: LokiClient,
        tempo_client: TempoClient,
    ):
        self.prometheus = prometheus_client
        self.loki = loki_client
        self.tempo = tempo_client
    
    async def query_metrics(
        self,
        service_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> str:
        """查询指标数据
        
        Returns:
            格式化的指标数据（JSON 字符串）
        """
        try:
            # 查询关键指标
            queries = {
                "cpu_usage": f'rate(process_cpu_seconds_total{{service="{service_name}"}}[5m])',
                "memory_usage": f'process_resident_memory_bytes{{service="{service_name}"}}',
                "request_rate": f'rate(http_requests_total{{service="{service_name}"}}[5m])',
                "error_rate": f'rate(http_requests_total{{service="{service_name}",status=~"5.."}}[5m])',
                "latency_p99": f'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{{service="{service_name}"}}[5m]))',
            }
            
            results = {}
            for name, query in queries.items():
                data = await self.prometheus.query_range(
                    query=query,
                    start=start_time,
                    end=end_time,
                    step="1m",
                )
                results[name] = data
            
            return json.dumps(results, indent=2, default=str)
        
        except Exception as e:
            logger.error("query_metrics_failed", error=str(e))
            return json.dumps({"error": str(e)})
    
    async def query_logs(
        self,
        service_name: str,
        start_time: datetime,
        end_time: datetime,
        level: str = "error",
    ) -> str:
        """查询日志数据
        
        Returns:
            格式化的日志数据（JSON 字符串）
        """
        try:
            query = f'{{service="{service_name}",level="{level}"}}'
            
            logs = await self.loki.query_range(
                query=query,
                start=start_time,
                end=end_time,
                limit=100,
            )
            
            return json.dumps(logs, indent=2, default=str)
        
        except Exception as e:
            logger.error("query_logs_failed", error=str(e))
            return json.dumps({"error": str(e)})
    
    async def query_traces(
        self,
        service_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> str:
        """查询链路数据
        
        Returns:
            格式化的链路数据（JSON 字符串）
        """
        try:
            traces = await self.tempo.search(
                service_name=service_name,
                start=start_time,
                end=end_time,
                limit=10,
            )
            
            return json.dumps(traces, indent=2, default=str)
        
        except Exception as e:
            logger.error("query_traces_failed", error=str(e))
            return json.dumps({"error": str(e)})
```

---

### 5.2 Agent 实现（4 个任务）

#### 5.2.1 Metric Agent

**application/agents/metric_agent.py**

```python
"""Metric Agent - 指标分析"""
import json
from datetime import datetime

import structlog

from application.agents.prompts import PromptTemplate
from application.agents.tools import AgentTools
from domain.enums import EvidenceType
from domain.models.evidence import Evidence
from domain.value_objects.time_range import TimeRange
from infrastructure.llm.llm_client import LLMClient

logger = structlog.get_logger(__name__)


class MetricAgent:
    """Metric Agent
    
    职责：
    1. 从 Prometheus 查询指标数据
    2. 使用 LLM 分析异常模式
    3. 提取指标证据
    """
    
    def __init__(self, llm_client: LLMClient, tools: AgentTools):
        self.llm = llm_client
        self.tools = tools
    
    async def analyze(
        self,
        service_name: str,
        time_range: TimeRange,
    ) -> list[Evidence]:
        """分析指标数据
        
        Args:
            service_name: 服务名称
            time_range: 时间范围
        
        Returns:
            证据列表
        """
        logger.info(
            "metric_agent_start",
            service_name=service_name,
            time_range=str(time_range),
        )
        
        # 1. 查询指标数据
        metrics_data = await self.tools.query_metrics(
            service_name=service_name,
            start_time=time_range.start_time,
            end_time=time_range.end_time,
        )
        
        # 2. 格式化 prompt
        messages = PromptTemplate.format_metric_agent_prompt(
            service_name=service_name,
            time_range=str(time_range),
            metrics_data=metrics_data,
        )
        
        # 3. 调用 LLM 分析
        try:
            response = await self.llm.chat(messages)
            analysis = json.loads(response)
            
            # 4. 转换为领域模型
            evidences = []
            for ev in analysis.get("evidence", []):
                evidence = Evidence(
                    type=EvidenceType.METRIC,
                    summary=ev["summary"],
                    source=ev["source"],
                    time_range=time_range,
                    detail=ev.get("detail", {}),
                )
                evidences.append(evidence)
            
            logger.info(
                "metric_agent_completed",
                service_name=service_name,
                evidence_count=len(evidences),
            )
            
            return evidences
        
        except Exception as e:
            logger.error("metric_agent_failed", error=str(e))
            return []
```

#### 5.2.2 Log Agent

**application/agents/log_agent.py**

（类似 MetricAgent，分析日志数据）

#### 5.2.3 Trace Agent

**application/agents/trace_agent.py**

（类似 MetricAgent，分析链路数据）

#### 5.2.4 RCA Agent

**application/agents/rca_agent.py**

（综合分析，推理根因）

---

### 5.3 LangGraph 编排（3 个任务）

#### 5.3.1 状态定义

**application/agents/diagnosis_state.py**

```python
"""诊断状态定义"""
from typing import Annotated, List, TypedDict

from domain.models.evidence import Evidence
from domain.models.root_cause import RootCause


class DiagnosisState(TypedDict):
    """诊断状态
    
    LangGraph 状态机的状态定义
    """
    
    # 输入
    service_name: str
    start_time: str
    end_time: str
    
    # 中间状态
    metric_evidences: Annotated[List[Evidence], "指标证据"]
    log_evidences: Annotated[List[Evidence], "日志证据"]
    trace_evidences: Annotated[List[Evidence], "链路证据"]
    
    # 输出
    root_causes: Annotated[List[RootCause], "根因列表"]
    summary: str
    
    # 错误
    error: str
```

#### 5.3.2 Graph 构建

**application/agents/diagnosis_graph.py**

```python
"""诊断 Graph"""
from langgraph.graph import StateGraph, END

from application.agents.diagnosis_state import DiagnosisState
from application.agents.metric_agent import MetricAgent
from application.agents.log_agent import LogAgent
from application.agents.trace_agent import TraceAgent
from application.agents.rca_agent import RCAAgent


def build_diagnosis_graph(
    metric_agent: MetricAgent,
    log_agent: LogAgent,
    trace_agent: TraceAgent,
    rca_agent: RCAAgent,
) -> StateGraph:
    """构建诊断 Graph"""
    
    # 定义节点
    async def metric_node(state: DiagnosisState) -> DiagnosisState:
        """Metric Agent 节点"""
        evidences = await metric_agent.analyze(...)
        state["metric_evidences"] = evidences
        return state
    
    async def log_node(state: DiagnosisState) -> DiagnosisState:
        """Log Agent 节点"""
        evidences = await log_agent.analyze(...)
        state["log_evidences"] = evidences
        return state
    
    async def trace_node(state: DiagnosisState) -> DiagnosisState:
        """Trace Agent 节点"""
        evidences = await trace_agent.analyze(...)
        state["trace_evidences"] = evidences
        return state
    
    async def rca_node(state: DiagnosisState) -> DiagnosisState:
        """RCA Agent 节点"""
        root_causes = await rca_agent.analyze(...)
        state["root_causes"] = root_causes
        return state
    
    # 构建 Graph
    workflow = StateGraph(DiagnosisState)
    
    # 添加节点
    workflow.add_node("metric_agent", metric_node)
    workflow.add_node("log_agent", log_node)
    workflow.add_node("trace_agent", trace_node)
    workflow.add_node("rca_agent", rca_node)
    
    # 定义边（并行执行 metric/log/trace，然后汇聚到 rca）
    workflow.set_entry_point("metric_agent")
    workflow.add_edge("metric_agent", "log_agent")
    workflow.add_edge("log_agent", "trace_agent")
    workflow.add_edge("trace_agent", "rca_agent")
    workflow.add_edge("rca_agent", END)
    
    return workflow.compile()
```

#### 5.3.3 诊断服务

**application/services/diagnosis_engine_service.py**

```python
"""诊断引擎服务"""
import structlog

from domain.models.diagnosis_session import DiagnosisSession
from application.agents.diagnosis_graph import build_diagnosis_graph

logger = structlog.get_logger(__name__)


class DiagnosisEngineService:
    """诊断引擎服务
    
    职责：
    1. 执行 LangGraph 诊断流程
    2. 更新诊断会话状态
    3. 持久化证据和根因
    """
    
    def __init__(self, graph):
        self.graph = graph
    
    async def run(self, session: DiagnosisSession) -> None:
        """运行诊断
        
        Args:
            session: 诊断会话
        """
        logger.info("diagnosis_engine_start", session_id=session.diagnosis_id)
        
        try:
            # 启动会话
            session.start()
            
            # 执行 LangGraph
            result = await self.graph.ainvoke({
                "service_name": session.service.service_name,
                "start_time": session.time_range.start_time.isoformat(),
                "end_time": session.time_range.end_time.isoformat(),
            })
            
            # 添加证据
            for evidence in result["metric_evidences"]:
                session.add_evidence(evidence)
            
            # 添加根因
            for root_cause in result["root_causes"]:
                session.add_root_cause(root_cause)
            
            # 生成报告
            # TODO: 报告生成
            
            # 完成诊断
            # session.complete(report)
            
            logger.info("diagnosis_engine_completed", session_id=session.diagnosis_id)
        
        except Exception as e:
            logger.error("diagnosis_engine_failed", session_id=session.diagnosis_id, error=str(e))
            session.fail(str(e))
```

---

### 5.4 集成与测试（3 个任务）

#### 5.4.1 集成到应用层

更新 `application/container.py`，初始化 LLM 客户端和诊断引擎。

#### 5.4.2 单元测试

- 测试各 Agent（Mock LLM 响应）
- 测试 Graph 流转

#### 5.4.3 集成测试

- 端到端诊断流程测试

---

## 📝 验收标准

### 功能验收
- [ ] LLM 客户端连接成功
- [ ] 4 个 Agent 能正确分析数据
- [ ] LangGraph 流转正确
- [ ] 证据和根因正确保存

### 代码质量
- [ ] 100% 类型标注
- [ ] Prompt 模板可维护
- [ ] 错误处理完整
- [ ] 日志埋点完整

### 性能要求
- [ ] 单次诊断耗时 < 60 秒
- [ ] LLM 调用有超时和重试

---

## 🚀 实施顺序

1. **基础设施**：LLM 客户端、Prompt 模板、工具集
2. **Agent 实现**：按顺序实现 4 个 Agent
3. **LangGraph 编排**：状态定义、Graph 构建、诊断服务
4. **集成测试**：端到端验证

---

**创建时间**：2025-01-10  
**预计完成**：阶段五完成后即可执行完整诊断流程
