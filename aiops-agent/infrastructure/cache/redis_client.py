"""Redis 客户端封装"""
import redis.asyncio as redis
from typing import Optional
import structlog

from config.settings import settings

logger = structlog.get_logger(__name__)


class RedisClient:
    """Redis 客户端
    
    职责：
    1. 基础 get/set 操作
    2. 过期时间管理
    3. 连接池管理
    
    特性：
    - 异步操作
    - 支持禁用（降级）
    - 连接池复用
    """
    
    def __init__(self):
        """初始化客户端"""
        self.enabled = settings.redis_enabled
        self.redis: Optional[redis.Redis] = None
        
        if self.enabled:
            logger.info("redis_client_initialized", url=settings.redis_url)
        else:
            logger.info("redis_client_disabled")
    
    async def connect(self):
        """建立连接"""
        if not self.enabled:
            logger.debug("redis_disabled_skip_connect")
            return
        
        try:
            self.redis = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.redis_max_connections
            )
            logger.info("redis_connected")
        except Exception as e:
            logger.error("redis_connect_failed", error=str(e))
            self.redis = None
    
    async def close(self):
        """关闭连接"""
        if self.redis:
            await self.redis.close()
            logger.info("redis_connection_closed")
    
    async def get(self, key: str) -> Optional[str]:
        """获取值
        
        Args:
            key: 键
        
        Returns:
            值，如果不存在或 Redis 禁用则返回 None
        """
        if not self.enabled or not self.redis:
            logger.debug("redis_disabled_skip_get", key=key)
            return None
        
        try:
            value = await self.redis.get(key)
            logger.debug("redis_get_success", key=key, found=value is not None)
            return value
        except Exception as e:
            logger.warning("redis_get_failed", key=key, error=str(e))
            return None
    
    async def set(
        self,
        key: str,
        value: str,
        ex: Optional[int] = None
    ) -> bool:
        """设置值
        
        Args:
            key: 键
            value: 值
            ex: 过期时间（秒），None 表示永不过期
        
        Returns:
            是否设置成功
        """
        if not self.enabled or not self.redis:
            logger.debug("redis_disabled_skip_set", key=key)
            return False
        
        try:
            result = await self.redis.set(key, value, ex=ex)
            logger.debug("redis_set_success", key=key, ttl=ex)
            return result is not None
        except Exception as e:
            logger.warning("redis_set_failed", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """删除键
        
        Args:
            key: 键
        
        Returns:
            是否删除成功
        """
        if not self.enabled or not self.redis:
            logger.debug("redis_disabled_skip_delete", key=key)
            return False
        
        try:
            result = await self.redis.delete(key)
            logger.debug("redis_delete_success", key=key)
            return result > 0
        except Exception as e:
            logger.warning("redis_delete_failed", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在
        
        Args:
            key: 键
        
        Returns:
            键是否存在
        """
        if not self.enabled or not self.redis:
            return False
        
        try:
            result = await self.redis.exists(key)
            return result > 0
        except Exception as e:
            logger.warning("redis_exists_failed", key=key, error=str(e))
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间
        
        Args:
            key: 键
            seconds: 过期时间（秒）
        
        Returns:
            是否设置成功
        """
        if not self.enabled or not self.redis:
            return False
        
        try:
            result = await self.redis.expire(key, seconds)
            logger.debug("redis_expire_success", key=key, ttl=seconds)
            return result
        except Exception as e:
            logger.warning("redis_expire_failed", key=key, error=str(e))
            return False
    
    async def ttl(self, key: str) -> int:
        """获取键的剩余生存时间
        
        Args:
            key: 键
        
        Returns:
            剩余秒数，-1 表示永不过期，-2 表示键不存在
        """
        if not self.enabled or not self.redis:
            return -2
        
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.warning("redis_ttl_failed", key=key, error=str(e))
            return -2
    
    async def ping(self) -> bool:
        """健康检查
        
        Returns:
            Redis 是否可用
        """
        if not self.enabled:
            return False
        
        try:
            if not self.redis:
                await self.connect()
            
            if self.redis:
                result = await self.redis.ping()
                logger.debug("redis_ping_success", result=result)
                return result
            return False
        except Exception as e:
            logger.warning("redis_ping_failed", error=str(e))
            return False
    
    async def incr(self, key: str) -> Optional[int]:
        """递增键的值
        
        Args:
            key: 键
        
        Returns:
            递增后的值，失败返回 None
        """
        if not self.enabled or not self.redis:
            return None
        
        try:
            return await self.redis.incr(key)
        except Exception as e:
            logger.warning("redis_incr_failed", key=key, error=str(e))
            return None
    
    async def decr(self, key: str) -> Optional[int]:
        """递减键的值
        
        Args:
            key: 键
        
        Returns:
            递减后的值，失败返回 None
        """
        if not self.enabled or not self.redis:
            return None
        
        try:
            return await self.redis.decr(key)
        except Exception as e:
            logger.warning("redis_decr_failed", key=key, error=str(e))
            return None
