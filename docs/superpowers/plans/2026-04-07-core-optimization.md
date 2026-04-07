# 核心功能优化实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 优化AI视频生成核心功能，实现角色一致性、缓存异步处理、错误处理增强、一键生成流程。

**Architecture:** 
- 角色一致性：使用reference图+LoRA控制图像生成
- 缓存：Redis缓存层+内存缓存fallback
- 异步：Celery任务队列处理长时任务
- 错误处理：重试机制+降级策略+限流

**Tech Stack:** Redis, Celery, tenacity, asyncio

---

## Task 1: 角色一致性服务

**Files:**
- Create: `src/backend/app/services/character_consistency.py`
- Create: `src/backend/app/services/reference_image.py`

### 功能设计

```python
# 角色一致性服务
class CharacterConsistencyService:
    """
    保持角色在多张图片中外观一致
    
    方法：
    1. Reference Image: 使用参考图引导生成
    2. IP-Adapter: 使用图像作为条件
    3. LoRA微调: 为角色训练小型适配器
    """
    
    async def generate_consistent_image(
        self,
        character_id: int,
        prompt: str,
        scene_context: dict,
        style: str = "realistic"
    ) -> GenerationResult:
        """
        生成角色一致的形象图
        
        Args:
            character_id: 角色ID
            prompt: 场景描述
            scene_context: 场景上下文（光线、氛围等）
            style: 图像风格
        
        Returns:
            生成结果，包含图像URL
        """
        # 1. 获取角色reference图
        # 2. 构建一致性提示词
        # 3. 调用图像生成服务
        # 4. 返回结果
        pass
```

- [ ] **Step 1: 创建角色一致性服务**

创建文件 `src/backend/app/services/character_consistency.py`:

```python
"""
Character Consistency Service
保持角色在多张图片中外观一致
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib

from app.core.database import Character, ModelConfig
from .base import BaseAIService, GenerationResult
from .image_service import get_image_service


class CharacterConsistencyService:
    """角色一致性服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._reference_cache: Dict[int, str] = {}
    
    async def get_character_reference(self, character_id: int) -> Optional[str]:
        """获取角色参考图"""
        result = await self.db.execute(
            select(Character).where(Character.id == character_id)
        )
        character = result.scalar_one_or_none()
        if character and character.selected_image:
            return character.selected_image
        return None
    
    async def generate_consistent_image(
        self,
        character_id: int,
        prompt: str,
        scene_context: Optional[Dict[str, Any]] = None,
        style: str = "realistic"
    ) -> GenerationResult:
        """
        生成角色一致的形象图
        
        Args:
            character_id: 角色ID
            prompt: 场景描述
            scene_context: 场景上下文
            style: 图像风格
        
        Returns:
            生成结果
        """
        # 获取角色信息
        result = await self.db.execute(
            select(Character).where(Character.id == character_id)
        )
        character = result.scalar_one_or_none()
        if not character:
            return GenerationResult(success=False, error="Character not found")
        
        # 获取模型配置
        config_result = await self.db.execute(
            select(ModelConfig).where(
                ModelConfig.name == "image",
                ModelConfig.is_active == True
            )
        )
        config = config_result.scalar_one_or_none()
        if not config:
            return GenerationResult(success=False, error="Image model not configured")
        
        # 构建一致性提示词
        consistency_prompt = self._build_consistency_prompt(
            character=character,
            scene_prompt=prompt,
            scene_context=scene_context or {},
            style=style
        )
        
        # 获取图像服务
        service = get_image_service(
            provider=config.provider,
            api_key=config.api_key,
            **config.params
        )
        
        # 如果有参考图，使用reference模式
        if character.selected_image:
            result = await service.generate_with_reference(
                prompt=consistency_prompt,
                reference_image=character.selected_image,
                strength=0.6  # 保持60%的原角色特征
            )
        else:
            result = await service.generate(prompt=consistency_prompt)
        
        return result
    
    def _build_consistency_prompt(
        self,
        character: Character,
        scene_prompt: str,
        scene_context: Dict[str, Any],
        style: str
    ) -> str:
        """构建一致性提示词"""
        parts = []
        
        # 角色核心特征（必须包含）
        if character.appearance:
            parts.append(f"Character appearance: {character.appearance}")
        
        # 服装信息
        if character.clothing:
            parts.append(f"Clothing: {character.clothing}")
        
        # 场景描述
        parts.append(f"Scene: {scene_prompt}")
        
        # 场景上下文
        if scene_context:
            if "lighting" in scene_context:
                parts.append(f"Lighting: {scene_context['lighting']}")
            if "mood" in scene_context:
                parts.append(f"Mood: {scene_context['mood']}")
        
        # 风格
        parts.append(f"Style: {style}")
        
        # 质量标签
        parts.extend([
            "high quality",
            "detailed",
            "cinematic",
            "consistent character design"
        ])
        
        return ", ".join(parts)
    
    async def batch_generate_scenes(
        self,
        character_id: int,
        scenes: List[Dict[str, Any]],
        style: str = "realistic"
    ) -> List[GenerationResult]:
        """
        批量生成角色的多个场景图
        
        Args:
            character_id: 角色ID
            scenes: 场景列表
            style: 图像风格
        
        Returns:
            生成结果列表
        """
        results = []
        for scene in scenes:
            result = await self.generate_consistent_image(
                character_id=character_id,
                prompt=scene.get("description", ""),
                scene_context=scene.get("context"),
                style=style
            )
            results.append(result)
        return results
```

