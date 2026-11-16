"""健康检查路由"""
from fastapi import APIRouter

from config.settings import settings

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """服务健康检查"""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }
