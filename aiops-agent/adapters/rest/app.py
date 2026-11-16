"""FastAPI 应用"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from adapters.rest.middleware.cors import setup_cors
from adapters.rest.middleware.error_handler import setup_error_handlers
from adapters.rest.routes import diagnosis, health
from application.container import container
from config.settings import settings

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时初始化容器
    logger.info("app_startup_start")
    await container.init()
    logger.info("app_startup_completed")

    yield

    # 关闭时清理资源
    logger.info("app_shutdown_start")
    await container.close()
    logger.info("app_shutdown_completed")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="AIOps Diagnosis Agent API",
        description="智能诊断服务 API - 基于 LangGraph 多 Agent 协同诊断",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # 设置 CORS
    setup_cors(app)

    # 设置错误处理
    setup_error_handlers(app)

    # 注册路由
    app.include_router(health.router)
    app.include_router(diagnosis.router)
    
    # 注册 WebSocket 路由
    from adapters.rest.routes import websocket
    app.include_router(websocket.router)

    logger.info("fastapi_app_created", title=app.title, version=app.version)

    return app


app = create_app()
