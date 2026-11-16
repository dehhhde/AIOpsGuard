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
