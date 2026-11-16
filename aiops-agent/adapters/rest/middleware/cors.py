"""CORS 配置"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI) -> None:
    """设置 CORS
    
    允许的来源：
    - http://localhost:5173 (Vite 开发服务器)
    - http://localhost:3000 (Next.js / React 开发服务器)
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:3000",
            "http://localhost:5174",  # Vite 备用端口
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