- [ ] **Step 2: 提交**

```bash
git add src/backend/app/services/character_consistency.py
git commit -m "feat: 添加角色一致性服务"
```

---

## Task 2: 缓存服务

**Files:**
- Create: `src/backend/app/services/cache_service.py`

### 功能设计

```python
# 缓存服务
class CacheService:
    """
    多层缓存服务
    
    缓存层次：
    1. 内存缓存 (最快，容量小)
    2. Redis缓存 (中等速度，共享)
    3. 数据库持久化 (最慢，可靠)
    """
    
    async def get_or_generate(
        self,
        key: str,
        generator: Callable,
        ttl: int = 3600
    ) -> Any:
        """
        获取缓存或生成新数据
        
        Args:
            key: 缓存键
            generator: 数据生成函数
            ttl: 过期时间(秒)
        """
        # 1. 检查内存缓存
        # 2. 检查Redis缓存
        # 3. 生成数据
        # 4. 存入缓存
        pass
```

- [ ] **Step 1: 创建缓存服务**

创建文件 `src/backend/app/services/cache_service.py`:

```python
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
```

- [ ] **Step 2: 提交**

```bash
git add src/backend/app/services/cache_service.py
git commit -m "feat: 添加多层缓存服务"
```

---

## Task 3: 错误处理增强

**Files:**
- Create: `src/backend/app/services/resilience.py`

### 功能设计

```python
# 韧性服务
class ResilienceService:
    """
    错误处理和容错机制
    
    功能：
    1. 自动重试 (exponential backoff)
    2. 降级策略 (fallback)
    3. 限流保护 (rate limiting)
    4. 熔断器 (circuit breaker)
    """
    
    @staticmethod
    def retry(
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exceptions: tuple = (Exception,)
    ):
        """重试装饰器"""
        pass
```

- [ ] **Step 1: 创建韧性服务**

创建文件 `src/backend/app/services/resilience.py`:

```python
"""
Resilience Service
错误处理和容错机制
"""
from typing import Optional, Callable, Any, Type, Tuple, List
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
        exceptions: Tuple[Type[Exception], ...] = (Exception,)
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
```

- [ ] **Step 2: 提交**

```bash
git add src/backend/app/services/resilience.py
git commit -m "feat: 添加韧性服务(重试/熔断/限流)"
```

---

## Task 4: 一键生成流程

**Files:**
- Create: `src/backend/app/services/pipeline.py`
- Create: `src/backend/app/api/v1/endpoints/pipeline.py`

### 功能设计

```python
# 一键生成流水线
class VideoPipeline:
    """
    完整视频生成流水线
    
    流程：
    1. 剧本生成 (LLM)
    2. 角色形象生成 (Image)
    3. 分镜脚本生成 (LLM)
    4. 场景图生成 (Image)
    5. 视频片段生成 (Video)
    6. 音频生成 (Voice)
    7. 最终合成
    """
    
    async def generate_short_drama(
        self,
        project_id: int,
        user_input: str,
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        一键生成短剧
        
        Args:
            project_id: 项目ID
            user_input: 用户输入
            options: 生成选项
        
        Returns:
            生成结果
        """
        pass
```

- [ ] **Step 1: 创建一键生成流水线服务**

