"""诊断会话缓存"""
import json
from typing import Optional
import structlog

from .redis_client import RedisClient

logger = structlog.get_logger(__name__)


class SessionCache:
    """诊断会话缓存
    
    职责：
    1. 缓存正在进行的诊断会话
    2. 减少数据库查询
    3. 提供快速访问
    
    特性：
    - 自动过期（TTL）
    - 降级支持（Redis 不可用时跳过）
    """
    
    def __init__(self, redis_client: RedisClient):
        """初始化缓存
        
        Args:
            redis_client: Redis 客户端实例
        """
        self.redis = redis_client
        self.prefix = "diagnosis:session:"
        self.default_ttl = 3600  # 1 小时
    
    def _make_key(self, session_id: str) -> str:
        """生成缓存键
        
        Args:
            session_id: 诊断会话 ID
        
        Returns:
            完整的缓存键
        """
        return f"{self.prefix}{session_id}"
    
    async def set(
        self,
        session_id: str,
        session_data: dict,
        ttl: Optional[int] = None
    ) -> bool:
        """缓存会话
        
        Args:
            session_id: 诊断会话 ID
            session_data: 会话数据（字典）
            ttl: 过期时间（秒），None 使用默认值
        
        Returns:
            是否缓存成功
        """
        key = self._make_key(session_id)
        value = json.dumps(session_data, ensure_ascii=False)
        ttl = ttl or self.default_ttl
        
        success = await self.redis.set(key, value, ex=ttl)
        
        if success:
            logger.debug(
                "session_cache_set",
                session_id=session_id,
                ttl=ttl
            )
        
        return success
    
    async def get(self, session_id: str) -> Optional[dict]:
        """获取缓存的会话
        
        Args:
            session_id: 诊断会话 ID
        
        Returns:
            会话数据（字典），如果不存在或解析失败则返回 None
        """
        key = self._make_key(session_id)
        value = await self.redis.get(key)
        
        if not value:
            logger.debug("session_cache_miss", session_id=session_id)
            return None
        
        try:
            session_data = json.loads(value)
            logger.debug("session_cache_hit", session_id=session_id)
            return session_data
        except json.JSONDecodeError as e:
            logger.warning(
                "session_cache_decode_failed",
                session_id=session_id,
                error=str(e)
            )
            return None
    
    async def delete(self, session_id: str) -> bool:
        """删除缓存的会话
        
        Args:
            session_id: 诊断会话 ID
        
        Returns:
            是否删除成功
        """
        key = self._make_key(session_id)
        success = await self.redis.delete(key)
        
        if success:
            logger.debug("session_cache_deleted", session_id=session_id)
        
        return success
    
    async def exists(self, session_id: str) -> bool:
        """检查会话是否在缓存中
        
        Args:
            session_id: 诊断会话 ID
        
        Returns:
            是否存在
        """
        key = self._make_key(session_id)
        return await self.redis.exists(key)
    
    async def extend_ttl(self, session_id: str, seconds: int) -> bool:
        """延长缓存过期时间
        
        Args:
            session_id: 诊断会话 ID
            seconds: 延长的秒数
        
        Returns:
            是否成功
        """
        key = self._make_key(session_id)
        return await self.redis.expire(key, seconds)
    
    async def get_ttl(self, session_id: str) -> int:
        """获取缓存剩余时间
        
        Args:
            session_id: 诊断会话 ID
        
        Returns:
            剩余秒数，-1 表示永不过期，-2 表示不存在
        """
        key = self._make_key(session_id)
        return await self.redis.ttl(key)
