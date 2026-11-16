"""Tempo 链路追踪客户端"""
import httpx
from typing import Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

from config.settings import settings

logger = structlog.get_logger(__name__)


class TempoClient:
    """Tempo 链路追踪客户端
    
    职责：
    1. 根据 trace_id 查询链路
    2. 搜索链路
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
            base_url: Tempo 地址，默认从配置读取
            timeout: 请求超时（秒）
        """
        self.base_url = base_url or settings.tempo_url
        self.timeout = timeout
        self.enabled = settings.tempo_enabled
        self._client: Optional[httpx.AsyncClient] = None
        
        if self.enabled:
            logger.info("tempo_client_initialized", base_url=self.base_url)
        else:
            logger.info("tempo_client_disabled")
    
    async def __aenter__(self):
        """上下文管理器入口"""
        if not self.enabled:
            logger.debug("tempo_disabled_skip_connect")
            return self
        
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        )
        logger.debug("tempo_client_connected")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        if self._client:
            await self._client.aclose()
            logger.debug("tempo_client_closed")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def get_trace(self, trace_id: str) -> dict[str, Any]:
        """根据 trace_id 查询链路
        
        Args:
            trace_id: 链路 ID
        
        Returns:
            链路数据（OpenTelemetry Trace 格式）
        
        Examples:
            >>> async with TempoClient() as client:
            ...     trace = await client.get_trace("abc123def456")
        """
        if not self.enabled or not self._client:
            logger.debug("tempo_disabled_skip_get_trace")
            return {"status": "disabled", "trace": None}
        
        logger.debug("tempo_get_trace_start", trace_id=trace_id)
        
        try:
            response = await self._client.get(f"/api/traces/{trace_id}")
            response.raise_for_status()
            
            result = response.json()
            
            logger.info("tempo_get_trace_success", trace_id=trace_id)
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "tempo_get_trace_http_error",
                trace_id=trace_id,
                status_code=e.response.status_code,
                error=str(e)
            )
            return {"status": "error", "error": str(e), "trace": None}
        except httpx.RequestError as e:
            logger.error(
                "tempo_get_trace_request_error",
                trace_id=trace_id,
                error=str(e)
            )
            return {"status": "error", "error": str(e), "trace": None}
    
    async def search(
        self,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        min_duration: Optional[str] = None,
        max_duration: Optional[str] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        limit: int = 20
    ) -> dict[str, Any]:
        """搜索链路
        
        Args:
            service_name: 服务名（可选）
            operation_name: 操作名（可选）
            min_duration: 最小耗时，如 "100ms"（可选）
            max_duration: 最大耗时，如 "1s"（可选）
            start: 开始时间（Unix 时间戳，秒）（可选）
            end: 结束时间（Unix 时间戳，秒）（可选）
            limit: 返回条数限制
        
        Returns:
            链路列表
        
        Examples:
            >>> result = await client.search(
            ...     service_name="user-service",
            ...     min_duration="500ms",
            ...     limit=10
            ... )
        """
        if not self.enabled or not self._client:
            logger.debug("tempo_disabled_skip_search")
            return {"status": "disabled", "traces": []}
        
        params: dict[str, Any] = {"limit": limit}
        if service_name:
            params["service.name"] = service_name
        if operation_name:
            params["operation.name"] = operation_name
        if min_duration:
            params["minDuration"] = min_duration
        if max_duration:
            params["maxDuration"] = max_duration
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        
        logger.debug("tempo_search_start", params=params)
        
        try:
            response = await self._client.get("/api/search", params=params)
            response.raise_for_status()
            
            result = response.json()
            
            trace_count = len(result.get("traces", []))
            logger.info("tempo_search_success", trace_count=trace_count)
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "tempo_search_http_error",
                status_code=e.response.status_code,
                error=str(e)
            )
            return {"status": "error", "error": str(e), "traces": []}
        except httpx.RequestError as e:
            logger.error("tempo_search_request_error", error=str(e))
            return {"status": "error", "error": str(e), "traces": []}
    
    async def search_tags(self) -> dict[str, Any]:
        """获取可搜索的标签列表
        
        Returns:
            标签列表
        """
        if not self.enabled or not self._client:
            return {"status": "disabled", "tagNames": []}
        
        try:
            response = await self._client.get("/api/search/tags")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("tempo_search_tags_failed", error=str(e))
            return {"status": "error", "tagNames": []}
    
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
                    response = await temp_client.get("/status")
                    is_healthy = response.status_code == 200
                finally:
                    await temp_client.aclose()
            else:
                response = await self._client.get("/status")
                is_healthy = response.status_code == 200
            
            logger.debug("tempo_health_check", is_healthy=is_healthy)
            return {"is_healthy": is_healthy}
            
        except Exception as e:
            logger.warning("tempo_health_check_failed", error=str(e))
            return {"is_healthy": False}
