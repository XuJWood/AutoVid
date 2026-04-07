"""
Image Service 单元测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.image_service import get_image_service
from app.services.base import GenerationResult


pytestmark = pytest.mark.unit


class TestImageService:
    """图像服务测试"""

    def test_get_image_service_dalle(self):
        """测试获取DALL-E服务"""
        service = get_image_service(
            provider="dalle",
            api_key="test-key"
        )
        assert service is not None

    def test_get_image_service_stability(self):
        """测试获取Stability AI服务"""
        service = get_image_service(
            provider="stability",
            api_key="test-key"
        )
        assert service is not None

    def test_get_image_service_wanx(self):
        """测试获取万相服务"""
        service = get_image_service(
            provider="wanx",
            api_key="test-key"
        )
        assert service is not None


class TestImageServiceGenerate:
    """图像生成测试"""

    @pytest.mark.asyncio
    async def test_dalle_generate_success(self):
        """测试DALL-E生成成功"""
        with patch("app.services.image_service.AsyncOpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.data = [MagicMock()]
            mock_response.data[0].url = "https://example.com/image.png"
            mock_client.images.generate = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            service = get_image_service(
                provider="dalle",
                api_key="test-key"
            )
            result = await service.generate(
                prompt="一个美丽的风景"
            )

            assert result.success is True
            assert result.data is not None

    @pytest.mark.asyncio
    async def test_image_generate_with_error(self):
        """测试图像生成失败"""
        with patch("app.services.image_service.AsyncOpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.images.generate = AsyncMock(
                side_effect=Exception("API Error")
            )
            mock_openai.return_value = mock_client

            service = get_image_service(
                provider="dalle",
                api_key="test-key"
            )
            result = await service.generate(
                prompt="测试提示词"
            )

            assert result.success is False
            assert result.error is not None
