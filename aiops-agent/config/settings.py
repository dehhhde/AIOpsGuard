"""应用配置"""
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    app_name: str = "AIOps Diagnosis Agent"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # 测试模式（使用 Mock 数据，无需外部依赖）
    test_mode: bool = False

    # 数据库配置
    database_enabled: bool = False
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aiops"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_echo: bool = False

    # Redis 配置
    redis_enabled: bool = False
    redis_url: str = "redis://localhost:6379/0"
    redis_pool_size: int = 10
    redis_max_connections: int = 50

    # Prometheus 配置
    prometheus_enabled: bool = True  # Prometheus 已实现，默认启用
    prometheus_url: str = "http://localhost:9090"
    prometheus_timeout: int = 30

    # Loki 配置
    loki_enabled: bool = False
    loki_url: str = "http://localhost:3100"
    loki_timeout: int = 30

    # Tempo 配置
    tempo_enabled: bool = False
    tempo_url: str = "http://localhost:3200"
    tempo_timeout: int = 30

    # Kafka 配置
    kafka_enabled: bool = False
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_group_id: str = "aiops-agent"

    # LLM 配置
    llm_enabled: bool = False
    llm_provider: str = "openai"  # openai / ollama / qwen / deepseek
    llm_api_key: str = "sk-xxx"
    llm_base_url: Optional[str] = None  # Ollama: http://localhost:11434/v1
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    llm_timeout: float = 60.0
    llm_base_url: Optional[str] = None
    llm_model: str = "qwen-max"
    llm_timeout: int = 60

    # JWT 配置
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"  # json, text

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
