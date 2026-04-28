"""
Resilience Service
错误处理和容错机制
"""
from typing import Optional, Callable, Any, Type, Tuple, List, Dict
from functools import wraps
import asyncio
import random
import time
from enum import Enum
from dataclasses import dataclass, field


class CircuitState(str, Enum):
    """熔断器状态"""
    CLOSED = "closed"  # 正常
    OPEN = "open"      # 熔断
    HALF_OPEN = "half_open"  # 半开


@dataclass
class CircuitBreaker:
    """熔断器"""
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0

    def record_success(self):
        """记录成功"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self):
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def should_allow_request(self) -> bool:
        """是否允许请求"""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # 检查是否应该进入半开状态
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        # HALF_OPEN 状态只允许一个请求
        return True


@dataclass
class RateLimiter:
    """限流器"""
    max_requests: int = 100
    window_seconds: float = 60.0
    requests: List[float] = field(default_factory=list)

    def is_allowed(self) -> bool:
        """检查是否允许请求"""
        now = time.time()

        # 清理过期的请求记录
        self.requests = [
            t for t in self.requests
            if now - t < self.window_seconds
        ]

        if len(self.requests) >= self.max_requests:
            return False

        self.requests.append(now)
        return True

    def get_remaining(self) -> int:
        """获取剩余请求数"""
        now = time.time()
        self.requests = [
            t for t in self.requests
            if now - t < self.window_seconds
        ]
        return max(0, self.max_requests - len(self.requests))


class ResilienceService:
    """韧性服务"""

    def __init__(self):
        self._circuit_breakers: dict = {}
        self._rate_limiters: dict = {}

    def get_circuit_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """获取或创建熔断器"""
        if name not in self._circuit_breakers:
            self._circuit_breakers[name] = CircuitBreaker(**kwargs)
        return self._circuit_breakers[name]

    def get_rate_limiter(self, name: str, **kwargs) -> RateLimiter:
        """获取或创建限流器"""
        if name not in self._rate_limiters:
            self._rate_limiters[name] = RateLimiter(**kwargs)
        return self._rate_limiters[name]

    @staticmethod
    def retry(
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        on_retry: Optional[Callable] = None
    ):
        """
        重试装饰器

        Args:
            max_attempts: 最大尝试次数
            base_delay: 基础延迟(秒)
            max_delay: 最大延迟(秒)
            exponential_base: 指数基数
            jitter: 是否添加随机抖动
            exceptions: 需要重试的异常类型
            on_retry: 重试回调函数
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                last_exception = None

                for attempt in range(max_attempts):
                    try:
                        if asyncio.iscoroutinefunction(func):
                            return await func(*args, **kwargs)
                        else:
                            return func(*args, **kwargs)

                    except exceptions as e:
                        last_exception = e

                        if attempt < max_attempts - 1:
                            # 计算延迟
                            delay = min(
                                base_delay * (exponential_base ** attempt),
                                max_delay
                            )

                            # 添加抖动
                            if jitter:
                                delay = delay * (0.5 + random.random())

                            # 回调
                            if on_retry:
                                on_retry(attempt + 1, e, delay)

                            await asyncio.sleep(delay)

                # 所有尝试都失败
                raise last_exception

            return wrapper
        return decorator

    def with_circuit_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0
    ):
        """
        熔断器装饰器
        """
        circuit_breaker = self.get_circuit_breaker(
            name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not circuit_breaker.should_allow_request():
                    raise Exception(f"Circuit breaker '{name}' is open")

                try:
                    result = await func(*args, **kwargs)
                    circuit_breaker.record_success()
                    return result
                except Exception as e:
                    circuit_breaker.record_failure()
                    raise

            return wrapper
        return decorator

    def with_rate_limit(
        self,
        name: str,
        max_requests: int = 100,
        window_seconds: float = 60.0
    ):
        """
        限流装饰器
        """
        rate_limiter = self.get_rate_limiter(
            name,
            max_requests=max_requests,
            window_seconds=window_seconds
        )

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not rate_limiter.is_allowed():
                    raise Exception(f"Rate limit exceeded for '{name}'")
                return await func(*args, **kwargs)

            return wrapper
        return decorator

    def get_stats(self) -> Dict[str, Any]:
        """获取韧性服务统计信息"""
        return {
            "circuit_breakers": {
                name: {
                    "state": cb.state.value,
                    "failure_count": cb.failure_count,
                    "failure_threshold": cb.failure_threshold
                }
                for name, cb in self._circuit_breakers.items()
            },
            "rate_limiters": {
                name: {
                    "current_requests": len(rl.requests),
                    "max_requests": rl.max_requests,
                    "remaining": rl.get_remaining()
                }
                for name, rl in self._rate_limiters.items()
            }
        }


# 全局韧性服务实例
_resilience_service: Optional[ResilienceService] = None


def get_resilience_service() -> ResilienceService:
    """获取韧性服务实例"""
    global _resilience_service
    if _resilience_service is None:
        _resilience_service = ResilienceService()
    return _resilience_service


# 便捷装饰器
retry = ResilienceService.retry
