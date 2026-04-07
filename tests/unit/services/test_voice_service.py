"""
Voice Service 单元测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.voice_service import get_voice_service
from app.services.base import GenerationResult


pytestmark = pytest.mark.unit


class TestVoiceService:
    """语音服务测试"""

    def test_get_voice_service_openai(self):
        """测试获取OpenAI TTS服务"""
        service = get_voice_service(
            provider="openai",
            api_key="test-key"
        )
        assert service is not None

    def test_get_voice_service_elevenlabs(self):
        """测试获取ElevenLabs服务"""
        service = get_voice_service(
            provider="elevenlabs",
            api_key="test-key"
        )
        assert service is not None

    def test_get_voice_service_cosyvoice(self):
        """测试获取CosyVoice服务"""
        service = get_voice_service(
            provider="cosyvoice",
            api_key="test-key"
        )
        assert service is not None


class TestVoiceServiceSynthesize:
    """语音合成测试"""

    @pytest.mark.asyncio
    async def test_openai_synthesize_success(self):
        """测试OpenAI TTS合成成功"""
        with patch("app.services.voice_service.AsyncOpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = b"fake_audio_data"
            mock_client.audio.speech.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            service = get_voice_service(
                provider="openai",
                api_key="test-key"
            )
            result = await service.synthesize(
                text="测试文本",
                voice="alloy"
            )

            assert result.success is True
            assert result.data is not None

    @pytest.mark.asyncio
    async def test_voice_synthesize_with_error(self):
        """测试语音合成失败"""
        with patch("app.services.voice_service.AsyncOpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.audio.speech.create = AsyncMock(
                side_effect=Exception("API Error")
            )
            mock_openai.return_value = mock_client

            service = get_voice_service(
                provider="openai",
                api_key="test-key"
            )
            result = await service.synthesize(
                text="测试文本"
            )

            assert result.success is False
            assert result.error is not None
