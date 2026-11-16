"""健康检查聚合器"""
from dataclasses import dataclass, field
from typing import Any
import structlog

from .prometheus_client import PrometheusClient
from .loki_client import LokiClient
from .tempo_client import TempoClient
from config.settings import settings

logger = structlog.get_logger(__name__)


@dataclass
class HealthStatus:
    """健康状态
    
    Attributes:
        is_healthy: 整体是否健康
        details: 各个服务的详细健康状态
    """
    is_healthy: bool
    details: dict[str, dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "is_healthy": self.is_healthy,
            "details": self.details
        }


class HealthChecker:
    """健康检查聚合器
    
    职责：检查所有外部依赖的健康状态
    
    使用示例：
        >>> checker = HealthChecker()
        >>> status = await checker.check_all()
        >>> if status.is_healthy:
        ...     print("All systems healthy")
    """
    
    async def check_all(self) -> HealthStatus:
        """检查所有外部服务
        
        Returns:
            HealthStatus: 聚合的健康状态
        """
        details = {}
        
        # 检查 Prometheus
        details["prometheus"] = await self._check_prometheus()
        
        # 检查 Loki
        details["loki"] = await self._check_loki()
        
        # 检查 Tempo
        details["tempo"] = await self._check_tempo()
        
        # 检查数据库
        details["database"] = self._check_database()
        
        # 检查 Redis
        details["redis"] = self._check_redis()
        
        # 检查 Kafka
        details["kafka"] = self._check_kafka()
        
        # 整体健康判断：至少核心服务可用或所有服务都可以禁用
        # 如果有启用的服务，至少一个必须健康
        enabled_services = [
            details[svc] for svc in details
            if details[svc].get("enabled", False)
        ]
        
        if not enabled_services:
            # 所有服务都禁用，认为健康（降级模式）
            is_healthy = True
            logger.info("all_services_disabled_degraded_mode")
        else:
            # 至少有一个启用的服务是健康的
            is_healthy = any(
                svc.get("status") == "healthy"
                for svc in enabled_services
            )
        
        logger.info(
            "health_check_completed",
            is_healthy=is_healthy,
            enabled_count=len(enabled_services)
        )
        
        return HealthStatus(is_healthy=is_healthy, details=details)
    
    async def _check_prometheus(self) -> dict[str, Any]:
        """检查 Prometheus"""
        if not settings.prometheus_enabled:
            return {"status": "disabled", "enabled": False}
        
        try:
            async with PrometheusClient() as client:
                health = await client.health()
                return {
                    "status": "healthy" if health["is_healthy"] else "unhealthy",
                    "enabled": True
                }
        except Exception as e:
            logger.error("prometheus_health_check_failed", error=str(e))
            return {"status": "unhealthy", "enabled": True, "error": str(e)}
    
    async def _check_loki(self) -> dict[str, Any]:
        """检查 Loki"""
        if not settings.loki_enabled:
            return {"status": "disabled", "enabled": False}
        
        try:
            async with LokiClient() as client:
                health = await client.health()
                return {
                    "status": "healthy" if health["is_healthy"] else "unhealthy",
                    "enabled": True
                }
        except Exception as e:
            logger.error("loki_health_check_failed", error=str(e))
            return {"status": "unhealthy", "enabled": True, "error": str(e)}
    
    async def _check_tempo(self) -> dict[str, Any]:
        """检查 Tempo"""
        if not settings.tempo_enabled:
            return {"status": "disabled", "enabled": False}
        
        try:
            async with TempoClient() as client:
                health = await client.health()
                return {
                    "status": "healthy" if health["is_healthy"] else "unhealthy",
                    "enabled": True
                }
        except Exception as e:
            logger.error("tempo_health_check_failed", error=str(e))
            return {"status": "unhealthy", "enabled": True, "error": str(e)}
    
    def _check_database(self) -> dict[str, Any]:
        """检查数据库"""
        if not settings.database_enabled:
            return {"status": "disabled", "enabled": False}
        
        # 简单检查：如果启用就认为配置正确
        # 实际连接测试在应用启动时进行
        return {"status": "configured", "enabled": True}
    
    def _check_redis(self) -> dict[str, Any]:
        """检查 Redis"""
        if not settings.redis_enabled:
            return {"status": "disabled", "enabled": False}
        
        return {"status": "configured", "enabled": True}
    
    def _check_kafka(self) -> dict[str, Any]:
        """检查 Kafka"""
        if not settings.kafka_enabled:
            return {"status": "disabled", "enabled": False}
        
        return {"status": "configured", "enabled": True}
    
    async def check_service(self, service_name: str) -> dict[str, Any]:
        """检查单个服务的健康状态
        
        Args:
            service_name: 服务名称（prometheus/loki/tempo/database/redis/kafka）
        
        Returns:
            该服务的健康状态
        """
        if service_name == "prometheus":
            return await self._check_prometheus()
        elif service_name == "loki":
            return await self._check_loki()
        elif service_name == "tempo":
            return await self._check_tempo()
        elif service_name == "database":
            return self._check_database()
        elif service_name == "redis":
            return self._check_redis()
        elif service_name == "kafka":
            return self._check_kafka()
        else:
            return {"status": "unknown", "enabled": False, "error": "Unknown service"}
