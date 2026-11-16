# 阶段六：API 层实现

## 📋 任务概述

本阶段目标是实现 REST + WebSocket API 层，对外提供诊断服务接口。

**预计时间**：3-4 天  
**优先级**：P0（必须完成）  
**依赖**：阶段四（应用层）、阶段五（Agent 引擎）

---

## 🎯 核心目标

1. 实现 REST API（诊断 CRUD）
2. 实现 WebSocket 实时推送（诊断进度）
3. 统一错误处理
4. API 文档（OpenAPI / Swagger）
5. CORS 配置
6. 健康检查完善

---

## ✅ 任务清单

### 6.1 REST API 实现（5 个任务）

#### 6.1.1 诊断路由

**adapters/rest/routes/diagnosis.py**

```python
"""诊断路由"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from application.container import container
from application.dto.requests import QueryDiagnosisRequest, TriggerDiagnosisRequest
from application.dto.responses import (
    DiagnosisReportResponse,
    DiagnosisSessionResponse,
    TriggerDiagnosisResponse,
)
from application.services.diagnosis_application_service import (
    DiagnosisApplicationService,
)
from application.use_cases.trigger_diagnosis_use_case import (
    DiagnosisAlreadyInProgressError,
)

router = APIRouter(prefix="/api/v1/diagnosis", tags=["diagnosis"])


def get_diagnosis_service() -> DiagnosisApplicationService:
    """获取诊断应用服务"""
    return container.diagnosis_service


@router.post(
    "/trigger",
    response_model=TriggerDiagnosisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="触发诊断",
    description="触发一次新的诊断任务，返回诊断会话 ID",
)
async def trigger_diagnosis(
    request: TriggerDiagnosisRequest,
    service: DiagnosisApplicationService = Depends(get_diagnosis_service),
) -> TriggerDiagnosisResponse:
    """触发诊断"""
    try:
        return await service.trigger_diagnosis(request)
    except DiagnosisAlreadyInProgressError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get(
    "/sessions",
    response_model=List[DiagnosisSessionResponse],
    summary="查询诊断会话",
    description="根据条件查询诊断会话列表",
)
async def query_diagnosis(
    session_id: str | None = None,
    service_name: str | None = None,
    status: str | None = None,
    limit: int = 10,
    service: DiagnosisApplicationService = Depends(get_diagnosis_service),
) -> List[DiagnosisSessionResponse]:
    """查询诊断会话"""
    request = QueryDiagnosisRequest(
        session_id=session_id,
        service_name=service_name,
        status=status,
        limit=limit,
    )
    return await service.query_diagnosis(request)


@router.get(
    "/sessions/{session_id}",
    response_model=DiagnosisSessionResponse,
    summary="获取诊断会话详情",
    description="根据会话 ID 获取诊断详情",
)
async def get_diagnosis_by_id(
    session_id: str,
    service: DiagnosisApplicationService = Depends(get_diagnosis_service),
) -> DiagnosisSessionResponse:
    """获取诊断会话详情"""
    result = await service.get_diagnosis_by_id(session_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnosis session {session_id} not found",
        )
    return result


@router.get(
    "/sessions/{session_id}/report",
    response_model=DiagnosisReportResponse,
    summary="获取诊断报告",
    description="获取完整的诊断报告（含证据和根因）",
)
async def get_diagnosis_report(
    session_id: str,
    service: DiagnosisApplicationService = Depends(get_diagnosis_service),
) -> DiagnosisReportResponse:
    """获取诊断报告"""
    try:
        return await service.get_diagnosis_report(session_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/sessions/{session_id}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="取消诊断",
    description="取消正在进行的诊断任务",
)
async def cancel_diagnosis(
    session_id: str,
    service: DiagnosisApplicationService = Depends(get_diagnosis_service),
) -> None:
    """取消诊断"""
    try:
        await service.cancel_diagnosis(session_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/sessions/{session_id}/retry",
    response_model=TriggerDiagnosisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="重新诊断",
    description="重新执行失败的诊断任务",
)
async def retry_diagnosis(
    session_id: str,
    service: DiagnosisApplicationService = Depends(get_diagnosis_service),
) -> TriggerDiagnosisResponse:
    """重新诊断"""
    try:
        return await service.retry_diagnosis(session_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
```

