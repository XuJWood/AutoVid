"""
Unified Multimodal Service
统一多模态服务接口，使用 OpenAI 兼容 API 格式
支持文生图、图生图、图生视频
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from openai import AsyncOpenAI
import httpx

from .base import BaseAIService, GenerationResult


@dataclass
class ImageResult:
    success: bool
    images: List[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.images is None:
            self.images = []


@dataclass
class VideoResult:
    success: bool
    video_url: Optional[str] = None
    video_id: Optional[str] = None
    status: str = "pending"
    error: Optional[str] = None


class GenericMultimodalService(BaseAIService):
    """通用多模态服务，使用 OpenAI 兼容 API"""

    def __init__(self, api_key: str, base_url: str = None, model: str = None, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.model = model or "default"
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = None

    def _require_key(self):
        if not self.api_key:
            raise ValueError("多模态模型 API key 未设置，请在模型配置中填写 API key")

    async def generate_image(
        self,
        prompt: str,
        reference_image: Optional[str] = None,
        size: str = "1024x1024",
        n: int = 1,
        **kwargs
    ) -> ImageResult:
        """生成图片（文生图或图生图）"""
        self._require_key()

        try:
            if reference_image:
                # 图生图: 使用 chat/completions 格式传入图片
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": reference_image}}
                        ]
                    }
                ]
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    **kwargs
                )
                content = response.choices[0].message.content
                images = []
                if content:
                    images = self._extract_urls_from_content(content)
                return ImageResult(success=True, images=images)
            else:
                # 文生图: 尝试 images/generations 接口
                try:
                    response = await self.client.images.generate(
                        model=self.model,
                        prompt=prompt,
                        size=size,
                        n=n,
                        **kwargs
                    )
                    images = [img.url for img in response.data]
                    return ImageResult(success=True, images=images)
                except Exception:
                    # fallback: 使用 chat/completions 格式
                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": f"Generate an image: {prompt}"}
                            ]
                        }
                    ]
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        **kwargs
                    )
                    content = response.choices[0].message.content
                    images = self._extract_urls_from_content(content) if content else []
                    return ImageResult(success=True, images=images)

        except Exception as e:
            return ImageResult(success=False, error=str(e))

    async def generate_video(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        duration: int = 5,
        **kwargs
    ) -> VideoResult:
        """生成视频（文生视频或图生视频）"""
        self._require_key()

        try:
            messages = []
            if image_url:
                content_parts = [
                    {"type": "text", "text": f"Generate a video based on this image: {prompt}, duration {duration}s"},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            else:
                content_parts = [
                    {"type": "text", "text": f"Generate a video: {prompt}, duration {duration}s"}
                ]
            messages.append({"role": "user", "content": content_parts})

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            content = response.choices[0].message.content
            video_url = None
            if content:
                urls = self._extract_urls_from_content(content)
                video_url = urls[0] if urls else None

            return VideoResult(
                success=True,
                video_url=video_url,
                status="completed"
            )
        except Exception as e:
            return VideoResult(success=False, error=str(e))

    def _extract_urls_from_content(self, content: str) -> List[str]:
        """从响应内容中提取URL"""
        import re
        urls = re.findall(r'https?://[^\s<>"]+', content)
        return urls

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """通过 base interface 生成（默认走图片）"""
        image_mode = kwargs.pop("_mode", "image")
        if image_mode == "video":
            result = await self.generate_video(prompt, **kwargs)
            return GenerationResult(
                success=result.success,
                error=result.error,
                data={"video_url": result.video_url, "video_id": result.video_id, "status": result.status}
            )
        else:
            result = await self.generate_image(prompt, **kwargs)
            return GenerationResult(
                success=result.success,
                error=result.error,
                data={"images": result.images}
            )

    async def test_connection(self) -> bool:
        if not self.api_key:
            return False
        try:
            result = await self.generate_image("test", size="256x256")
            return result.success
        except Exception:
            return False


class MultimodalImageAdapter(BaseAIService):
    """多模态服务适配器，实现 BaseAIService 的 generate 用于图片生成"""

    def __init__(self, api_key: str, base_url: str = None, model: str = None, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.service = GenericMultimodalService(api_key=api_key, base_url=base_url, model=model, **kwargs)

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        result = await self.service.generate_image(prompt, **kwargs)
        return GenerationResult(
            success=result.success,
            error=result.error,
            data={"images": result.images}
        )

    async def test_connection(self) -> bool:
        return await self.service.test_connection()


class MultimodalVideoAdapter(BaseAIService):
    """多模态服务适配器，实现 BaseAIService 的 generate 用于视频生成"""

    def __init__(self, api_key: str, base_url: str = None, model: str = None, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.service = GenericMultimodalService(api_key=api_key, base_url=base_url, model=model, **kwargs)

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        result = await self.service.generate_video(prompt, **kwargs)
        return GenerationResult(
            success=result.success,
            error=result.error,
            data={"video_url": result.video_url, "video_id": result.video_id, "status": result.status}
        )

    async def test_connection(self) -> bool:
        return await self.service.test_connection()
