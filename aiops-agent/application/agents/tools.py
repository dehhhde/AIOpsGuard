"""Agent 工具集"""

import json
from datetime import datetime
from typing import Any, Dict, List

import structlog

from config.settings import settings
from infrastructure.external.loki_client import LokiClient
from infrastructure.external.mock_data import MockDataGenerator
from infrastructure.external.prometheus_client import PrometheusClient
from infrastructure.external.tempo_client import TempoClient

logger = structlog.get_logger(__name__)


class AgentTools:
    """Agent 工具集

    为 Agent 提供查询外部数据源的能力
    支持测试模式（使用 Mock 数据）
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
        self.mock_generator = MockDataGenerator()

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
        # 测试模式：使用 Mock 数据
        if settings.test_mode:
            logger.info(
                "test_mode_mock_metrics",
                service_name=service_name,
                message="Using mock Prometheus data",
            )
            mock_data = self.mock_generator.generate_prometheus_metrics(
                service_name, start_time, end_time
            )
            return json.dumps(mock_data, indent=2, default=str)

        # 正常模式：查询真实数据
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
        # 测试模式：使用 Mock 数据
        if settings.test_mode:
            logger.info(
                "test_mode_mock_logs",
                service_name=service_name,
                message="Using mock Loki data",
            )
            mock_data = self.mock_generator.generate_loki_logs(
                service_name, start_time, end_time
            )
            return json.dumps(mock_data, indent=2, default=str)

        # 正常模式：查询真实数据
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
        # 测试模式：使用 Mock 数据
        if settings.test_mode:
            logger.info(
                "test_mode_mock_traces",
                service_name=service_name,
                message="Using mock Tempo data",
            )
            mock_data = self.mock_generator.generate_tempo_traces(
                service_name, start_time, end_time
            )
            return json.dumps(mock_data, indent=2, default=str)

        # 正常模式：查询真实数据
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
