"""数据库连接管理"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
from typing import Optional, Any
import structlog

from config.settings import settings

logger = structlog.get_logger(__name__)

# 声明基类
Base = declarative_base()

# 全局引擎和会话工厂
_engine: Optional[Any] = None
_session_factory: Optional[Any] = None


def init_engine():
    """初始化数据库引擎
    
    在应用启动时调用，根据配置决定是否启用数据库
    """
    global _engine, _session_factory
    
    if not settings.database_enabled:
        logger.info("database_disabled_skip_init")
        return
    
    try:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_pre_ping=True  # 连接前检查健康
        )
        
        _session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info(
            "database_engine_initialized",
            url=settings.database_url.split('@')[-1] if '@' in settings.database_url else settings.database_url
        )
    except Exception as e:
        logger.error("database_init_failed", error=str(e))
        _engine = None
        _session_factory = None


@asynccontextmanager
async def get_db_session():
    """获取数据库会话
    
    使用上下文管理器自动管理事务
    
    Examples:
        >>> async with get_db_session() as session:
        ...     if session:
        ...         result = await session.execute(select(User))
        ...         users = result.scalars().all()
    
    Yields:
        AsyncSession | None: 数据库会话，如果数据库未启用则为 None
    """
    if not _session_factory:
        logger.debug("database_not_initialized_skip_session")
        yield None
        return
    
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("database_transaction_failed", error=str(e))
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库（创建表）
    
    在应用启动时调用，自动创建所有表
    """
    if not _engine:
        logger.info("database_not_initialized_skip_create_tables")
        return
    
    try:
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("database_tables_created")
    except Exception as e:
        logger.error("database_create_tables_failed", error=str(e))


async def close_db():
    """关闭数据库连接
    
    在应用关闭时调用
    """
    global _engine
    
    if _engine:
        await _engine.dispose()
        logger.info("database_connection_closed")
        _engine = None


def is_database_enabled() -> bool:
    """检查数据库是否已启用并初始化"""
    return _engine is not None and _session_factory is not None
