"""Loki 日志查询客户端"""
import httpx
from typing import Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

from config.settings import settings

logger = structlog.get_logger(__name__)


class LokiClient:
    """Loki 日志查询客户端
    
    职责：
    1. LogQL 范围查询
    2. 标签查询
    3. 健康检查
    
    特性：
    - 异步 HTTP 客户端
    - 自动重试
    - 支持禁用（降级）
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0
    ):
        """初始化客户端
        
        Args:
            base_url: Loki 地址，默认从配置读取
            timeout: 请求超时（秒）
        """
        self.base_url = base_url or settings.loki_url
        self.timeout = timeout
        self.enabled = settings.loki_enabled
        self._client: Optional[httpx.AsyncClient] = None
        
        if self.enabled:
            logger.info("loki_client_initialized", base_url=self.base_url)
        else:
            logger.info("loki_client_disabled")
    
    async def __aenter__(self):
        """上下文管理器入口"""
        if not self.enabled:
            logger.debug("loki_disabled_skip_connect")
            return self
        
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        )
        logger.debug("loki_client_connected")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        if self._client:
            await self._client.aclose()
            logger.debug("loki_client_closed")
    
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
        limit: int = 1000,
        direction: str = "backward"
    ) -> dict[str, Any]:
        """范围查询
        
        执行 LogQL 查询，返回时间范围内的日志。
        
        Args:
            query: LogQL 查询表达式
            start: 开始时间（纳秒时间戳或 RFC3339）
            end: 结束时间（纳秒时间戳或 RFC3339）
            limit: 返回日志条数限制
            direction: 查询方向（backward/forward）
        
        Returns:
            查询结果字典
        
        Examples:
            >>> async with LokiClient() as client:
            ...     result = await client.query_range(
            ...         query='{job="user-service"} |= "error"',
            ...         start="2025-01-10T10:00:00Z",
            ...         end="2025-01-10T11:00:00Z"
            ...     )
        """
        if not self.enabled or not self._client:
            logger.debug("loki_disabled_skip_query")
            return {"status": "disabled", "data": {"result": []}}
        
        params = {
            "query": query,
            "start": start,
            "end": end,
            "limit": limit,
            "direction": direction
        }
        
        logger.debug("loki_query_range_start", query=query)
        
        try:
            response = await self._client.get("/loki/api/v1/query_range", params=params)
            response.raise_for_status()
            
            result = response.json()
            
            result_count = len(result.get("data", {}).get("result", []))
            logger.info(
                "loki_query_range_success",
                query=query,
                result_count=result_count
            )
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "loki_query_range_http_error",
                query=query,
                status_code=e.response.status_code,
                error=str(e)
            )
            return {"status": "error", "error": str(e), "data": {"result": []}}
        except httpx.RequestError as e:
            logger.error(
                "loki_query_range_request_error",
                query=query,
                error=str(e)
            )
            return {"status": "error", "error": str(e), "data": {"result": []}}
    
    async def labels(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None
    ) -> dict[str, Any]:
        """获取标签列表
        
        Args:
            start: 开始时间（可选）
            end: 结束时间（可选）
        
        Returns:
            标签列表
        """
        if not self.enabled or not self._client:
            logger.debug("loki_disabled_skip_labels")
            return {"status": "disabled", "data": []}
        
        params = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        
        try:
            response = await self._client.get("/loki/api/v1/labels", params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.debug("loki_labels_success", count=len(result.get("data", [])))
            
            return result
            
        except Exception as e:
            logger.error("loki_labels_failed", error=str(e))
            return {"status": "error", "data": []}
    
    async def label_values(
        self,
        label: str,
        start: Optional[str] = None,
        end: Optional[str] = None
    ) -> dict[str, Any]:
        """获取指定标签的所有值
        
        Args:
            label: 标签名
            start: 开始时间（可选）
            end: 结束时间（可选）
        
        Returns:
            标签值列表
        """
        if not self.enabled or not self._client:
            return {"status": "disabled", "data": []}
        
        params = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        
        try:
            response = await self._client.get(
                f"/loki/api/v1/label/{label}/values",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("loki_label_values_failed", label=label, error=str(e))
            return {"status": "error", "data": []}
    
    async def health(self) -> dict[str, bool]:
        """健康检查
        
        Returns:
            {"is_healthy": True/False}
        """
        if not self.enabled:
            return {"is_healthy": False, "reason": "disabled"}
        
        try:
            if not self._client:
                # 临时创建客户端用于健康检查
                temp_client = httpx.AsyncClient(base_url=self.base_url, timeout=5.0)
                try:
                    response = await temp_client.get("/ready")
                    is_healthy = response.status_code == 200
                finally:
                    await temp_client.aclose()
            else:
                response = await self._client.get("/ready")
                is_healthy = response.status_code == 200
            
            logger.debug("loki_health_check", is_healthy=is_healthy)
            return {"is_healthy": is_healthy}
            
        except Exception as e:
            logger.warning("loki_health_check_failed", error=str(e))
            return {"is_healthy": False}
