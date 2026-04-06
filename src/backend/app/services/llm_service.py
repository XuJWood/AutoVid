"""
LLM Service - Text generation using various LLM providers
"""
import json
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import httpx

from .base import BaseAIService, GenerationResult


class OpenAIService(BaseAIService):
    """OpenAI GPT service"""

    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = "gpt-4-turbo-preview", **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> GenerationResult:
        """Generate text using OpenAI"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            content = response.choices[0].message.content

            # Try to parse as JSON if possible
            data = None
            try:
                data = json.loads(content)
            except (json.JSONDecodeError, TypeError):
                pass

            return GenerationResult(
                success=True,
                content=content,
                data=data,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            )
        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    async def test_connection(self) -> bool:
        """Test OpenAI connection"""
        try:
            result = await self.generate("Hello", max_tokens=10)
            return result.success
        except:
            return False


class ClaudeService(BaseAIService):
    """Anthropic Claude service"""

    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = "claude-3-opus-20240229", **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> GenerationResult:
        """Generate text using Claude"""
        try:
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            response = await self.client.messages.create(**kwargs)

            content = response.content[0].text

            # Try to parse as JSON
            data = None
            try:
                data = json.loads(content)
            except (json.JSONDecodeError, TypeError):
                pass

            return GenerationResult(
                success=True,
                content=content,
                data=data,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            )
        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    async def test_connection(self) -> bool:
        """Test Claude connection"""
        try:
            result = await self.generate("Hello", max_tokens=10)
            return result.success
        except:
            return False


class DeepSeekService(BaseAIService):
    """DeepSeek service (OpenAI compatible)"""

    def __init__(self, api_key: str, base_url: Optional[str] = "https://api.deepseek.com/v1", model: str = "deepseek-chat", **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url or "https://api.deepseek.com/v1"
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> GenerationResult:
        """Generate text using DeepSeek"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            content = response.choices[0].message.content

            data = None
            try:
                data = json.loads(content)
            except (json.JSONDecodeError, TypeError):
                pass

            return GenerationResult(
                success=True,
                content=content,
                data=data,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            )
        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    async def test_connection(self) -> bool:
        """Test DeepSeek connection"""
        try:
            result = await self.generate("Hello", max_tokens=10)
            return result.success
        except:
            return False


def get_llm_service(provider: str, api_key: str, model: Optional[str] = None, **kwargs) -> BaseAIService:
    """Factory function to get LLM service"""
    services = {
        "openai": OpenAIService,
        "anthropic": ClaudeService,
        "claude": ClaudeService,
        "deepseek": DeepSeekService,
        "qwen": "alibaba",  # 别名
        "tongyi": "alibaba",  # 别名
        "alibaba": "alibaba",  # 别名
        "aliyun": "alibaba",  # 别名
    }

    provider_lower = provider.lower()

    # 阿里云百炼特殊处理
    if provider_lower in ["qwen", "tongyi", "alibaba", "aliyun"]:
        from .alibaba_cloud import QwenService
        default_model = model or "qwen-plus"
        return QwenService(api_key=api_key, model=default_model, **kwargs)

    service_class = services.get(provider_lower)
    if not service_class:
        raise ValueError(f"Unknown LLM provider: {provider}")

    if model:
        return service_class(api_key=api_key, model=model, **kwargs)
    return service_class(api_key=api_key, **kwargs)
