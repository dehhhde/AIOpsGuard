"""WebSocket 路由"""

from typing import Dict

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """WebSocket 连接管理器
    
    管理所有活跃的 WebSocket 连接，支持：
    - 连接注册与断开
    - 单播（发送给特定会话）
    - 广播（发送给所有连接）
    """

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """接受连接"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info("websocket_connected", session_id=session_id)

    def disconnect(self, session_id: str) -> None:
        """断开连接"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info("websocket_disconnected", session_id=session_id)

    async def send_progress(self, session_id: str, data: dict) -> None:
        """发送进度更新
        
        Args:
            session_id: 诊断会话 ID
            data: 进度数据
        """
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(data)
                logger.debug("websocket_progress_sent", session_id=session_id)
            except Exception as e:
                logger.error(
                    "websocket_send_failed", session_id=session_id, error=str(e)
                )
                self.disconnect(session_id)

    async def broadcast(self, data: dict) -> None:
        """广播消息到所有连接"""
        disconnected = []
        for session_id, connection in self.active_connections.items():
            try:
                await connection.send_json(data)
            except Exception:
                disconnected.append(session_id)

        # 清理断开的连接
        for session_id in disconnected:
            self.disconnect(session_id)


# 全局连接管理器
manager = ConnectionManager()


@router.websocket("/ws/diagnosis/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket 端点：实时推送诊断进度
    
    消息格式：
    - 客户端 -> 服务端：{"type": "ping"}
    - 服务端 -> 客户端：
      - {"type": "pong", "timestamp": "..."}
      - {"type": "progress", "stage": "...", "progress": 50}
      - {"type": "completed", "session_id": "..."}
      - {"type": "error", "message": "..."}
    """
    await manager.connect(session_id, websocket)

    try:
        # 发送欢迎消息
        await websocket.send_json(
            {
                "type": "connected",
                "session_id": session_id,
                "message": "WebSocket connection established",
            }
        )

        while True:
            # 接收消息
            data = await websocket.receive_json()

            # 处理 ping
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong", "session_id": session_id})

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error("websocket_error", session_id=session_id, error=str(e))
        manager.disconnect(session_id)