创建文件 `src/backend/app/services/pipeline.py`:

```python
"""
Video Generation Pipeline
一键生成完整短剧的流水线服务
"""
from typing import Optional, Dict, Any, List, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from enum import Enum
from dataclasses import dataclass
import asyncio

from app.core.database import Project, Character, ModelConfig, GeneratedVideo
from .llm_service import get_llm_service, GenerationResult
from .image_service import get_image_service
from .video_service import get_video_service
from .voice_service import get_voice_service
from .prompts import get_script_prompt, get_character_prompt, get_storyboard_prompt
from .character_consistency import CharacterConsistencyService
from .cache_service import get_cache_service
from .resilience import retry


class PipelineStage(str, Enum):
    """流水线阶段"""
    SCRIPT = "script"
    CHARACTERS = "characters"
    STORYBOARD = "storyboard"
    SCENES = "scenes"
    VIDEOS = "videos"
    AUDIO = "audio"
    COMPLETED = "completed"


@dataclass
class PipelineProgress:
    """流水线进度"""
    stage: PipelineStage
    progress: float  # 0.0 - 1.0
    message: str
    data: Optional[Dict[str, Any]] = None


class VideoPipeline:
    """一键生成流水线"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.consistency_service = CharacterConsistencyService(db)
        self._progress_callbacks: List[Callable] = []
    
    def on_progress(self, callback: Callable):
        """注册进度回调"""
        self._progress_callbacks.append(callback)
    
    async def _report_progress(self, progress: PipelineProgress):
        """报告进度"""
        for callback in self._progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(progress)
                else:
                    callback(progress)
            except Exception:
                pass
    
    @retry(max_attempts=3, base_delay=2.0)
    async def _generate_with_retry(
        self,
        service,
        prompt: str,
        **kwargs
    ) -> GenerationResult:
        """带重试的生成"""
        return await service.generate(prompt=prompt, **kwargs)
    
    async def generate_script(
        self,
        project_id: int,
        user_input: str,
        prompt_suffix: str = ""
    ) -> Dict[str, Any]:
        """生成剧本"""
        # 获取项目信息
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # 获取模型配置
        config_result = await self.db.execute(
            select(ModelConfig).where(
                ModelConfig.name == "text",
                ModelConfig.is_active == True
            )
        )
        config = config_result.scalar_one_or_none()
        if not config:
            raise ValueError("Text model not configured")
        
        # 构建提示词
        system_prompt, user_prompt = get_script_prompt(
            name=project.name,
            type=project.type,
            style=project.style,
            genre=project.genre,
            duration=project.duration,
            platform=project.target_platform,
            description=project.description,
            user_input=user_input
        )
        
        if prompt_suffix:
            user_prompt += f"\n\n## 用户额外要求\n{prompt_suffix}"
        
        # 调用LLM生成
        service = get_llm_service(
            provider=config.provider,
            api_key=config.api_key,
            model=config.model,
            base_url=config.base_url
        )
        
        generation_result = await self._generate_with_retry(
            service,
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.8,
            max_tokens=8000
        )
        
        if not generation_result.success:
            raise Exception(f"Script generation failed: {generation_result.error}")
        
        # 解析结果
        script_data = generation_result.data or {}
        
        # 保存到项目
        project.script_content = script_data
        project.status = "in_progress"
        await self.db.commit()
        
        return script_data
    
    async def generate_character_images(
        self,
        project_id: int,
        characters: List[Dict[str, Any]],
        style: str = "realistic"
    ) -> List[Dict[str, Any]]:
        """生成角色形象图"""
        results = []
        
        for char_data in characters:
            # 创建角色记录
            character = Character(
                project_id=project_id,
                name=char_data.get("name", "未命名角色"),
                age=char_data.get("age"),
                gender=char_data.get("gender"),
                occupation=char_data.get("occupation"),
                appearance=char_data.get("appearance", {}).get("face", "") if isinstance(char_data.get("appearance"), dict) else char_data.get("appearance", ""),
                clothing=char_data.get("clothing", {}).get("style", "") if isinstance(char_data.get("clothing"), dict) else char_data.get("clothing", "")
            )
            self.db.add(character)
            await self.db.flush()
            
            # 生成角色形象图
            try:
                image_result = await self.consistency_service.generate_consistent_image(
                    character_id=character.id,
                    prompt=f"Character portrait, {char_data.get('appearance', '')}, {style} style",
                    style=style
                )
                
                if image_result.success:
                    character.selected_image = image_result.data
            except Exception as e:
                print(f"Failed to generate image for {char_data.get('name')}: {e}")
            
            results.append({
                "id": character.id,
                "name": character.name,
                "image": character.selected_image
            })
        
        await self.db.commit()
        return results
    
    async def generate_short_drama(
        self,
        project_id: int,
        user_input: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        一键生成短剧
        
        Args:
            project_id: 项目ID
            user_input: 用户输入
            options: 生成选项
        
        Returns:
            生成结果
        """
        options = options or {}
        result = {
            "project_id": project_id,
            "stages": {}
        }
        
        try:
            # 阶段1: 剧本生成
            await self._report_progress(PipelineProgress(
                stage=PipelineStage.SCRIPT,
                progress=0.0,
                message="正在生成剧本..."
            ))
            
            script = await self.generate_script(
                project_id=project_id,
                user_input=user_input,
                prompt_suffix=options.get("prompt_suffix", "")
            )
            result["stages"]["script"] = script
            
            await self._report_progress(PipelineProgress(
                stage=PipelineStage.SCRIPT,
                progress=1.0,
                message="剧本生成完成",
                data={"character_count": len(script.get("characters", []))}
            ))
            
            # 阶段2: 角色形象生成
            characters = script.get("characters", [])
            if characters:
                await self._report_progress(PipelineProgress(
                    stage=PipelineStage.CHARACTERS,
                    progress=0.0,
                    message=f"正在生成{len(characters)}个角色形象..."
                ))
                
                character_images = await self.generate_character_images(
                    project_id=project_id,
                    characters=characters,
                    style=options.get("image_style", "realistic")
                )
                result["stages"]["characters"] = character_images
                
                await self._report_progress(PipelineProgress(
                    stage=PipelineStage.CHARACTERS,
                    progress=1.0,
                    message="角色形象生成完成"
                ))
            
            # 阶段3-5: 场景和视频生成 (可选)
            if options.get("generate_videos", False):
                # TODO: 实现场景图和视频生成
                pass
            
            # 完成
            await self._report_progress(PipelineProgress(
                stage=PipelineStage.COMPLETED,
                progress=1.0,
                message="短剧生成完成"
            ))
            
            return result
            
        except Exception as e:
            await self._report_progress(PipelineProgress(
                stage=PipelineStage.COMPLETED,
                progress=0.0,
                message=f"生成失败: {str(e)}"
            ))
            raise
```

