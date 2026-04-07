"""
LLM Service 单元测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.llm_service import get_llm_service
from app.services.base import GenerationResult


pytestmark = pytest.mark.unit


class TestLLMService:
    """LLM服务测试"""

    def test_get_llm_service_openai(self):
        """测试获取OpenAI服务"""
        service = get_llm_service(
            provider="openai",
            api_key="test-key",
            model="gpt-4"
        )
        assert service is not None

    def test_get_llm_service_anthropic(self):
        """测试获取Anthropic服务"""
        service = get_llm_service(
            provider="anthropic",
            api_key="test-key",
            model="claude-3-opus"
        )
        assert service is not None

    def test_get_llm_service_qwen(self):
        """测试获取通义千问服务"""
        service = get_llm_service(
            provider="qwen",
            api_key="test-key",
            model="qwen-plus",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        assert service is not None

    def test_get_llm_service_deepseek(self):
        """测试获取DeepSeek服务"""
        service = get_llm_service(
            provider="deepseek",
            api_key="test-key",
            model="deepseek-chat"
        )
        assert service is not None


class TestLLMServiceGenerate:
    """LLM生成测试"""

    @pytest.mark.asyncio
    async def test_openai_generate_success(self):
        """测试OpenAI生成成功"""
        with patch("app.services.llm_service.AsyncOpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"title": "测试剧本"}'
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            service = get_llm_service(
                provider="openai",
                api_key="test-key",
                model="gpt-4"
            )
            result = await service.generate(
                prompt="测试提示词",
                system_prompt="系统提示词"
            )

            assert result.success is True
            assert result.content is not None

    @pytest.mark.asyncio
    async def test_openai_generate_with_error(self):
        """测试OpenAI生成失败"""
        with patch("app.services.llm_service.AsyncOpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("API Error")
            )
            mock_openai.return_value = mock_client

            service = get_llm_service(
                provider="openai",
                api_key="test-key",
                model="gpt-4"
            )
            result = await service.generate(
                prompt="测试提示词"
            )

            assert result.success is False
            assert result.error is not None
