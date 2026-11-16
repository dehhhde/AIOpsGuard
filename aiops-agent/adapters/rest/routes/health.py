"""健康检查路由"""

from fastapi import APIRouter

from config.settings import settings
from infrastructure.cache.redis_client import RedisClient
from infrastructure.external.prometheus_client import PrometheusClient
from infrastructure.llm.llm_client import LLMClient

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("/", summary="健康检查", description="检查服务是否正常运行")
async def health_check() -> dict:
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/ready", summary="就绪检查", description="检查服务是否就绪（依赖检查）")
async def readiness_check() -> dict:
    """就绪检查"""
    checks = {}

    # 检查 Prometheus
    if settings.prometheus_enabled:
        prometheus = PrometheusClient()
        checks["prometheus"] = await prometheus.health()

    # 检查 Redis（如果启用）
    if settings.redis_enabled:
        redis = RedisClient()
        checks["redis"] = await redis.ping()

    # 检查 LLM（如果启用）
    if settings.llm_enabled:
        llm = LLMClient()
        checks["llm"] = await llm.health()

    all_healthy = all(checks.values()) if checks else True

    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
    }