- [ ] **Step 2: 创建API端点**

创建文件 `src/backend/app/api/v1/endpoints/pipeline.py`:

```python
"""
Pipeline API endpoints
一键生成流水线API
"""
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import asyncio

from app.core.database import get_db
from app.services.pipeline import VideoPipeline, PipelineProgress


router = APIRouter()


class PipelineStartRequest(BaseModel):
    """流水线启动请求"""
    project_id: int
    user_input: str
    prompt_suffix: Optional[str] = ""
    options: Optional[Dict[str, Any]] = None


class PipelineStatusResponse(BaseModel):
    """流水线状态响应"""
    project_id: int
    status: str
    progress: float
    message: str
    data: Optional[Dict[str, Any]] = None


# 存储运行中的流水线状态
_pipeline_status: Dict[int, Dict[str, Any]] = {}


@router.post("/start", response_model=Dict[str, Any])
async def start_pipeline(
    request: PipelineStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """启动一键生成流水线"""
    # 初始化状态
    _pipeline_status[request.project_id] = {
        "status": "running",
        "progress": 0.0,
        "message": "流水线启动中..."
    }
    
    # 后台运行流水线
    async def run_pipeline():
        pipeline = VideoPipeline(db)
        
        async def update_status(progress: PipelineProgress):
            _pipeline_status[request.project_id] = {
                "status": "running",
                "progress": progress.progress,
                "message": progress.message,
                "stage": progress.stage.value,
                "data": progress.data
            }
        
        pipeline.on_progress(update_status)
        
        try:
            result = await pipeline.generate_short_drama(
                project_id=request.project_id,
                user_input=request.user_input,
                options=request.options
            )
            _pipeline_status[request.project_id] = {
                "status": "completed",
                "progress": 1.0,
                "message": "生成完成",
                "result": result
            }
        except Exception as e:
            _pipeline_status[request.project_id] = {
                "status": "failed",
                "progress": 0.0,
                "message": str(e)
            }
    
    background_tasks.add_task(run_pipeline)
    
    return {
        "project_id": request.project_id,
        "status": "started",
        "message": "流水线已启动，请使用 /pipeline/status/{project_id} 查询进度"
    }


@router.get("/status/{project_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(project_id: int):
    """获取流水线状态"""
    status = _pipeline_status.get(project_id, {
        "status": "not_found",
        "progress": 0.0,
        "message": "未找到该项目的流水线任务"
    })
    
    return PipelineStatusResponse(
        project_id=project_id,
        status=status.get("status", "unknown"),
        progress=status.get("progress", 0.0),
        message=status.get("message", ""),
        data=status.get("data") or status.get("result")
    )


@router.post("/start/stream")
async def start_pipeline_stream(
    request: PipelineStartRequest,
    db: AsyncSession = Depends(get_db)
):
    """启动流水线并实时返回进度 (SSE)"""
    
    async def generate_stream():
        pipeline = VideoPipeline(db)
        
        async def report_progress(progress: PipelineProgress):
            yield f"data: {json.dumps({
                'stage': progress.stage.value,
                'progress': progress.progress,
                'message': progress.message,
                'data': progress.data
            }, ensure_ascii=False)}\n\n"
        
        pipeline.on_progress(lambda p: None)  # 注册回调
        
        try:
            # 手动报告进度
            yield f"data: {json.dumps({
                'stage': 'script',
                'progress': 0.0,
                'message': '正在生成剧本...'
            }, ensure_ascii=False)}\n\n"
            
            result = await pipeline.generate_short_drama(
                project_id=request.project_id,
                user_input=request.user_input,
                options=request.options
            )
            
            yield f"data: {json.dumps({
                'stage': 'completed',
                'progress': 1.0,
                'message': '生成完成',
                'result': result
            }, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({
                'stage': 'failed',
                'progress': 0.0,
                'message': str(e)
            }, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

- [ ] **Step 3: 注册路由**

在 `src/backend/app/api/v1/__init__.py` 中添加:

```python
from app.api.v1.endpoints import pipeline
api_router.include_router(pipeline.router, prefix="/pipeline", tags=["Pipeline"])
```

- [ ] **Step 4: 提交**

```bash
git add src/backend/app/services/pipeline.py src/backend/app/api/v1/endpoints/pipeline.py src/backend/app/api/v1/__init__.py
git commit -m "feat: 添加一键生成流水线服务"
```

---

## Task 5: 集成和测试

**Files:**
- Create: `tests/integration/test_pipeline.py`

- [ ] **Step 1: 创建集成测试**

创建文件 `tests/integration/test_pipeline.py`:

```python
"""
Pipeline integration tests
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


class TestPipelineAPI:
    """流水线API测试"""
    
    async def test_start_pipeline(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试启动流水线"""
        # 创建项目
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]
        
        # 启动流水线
        response = await client.post(
            "/api/v1/pipeline/start",
            json={
                "project_id": project_id,
                "user_input": "一个关于程序员的故事",
                "options": {}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
    
    async def test_get_pipeline_status(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试获取流水线状态"""
        response = await client.get("/api/v1/pipeline/status/99999")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_found"
```

- [ ] **Step 2: 运行测试**

```bash
pytest tests/integration/test_pipeline.py -v
```

- [ ] **Step 3: 提交**

```bash
git add tests/integration/test_pipeline.py
git commit -m "test: 添加流水线集成测试"
```

---

## 文件清单

### 新增文件

| 文件路径 | 描述 |
|----------|------|
| `src/backend/app/services/character_consistency.py` | 角色一致性服务 |
| `src/backend/app/services/cache_service.py` | 多层缓存服务 |
| `src/backend/app/services/resilience.py` | 韧性服务(重试/熔断/限流) |
| `src/backend/app/services/pipeline.py` | 一键生成流水线 |
| `src/backend/app/api/v1/endpoints/pipeline.py` | 流水线API端点 |
| `tests/integration/test_pipeline.py` | 流水线集成测试 |

### 修改文件

| 文件路径 | 修改内容 |
|----------|----------|
| `src/backend/app/api/v1/__init__.py` | 注册pipeline路由 |
| `src/backend/app/core/config.py` | 添加REDIS_URL配置(可选) |
