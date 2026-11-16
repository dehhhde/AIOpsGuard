"""Prometheus 客户端"""
import httpx
from typing import Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

from config.settings import settings

logger = structlog.get_logger(__name__)


class PrometheusClient:
    """Prometheus 查询客户端
    
    职责：
    1. 即时查询（query）
    2. 范围查询（query_range）
    3. 序列查询（series）
    4. 健康检查
    
    特性：
    - 异步 HTTP 客户端
    - 自动重试（最多 3 次）
    - 超时控制
    - 连接池管理
    
    使用示例：
        >>> async with PrometheusClient() as client:
        ...     result = await client.query("up")
        ...     print(result["status"])  # "success"
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0
    ):
        """初始化客户端
        
        Args:
            base_url: Prometheus 地址，默认从配置读取
            timeout: 请求超时（秒）
        """
        self.base_url = base_url or settings.prometheus_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        
        logger.info(
            "prometheus_client_initialized",
            base_url=self.base_url,
            timeout=self.timeout
        )
    
    async def __aenter__(self):
        """上下文管理器入口"""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            limits=httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5
            )
        )
        logger.debug("prometheus_client_connected")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        if self._client:
            await self._client.aclose()
            logger.debug("prometheus_client_closed")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def query(
        self,
        query: str,
        time: Optional[str] = None
    ) -> dict[str, Any]:
        """即时查询
        
        执行 PromQL 查询，返回指定时间点的数据。
        
        Args:
            query: PromQL 查询表达式
            time: 查询时间（RFC3339 或 Unix 时间戳），默认当前时间
        
        Returns:
            查询结果字典，格式：
            {
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": [...]
                }
            }
        
        Raises:
            httpx.HTTPStatusError: HTTP 请求失败
            httpx.RequestError: 网络请求错误
        
        Examples:
            >>> async with PrometheusClient() as client:
            ...     # 查询所有实例的 up 状态
            ...     result = await client.query("up")
            ...     
            ...     # 查询特定时间点的 CPU 使用率
            ...     result = await client.query(
            ...         query="rate(cpu_usage[5m])",
            ...         time="2025-01-10T10:00:00Z"
            ...     )
        """
        params: dict[str, str] = {"query": query}
        if time:
            params["time"] = time
        
        logger.debug(
            "prometheus_query_start",
            query=query,
            time=time
        )
        
        try:
            response = await self._client.get("/api/v1/query", params=params)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(
                "prometheus_query_success",
                query=query,
                status=result.get("status")
            )
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "prometheus_query_http_error",
                query=query,
                status_code=e.response.status_code,
                error=str(e)
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                "prometheus_query_request_error",
                query=query,
                error=str(e)
            )
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def query_range(
        self,
        query: str,
        start: str,
        end: str,
        step: str = "15s"
    ) -> dict[str, Any]:
        """范围查询
        
        执行 PromQL 查询，返回时间范围内的数据。
        
        Args:
            query: PromQL 查询表达式
            start: 开始时间（RFC3339 或 Unix 时间戳）
            end: 结束时间（RFC3339 或 Unix 时间戳）
            step: 查询步长（如 15s, 1m, 5m）
        
        Returns:
            查询结果字典，格式：
            {
                "status": "success",
                "data": {
                    "resultType": "matrix",
                    "result": [...]
                }
            }
        
        Examples:
            >>> result = await client.query_range(
            ...     query="rate(requests_total[5m])",
            ...     start="2025-01-10T10:00:00Z",
            ...     end="2025-01-10T11:00:00Z",
            ...     step="1m"
            ... )
        """
        params = {
            "query": query,
            "start": start,
            "end": end,
            "step": step
        }
        
        logger.debug(
            "prometheus_query_range_start",
            query=query,
            start=start,
            end=end,
            step=step
        )
        
        try:
            response = await self._client.get("/api/v1/query_range", params=params)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(
                "prometheus_query_range_success",
                query=query,
                status=result.get("status"),
                result_count=len(result.get("data", {}).get("result", []))
            )
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "prometheus_query_range_http_error",
                query=query,
                status_code=e.response.status_code,
                error=str(e)
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                "prometheus_query_range_request_error",
                query=query,
                error=str(e)
            )
            raise
    
    async def series(
        self,
        match: list[str],
        start: Optional[str] = None,
        end: Optional[str] = None
    ) -> dict[str, Any]:
        """序列查询
        
        查询匹配的时间序列标签。
        
        Args:
            match: 匹配表达式列表（如 ["up", "process_cpu_seconds_total"]）
            start: 开始时间（可选）
            end: 结束时间（可选）
        
        Returns:
            序列列表，格式：
            {
                "status": "success",
                "data": [
                    {"__name__": "up", "job": "prometheus", ...},
                    ...
                ]
            }
        
        Examples:
            >>> result = await client.series(
            ...     match=["up", "process_cpu_seconds_total"],
            ...     start="2025-01-10T10:00:00Z"
            ... )
        """
        params: dict[str, Any] = {"match[]": match}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        
        logger.debug(
            "prometheus_series_start",
            match=match,
            start=start,
            end=end
        )
        
        try:
            response = await self._client.get("/api/v1/series", params=params)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(
                "prometheus_series_success",
                match=match,
                series_count=len(result.get("data", []))
            )
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "prometheus_series_http_error",
                match=match,
                status_code=e.response.status_code,
                error=str(e)
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                "prometheus_series_request_error",
                match=match,
                error=str(e)
            )
            raise
    
    async def health(self) -> dict[str, bool]:
        """健康检查
        
        检查 Prometheus 是否可访问。
        
        Returns:
            {"is_healthy": True/False}
        
        Examples:
            >>> health = await client.health()
            >>> if health["is_healthy"]:
            ...     print("Prometheus is healthy")
        """
        try:
            response = await self._client.get("/-/healthy")
            is_healthy = response.status_code == 200
            
            logger.info(
                "prometheus_health_check",
                is_healthy=is_healthy,
                status_code=response.status_code
            )
            
            return {"is_healthy": is_healthy}
            
        except Exception as e:
            logger.warning(
                "prometheus_health_check_failed",
                error=str(e)
            )
            return {"is_healthy": False}
    
    async def labels(self) -> dict[str, Any]:
        """获取所有标签名
        
        Returns:
            标签列表，格式：
            {
                "status": "success",
                "data": ["__name__", "job", "instance", ...]
            }
        """
        try:
            response = await self._client.get("/api/v1/labels")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("prometheus_labels_error", error=str(e))
            raise
    
    async def label_values(self, label: str) -> dict[str, Any]:
        """获取指定标签的所有值
        
        Args:
            label: 标签名（如 "job", "instance"）
        
        Returns:
            标签值列表，格式：
            {
                "status": "success",
                "data": ["prometheus", "node_exporter", ...]
            }
        """
        try:
            response = await self._client.get(f"/api/v1/label/{label}/values")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(
                "prometheus_label_values_error",
                label=label,
                error=str(e)
            )
            raise
