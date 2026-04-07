"""
Cache Service
多层缓存服务
"""
from typing import Optional, Any, Callable, Dict
from datetime import timedelta
import json
import hashlib
import asyncio
from functools import wraps

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class CacheService:
    """多层缓存服务"""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 3600,
        max_memory_cache_size: int = 1000
    ):
        self.default_ttl = default_ttl
        self.max_memory_cache_size = max_memory_cache_size

        # 内存缓存
        self._memory_cache: Dict[str, tuple] = []  # (key, value, expires_at)
        self._memory_cache_dict: Dict[str, Any] = {}

        # Redis客户端
        self._redis: Optional[redis.Redis] = None
        self._redis_url = redis_url

    async def initialize(self):
        """初始化Redis连接"""
        if REDIS_AVAILABLE and self._redis_url:
            try:
                self._redis = redis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self._redis.ping()
            except Exception as e:
                print(f"Redis connection failed: {e}")
                self._redis = None

    async def close(self):
        """关闭连接"""
        if self._redis:
            await self._redis.close()

    @staticmethod
    def generate_key(*args, **kwargs) -> str:
        """生成缓存键"""
        content = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        # 1. 检查内存缓存
        if key in self._memory_cache_dict:
            return self._memory_cache_dict[key]

        # 2. 检查Redis缓存
        if self._redis:
            try:
                value = await self._redis.get(key)
                if value:
                    data = json.loads(value)
                    # 存入内存缓存
                    self._memory_cache_dict[key] = data
                    return data
            except Exception:
                pass

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存"""
        ttl = ttl or self.default_ttl

        # 1. 存入内存缓存
        self._memory_cache_dict[key] = value

        # 清理过大的内存缓存
        if len(self._memory_cache_dict) > self.max_memory_cache_size:
            # 删除一半的缓存
            keys_to_remove = list(self._memory_cache_dict.keys())[:self.max_memory_cache_size // 2]
            for k in keys_to_remove:
                del self._memory_cache_dict[k]

        # 2. 存入Redis缓存
        if self._redis:
            try:
                await self._redis.setex(
                    key,
                    ttl,
                    json.dumps(value)
                )
                return True
            except Exception:
                pass

        return True

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        # 删除内存缓存
        if key in self._memory_cache_dict:
            del self._memory_cache_dict[key]

        # 删除Redis缓存
        if self._redis:
            try:
                await self._redis.delete(key)
            except Exception:
                pass

        return True

    async def get_or_generate(
        self,
        key: str,
        generator: Callable,
        ttl: Optional[int] = None
    ) -> Any:
        """
        获取缓存或生成新数据

        Args:
            key: 缓存键
            generator: 数据生成函数
            ttl: 过期时间
        """
        # 检查缓存
        cached = await self.get(key)
        if cached is not None:
            return cached

        # 生成数据
        if asyncio.iscoroutinefunction(generator):
            value = await generator()
        else:
            value = generator()

        # 存入缓存
        await self.set(key, value, ttl)

        return value

    def cached(self, key_func: Callable = None, ttl: int = None):
        """
        缓存装饰器

        Usage:
            @cache_service.cached(lambda x: f"result:{x}")
            async def get_result(x):
                return expensive_operation(x)
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                if key_func:
                    key = key_func(*args, **kwargs)
                else:
                    key = self.generate_key(func.__name__, *args, **kwargs)

                # 获取或生成
                return await self.get_or_generate(
                    key=key,
                    generator=lambda: func(*args, **kwargs),
                    ttl=ttl
                )
            return wrapper
        return decorator

    async def clear_all(self) -> bool:
        """清除所有缓存"""
        # 清除内存缓存
        self._memory_cache_dict.clear()

        # 清除Redis缓存
        if self._redis:
            try:
                await self._redis.flushdb()
            except Exception:
                pass

        return True

    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            "memory_cache_size": len(self._memory_cache_dict),
            "max_memory_cache_size": self.max_memory_cache_size,
            "redis_available": self._redis is not None
        }

        if self._redis:
            try:
                info = await self._redis.info("memory")
                stats["redis_used_memory"] = info.get("used_memory_human", "unknown")
            except Exception:
                pass

        return stats


# 全局缓存实例
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """获取缓存服务实例"""
    global _cache_service
    if _cache_service is None:
        from app.core.config import settings
        _cache_service = CacheService(redis_url=settings.REDIS_URL)
        await _cache_service.initialize()
    return _cache_service
