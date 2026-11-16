"""Mock 数据生成器

用于在没有外部依赖时生成测试数据
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List


class MockDataGenerator:
    """Mock 数据生成器"""

    @staticmethod
    def generate_prometheus_metrics(
        service_name: str, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """生成模拟的 Prometheus 指标数据"""
        # 生成时间序列
        timestamps = []
        current = start_time
        while current <= end_time:
            timestamps.append(current.timestamp())
            current += timedelta(minutes=1)

        return {
            "cpu_usage": {
                "status": "success",
                "data": {
                    "resultType": "matrix",
                    "result": [
                        {
                            "metric": {
                                "service": service_name,
                                "instance": f"{service_name}-01",
                            },
                            "values": [
                                [ts, "0.75"]
                                for ts in timestamps[:30]  # 前30分钟正常
                            ]
                            + [
                                [ts, "0.95"]
                                for ts in timestamps[30:40]  # 中间10分钟突增
                            ]
                            + [
                                [ts, "0.70"]
                                for ts in timestamps[40:]  # 后续恢复
                            ],
                        }
                    ],
                },
            },
            "memory_usage": {
                "status": "success",
                "data": {
                    "resultType": "matrix",
                    "result": [
                        {
                            "metric": {
                                "service": service_name,
                                "instance": f"{service_name}-01",
                            },
                            "values": [
                                [ts, str(1000000000 + i * 10000000)]
                                for i, ts in enumerate(timestamps)  # 内存持续增长
                            ],
                        }
                    ],
                },
            },
            "request_rate": {
                "status": "success",
                "data": {
                    "resultType": "matrix",
                    "result": [
                        {
                            "metric": {
                                "service": service_name,
                                "instance": f"{service_name}-01",
                            },
                            "values": [[ts, "100.5"] for ts in timestamps],
                        }
                    ],
                },
            },
            "error_rate": {
                "status": "success",
                "data": {
                    "resultType": "matrix",
                    "result": [
                        {
                            "metric": {
                                "service": service_name,
                                "instance": f"{service_name}-01",
                                "status": "500",
                            },
                            "values": [
                                [ts, "0.5"]
                                for ts in timestamps[:35]  # 前35分钟低错误率
                            ]
                            + [
                                [ts, "15.0"]
                                for ts in timestamps[35:]  # 后续错误率突增
                            ],
                        }
                    ],
                },
            },
            "latency_p99": {
                "status": "success",
                "data": {
                    "resultType": "matrix",
                    "result": [
                        {
                            "metric": {
                                "service": service_name,
                                "instance": f"{service_name}-01",
                            },
                            "values": [
                                [ts, "0.15"]
                                for ts in timestamps[:30]  # 前30分钟正常延迟
                            ]
                            + [
                                [ts, "2.5"]
                                for ts in timestamps[30:45]  # 中间延迟飙升
                            ]
                            + [
                                [ts, "0.20"]
                                for ts in timestamps[45:]  # 后续恢复
                            ],
                        }
                    ],
                },
            },
        }

    @staticmethod
    def generate_loki_logs(
        service_name: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """生成模拟的 Loki 日志数据"""
        base_timestamp = int(start_time.timestamp() * 1_000_000_000)

        return [
            {
                "stream": {
                    "service": service_name,
                    "level": "error",
                    "pod": f"{service_name}-01",
                },
                "values": [
                    [
                        str(base_timestamp + i * 60_000_000_000),  # 每分钟一条
                        f"ERROR: OutOfMemoryError: Java heap space at line {100 + i}",
                    ]
                    for i in range(10)
                ],
            },
            {
                "stream": {
                    "service": service_name,
                    "level": "error",
                    "pod": f"{service_name}-01",
                },
                "values": [
                    [
                        str(base_timestamp + 35 * 60_000_000_000 + i * 10_000_000_000),
                        f"ERROR: java.sql.SQLException: Connection timeout after 30s",
                    ]
                    for i in range(5)
                ],
            },
            {
                "stream": {
                    "service": service_name,
                    "level": "warn",
                    "pod": f"{service_name}-01",
                },
                "values": [
                    [
                        str(base_timestamp + 30 * 60_000_000_000 + i * 5_000_000_000),
                        f"WARN: GC overhead limit exceeded, consider increasing heap size",
                    ]
                    for i in range(8)
                ],
            },
        ]

    @staticmethod
    def generate_tempo_traces(
        service_name: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """生成模拟的 Tempo 链路数据"""
        base_timestamp = int(start_time.timestamp() * 1_000_000)

        return [
            {
                "traceID": "trace-001-slow-request",
                "rootServiceName": service_name,
                "rootTraceName": "GET /api/users",
                "startTimeUnixNano": str(base_timestamp * 1000),
                "durationMs": 3500,  # 慢请求：3.5秒
                "spanSet": {
                    "spans": [
                        {
                            "spanID": "span-001",
                            "operationName": "GET /api/users",
                            "startTimeUnixNano": str(base_timestamp * 1000),
                            "durationNanos": "3500000000",
                            "attributes": [
                                {"key": "http.method", "value": "GET"},
                                {"key": "http.status_code", "value": 200},
                            ],
                        },
                        {
                            "spanID": "span-002",
                            "operationName": "SELECT * FROM users",
                            "startTimeUnixNano": str(base_timestamp * 1000 + 100000000),
                            "durationNanos": "3200000000",  # 数据库查询慢
                            "attributes": [
                                {"key": "db.system", "value": "postgresql"},
                                {
                                    "key": "db.statement",
                                    "value": "SELECT * FROM users WHERE status = 'active'",
                                },
                            ],
                        },
                    ]
                },
            },
            {
                "traceID": "trace-002-timeout",
                "rootServiceName": service_name,
                "rootTraceName": "POST /api/orders",
                "startTimeUnixNano": str((base_timestamp + 2000000) * 1000),
                "durationMs": 30500,  # 超时：30.5秒
                "spanSet": {
                    "spans": [
                        {
                            "spanID": "span-003",
                            "operationName": "POST /api/orders",
                            "startTimeUnixNano": str((base_timestamp + 2000000) * 1000),
                            "durationNanos": "30500000000",
                            "attributes": [
                                {"key": "http.method", "value": "POST"},
                                {"key": "http.status_code", "value": 500},
                                {"key": "error", "value": "true"},
                            ],
                        },
                        {
                            "spanID": "span-004",
                            "operationName": "payment-service.charge",
                            "startTimeUnixNano": str(
                                (base_timestamp + 2000000) * 1000 + 500000000
                            ),
                            "durationNanos": "30000000000",  # 支付服务超时
                            "attributes": [
                                {"key": "rpc.service", "value": "payment-service"},
                                {"key": "error", "value": "true"},
                                {
                                    "key": "error.message",
                                    "value": "Connection timeout",
                                },
                            ],
                        },
                    ]
                },
            },
        ]

    @staticmethod
    def generate_llm_metric_analysis(
        service_name: str, metrics_data: str
    ) -> Dict[str, Any]:
        """生成模拟的 LLM 指标分析结果"""
        return {
            "anomalies": [
                {
                    "metric": "cpu_usage",
                    "pattern": "spike",
                    "severity": "high",
                    "summary": "CPU 使用率在 30-40 分钟时段突增至 95%",
                    "timestamp": "2024-01-10T12:30:00Z",
                },
                {
                    "metric": "memory_usage",
                    "pattern": "continuous_growth",
                    "severity": "high",
                    "summary": "内存使用量持续增长，疑似内存泄漏",
                    "timestamp": "2024-01-10T12:00:00Z",
                },
                {
                    "metric": "latency_p99",
                    "pattern": "spike",
                    "severity": "medium",
                    "summary": "P99 延迟在 30-45 分钟时段从 150ms 飙升至 2.5s",
                    "timestamp": "2024-01-10T12:30:00Z",
                },
                {
                    "metric": "error_rate",
                    "pattern": "spike",
                    "severity": "high",
                    "summary": "错误率在 35 分钟后从 0.5% 突增至 15%",
                    "timestamp": "2024-01-10T12:35:00Z",
                },
            ],
            "evidence": [
                {
                    "type": "METRIC",
                    "source": "cpu_usage",
                    "summary": "CPU 使用率异常突增至 95%",
                    "detail": {
                        "peak_value": "95%",
                        "normal_baseline": "75%",
                        "duration": "10 minutes",
                    },
                },
                {
                    "type": "METRIC",
                    "source": "memory_usage",
                    "summary": "内存持续增长，疑似内存泄漏",
                    "detail": {
                        "growth_rate": "10MB/min",
                        "total_increase": "600MB",
                        "current_usage": "1.6GB",
                    },
                },
                {
                    "type": "METRIC",
                    "source": "latency_p99",
                    "summary": "P99 延迟飙升至 2.5 秒",
                    "detail": {
                        "peak_latency": "2.5s",
                        "normal_latency": "150ms",
                        "affected_period": "15 minutes",
                    },
                },
            ],
        }

    @staticmethod
    def generate_llm_log_analysis(service_name: str, logs_data: str) -> Dict[str, Any]:
        """生成模拟的 LLM 日志分析结果"""
        return {
            "errors": [
                {
                    "level": "ERROR",
                    "message": "OutOfMemoryError: Java heap space",
                    "count": 10,
                    "first_seen": "2024-01-10T12:00:00Z",
                    "last_seen": "2024-01-10T12:09:00Z",
                    "stack_trace": "at com.example.service.UserService.loadUsers(UserService.java:100)",
                },
                {
                    "level": "ERROR",
                    "message": "java.sql.SQLException: Connection timeout after 30s",
                    "count": 5,
                    "first_seen": "2024-01-10T12:35:00Z",
                    "last_seen": "2024-01-10T12:40:00Z",
                    "stack_trace": "at com.example.dao.UserDao.query(UserDao.java:50)",
                },
                {
                    "level": "WARN",
                    "message": "GC overhead limit exceeded, consider increasing heap size",
                    "count": 8,
                    "first_seen": "2024-01-10T12:30:00Z",
                    "last_seen": "2024-01-10T12:37:00Z",
                    "stack_trace": None,
                },
            ],
            "evidence": [
                {
                    "type": "LOG",
                    "source": "application-error-log",
                    "summary": "频繁出现 OutOfMemoryError，JVM 堆内存不足",
                    "detail": {
                        "error_type": "OutOfMemoryError",
                        "occurrence_count": 10,
                        "affected_class": "UserService",
                    },
                },
                {
                    "type": "LOG",
                    "source": "database-error-log",
                    "summary": "数据库连接超时，5 次连接失败",
                    "detail": {
                        "error_type": "SQLException",
                        "timeout_duration": "30s",
                        "occurrence_count": 5,
                    },
                },
            ],
        }

    @staticmethod
    def generate_llm_trace_analysis(
        service_name: str, traces_data: str
    ) -> Dict[str, Any]:
        """生成模拟的 LLM 链路分析结果"""
        return {
            "slow_spans": [
                {
                    "span_name": "SELECT * FROM users",
                    "duration_ms": 3200,
                    "service": service_name,
                    "summary": "数据库查询耗时 3.2 秒，远超正常水平",
                },
                {
                    "span_name": "payment-service.charge",
                    "duration_ms": 30000,
                    "service": "payment-service",
                    "summary": "支付服务调用超时 30 秒",
                },
            ],
            "errors": [
                {
                    "span_name": "POST /api/orders",
                    "error_message": "Connection timeout",
                }
            ],
            "evidence": [
                {
                    "type": "TRACE",
                    "source": "trace-001-slow-request",
                    "summary": "数据库查询慢导致请求耗时 3.5 秒",
                    "detail": {
                        "trace_id": "trace-001-slow-request",
                        "total_duration": "3.5s",
                        "slow_span": "SELECT * FROM users (3.2s)",
                    },
                },
                {
                    "type": "TRACE",
                    "source": "trace-002-timeout",
                    "summary": "支付服务超时导致订单创建失败",
                    "detail": {
                        "trace_id": "trace-002-timeout",
                        "total_duration": "30.5s",
                        "error_span": "payment-service.charge (30s timeout)",
                    },
                },
            ],
        }

    @staticmethod
    def generate_llm_rca_analysis(
        service_name: str, evidence_list: str
    ) -> Dict[str, Any]:
        """生成模拟的 LLM 根因分析结果"""
        return {
            "root_causes": [
                {
                    "cause": "JVM 堆内存不足导致频繁 Full GC 和 OutOfMemoryError",
                    "confidence": 0.92,
                    "evidence_ids": ["evidence-metric-memory", "evidence-log-oom"],
                    "reasoning": "内存持续增长且出现 OutOfMemoryError，同时有 GC overhead 警告，"
                    "明确指向内存泄漏或堆内存配置不足。",
                    "recommendations": [
                        "增加 JVM 堆内存配置（-Xmx）",
                        "使用 MAT 或 JProfiler 分析内存泄漏点",
                        "检查是否有大对象未释放",
                        "优化数据库查询，避免一次性加载大量数据",
                    ],
                },
                {
                    "cause": "数据库查询性能问题导致请求延迟和连接池耗尽",
                    "confidence": 0.85,
                    "evidence_ids": [
                        "evidence-trace-slow-query",
                        "evidence-log-connection-timeout",
                    ],
                    "reasoning": "链路追踪显示数据库查询耗时 3.2 秒，且出现连接超时错误，"
                    "说明数据库成为性能瓶颈。",
                    "recommendations": [
                        "优化慢 SQL 查询，添加索引",
                        "检查数据库连接池配置",
                        "考虑添加查询缓存（Redis）",
                        "分页查询替代全量查询",
                    ],
                },
                {
                    "cause": "支付服务不稳定导致订单创建失败",
                    "confidence": 0.75,
                    "evidence_ids": ["evidence-trace-payment-timeout"],
                    "reasoning": "链路追踪显示支付服务调用超时 30 秒，导致订单创建失败。",
                    "recommendations": [
                        "检查支付服务健康状态",
                        "添加支付服务熔断机制（Hystrix/Sentinel）",
                        "实现支付异步化，避免阻塞主流程",
                        "添加支付重试机制",
                    ],
                },
            ],
            "summary": "诊断完成，发现 3 个根因。主要问题是 JVM 内存不足（92% 置信度）和数据库性能问题（85% 置信度）。",
        }
