"""分布式锁"""
from typing import Optional
from contextlib import asynccontextmanager
import structlog

from .redis_client import RedisClient

logger = structlog.get_logger(__name__)


class DistributedLock:
    """Redis 分布式锁
    
    职责：
    1. 防止重复诊断同一服务
    2. 确保并发安全
    
    特性：
    - 基于 Redis SETNX
    - 自动过期（防止死锁）
    - 支持上下文管理器
    """
    
    def __init__(self, redis_client: RedisClient):
        """初始化分布式锁
        
        Args:
            redis_client: Redis 客户端实例
        """
        self.redis = redis_client
        self.prefix = "lock:diagnosis:"
    
    def _make_key(self, resource: str) -> str:
        """生成锁键
        
        Args:
            resource: 资源标识（如服务名）
        
        Returns:
            完整的锁键
        """
        return f"{self.prefix}{resource}"
    
    async def acquire(
        self,
        resource: str,
        ttl: int = 60,
        value: str = "1"
    ) -> bool:
        """获取锁
        
        Args:
            resource: 资源标识
            ttl: 锁过期时间（秒），防止死锁
            value: 锁的值（可用于验证锁的所有权）
        
        Returns:
            是否成功获取锁
        """
        if not self.redis.enabled or not self.redis.redis:
            # Redis 未启用，直接返回 True（降级：不加锁）
            logger.debug(
                "lock_disabled_skip_acquire",
                resource=resource
            )
            return True
        
        key = self._make_key(resource)
        
        try:
            # 使用 SET NX（仅当键不存在时设置）
            result = await self.redis.redis.set(key, value, ex=ttl, nx=True)
            
            if result:
                logger.debug(
                    "lock_acquired",
                    resource=resource,
                    ttl=ttl
                )
            else:
                logger.debug(
                    "lock_acquire_failed_already_locked",
                    resource=resource
                )
            
            return result is not None
            
        except Exception as e:
            logger.warning(
                "lock_acquire_error",
                resource=resource,
                error=str(e)
            )
            # 发生错误时返回 True（降级：不阻塞）
            return True
    
    async def release(self, resource: str) -> bool:
        """释放锁
        
        Args:
            resource: 资源标识
        
        Returns:
            是否释放成功
        """
        key = self._make_key(resource)
        success = await self.redis.delete(key)
        
        if success:
            logger.debug("lock_released", resource=resource)
        
        return success
    
    async def is_locked(self, resource: str) -> bool:
        """检查资源是否被锁定
        
        Args:
            resource: 资源标识
        
        Returns:
            是否被锁定
        """
        key = self._make_key(resource)
        return await self.redis.exists(key)
    
    async def get_lock_ttl(self, resource: str) -> int:
        """获取锁的剩余时间
        
        Args:
            resource: 资源标识
        
        Returns:
            剩余秒数，-1 表示永不过期，-2 表示未锁定
        """
        key = self._make_key(resource)
        return await self.redis.ttl(key)
    
    @asynccontextmanager
    async def lock(
        self,
        resource: str,
        ttl: int = 60,
        wait: bool = False,
        wait_timeout: int = 10
    ):
        """锁的上下文管理器
        
        自动获取和释放锁。
        
        Args:
            resource: 资源标识
            ttl: 锁过期时间（秒）
            wait: 是否等待锁释放
            wait_timeout: 等待超时（秒）
        
        Raises:
            RuntimeError: 无法获取锁
        
        Examples:
            >>> lock = DistributedLock(redis_client)
            >>> async with lock.lock("user-service"):
            ...     # 执行诊断
            ...     pass
        """
        acquired = await self.acquire(resource, ttl)
        
        if not acquired:
            if wait:
                # 等待锁释放
                import asyncio
                start_time = asyncio.get_event_loop().time()
                
                while not acquired:
                    await asyncio.sleep(0.5)
                    acquired = await self.acquire(resource, ttl)
                    
                    if asyncio.get_event_loop().time() - start_time > wait_timeout:
                        raise RuntimeError(
                            f"Failed to acquire lock for {resource} after {wait_timeout}s"
                        )
            else:
                raise RuntimeError(
                    f"Resource {resource} is already locked"
                )
        
        try:
            yield
        finally:
            await self.release(resource)