#### 6.1.2 健康检查路由

**adapters/rest/routes/health.py**

```python
"""健康检查路由"""
from fastapi import APIRouter

from infrastructure.cache.redis_client import RedisClient
from infrastructure.external.prometheus_client import PrometheusClient
from infrastructure.llm.llm_client import LLMClient

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("/", summary="健康检查", description="检查服务是否正常运行")
async def health_check() -> dict:
    """健康检查"""
    return {
        "status": "healthy",
        "service": "AIOps Diagnosis Agent",
        "version": "0.1.0",
    }


@router.get("/ready", summary="就绪检查", description="检查服务是否就绪（依赖检查）")
async def readiness_check() -> dict:
    """就绪检查"""
    checks = {}

    # 检查 Prometheus
    prometheus = PrometheusClient()
    checks["prometheus"] = await prometheus.health()

    # 检查 Redis（如果启用）
    redis = RedisClient()
    if redis.enabled:
        checks["redis"] = await redis.ping()

    # 检查 LLM（如果启用）
    llm = LLMClient()
    if llm.enabled:
        checks["llm"] = await llm.health()

    all_healthy = all(checks.values())

    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
    }
```

#### 6.1.3 错误处理

**adapters/rest/middleware/error_handler.py**

```python
"""统一错误处理"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


def setup_error_handlers(app: FastAPI) -> None:
    """设置错误处理器"""

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """处理 ValueError"""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "ValidationError", "detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """处理通用异常"""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "InternalServerError", "detail": "An unexpected error occurred"},
        )
```

#### 6.1.4 CORS 配置

**adapters/rest/middleware/cors.py**

```python
"""CORS 配置"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI) -> None:
    """设置 CORS"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],  # 开发环境
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

#### 6.1.5 FastAPI 应用

**adapters/rest/app.py**

```python
"""FastAPI 应用"""
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from adapters.rest.middleware.cors import setup_cors
from adapters.rest.middleware.error_handler import setup_error_handlers
from adapters.rest.routes import diagnosis, health
from application.container import container

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
        description="智能诊断服务 API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # 设置 CORS
    setup_cors(app)

    # 设置错误处理
    setup_error_handlers(app)

    # 注册路由
    app.include_router(health.router)
    app.include_router(diagnosis.router)

    return app


app = create_app()
```

---

### 6.2 WebSocket 实现（2 个任务）

#### 6.2.1 WebSocket 路由

**adapters/rest/routes/websocket.py**

```python
"""WebSocket 路由"""
import asyncio
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """接受连接"""
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        """断开连接"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_progress(self, session_id: str, data: dict):
        """发送进度更新"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(data)
            except Exception:
                self.disconnect(session_id)


manager = ConnectionManager()


@router.websocket("/ws/diagnosis/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket 端点：实时推送诊断进度"""
    await manager.connect(session_id, websocket)

    try:
        while True:
            # 保持连接
            data = await websocket.receive_text()

            # TODO: 根据消息类型处理
            # 目前只是回显
            await websocket.send_json(
                {"type": "pong", "session_id": session_id, "message": data}
            )

    except WebSocketDisconnect:
        manager.disconnect(session_id)
```

#### 6.2.2 WebSocket 集成

需要在诊断引擎中发送进度更新到 WebSocket。

---

### 6.3 主入口（1 个任务）

#### 6.3.1 主入口文件

**main.py**

```python
"""主入口文件"""
from adapters.rest.app import app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
```

---

## 📝 验收标准

### 功能验收
- [ ] 所有 REST 端点正常工作
- [ ] WebSocket 连接正常
- [ ] API 文档可访问（/docs）
- [ ] 错误处理正确
- [ ] CORS 配置正确

### 代码质量
- [ ] 100% 类型标注
- [ ] 统一错误处理
- [ ] 日志埋点完整

### 测试覆盖
- [ ] API 集成测试
- [ ] WebSocket 测试

---

## 🚀 实施顺序

1. **REST API**：路由定义、错误处理、CORS
2. **WebSocket**：连接管理、进度推送
3. **主入口**：FastAPI 应用、生命周期管理
4. **测试**：API 集成测试

---

**创建时间**：2025-01-10  
**预计完成**：阶段六完成后即可部署上线
