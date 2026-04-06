"""
Image Generation Service
"""
import base64
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
import httpx

from .base import BaseAIService, GenerationResult


class ImageGenerationResult:
    """Result of image generation"""
    def __init__(self, success: bool, images: List[str] = None, error: str = None):
        self.success = success
        self.images = images or []
        self.error = error


class DALLEService(BaseAIService):
    """DALL-E image generation service"""

    def __init__(self, api_key: str, model: str = "dall-e-3", **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1,
        **kwargs
    ) -> ImageGenerationResult:
        """Generate image using DALL-E"""
        try:
            response = await self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size=size,
                quality=quality,
                n=n,
                **kwargs
            )

            images = [img.url for img in response.data]
            return ImageGenerationResult(success=True, images=images)
        except Exception as e:
            return ImageGenerationResult(success=False, error=str(e))

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """Generate using base interface"""
        result = await self.generate_image(prompt, **kwargs)
        return GenerationResult(
            success=result.success,
            error=result.error,
            data={"images": result.images}
        )

    async def test_connection(self) -> bool:
        """Test DALL-E connection"""
        try:
            result = await self.generate_image("A simple test image", size="256x256")
            return result.success
        except:
            return False


class StabilityAIService(BaseAIService):
    """Stability AI image generation service"""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.api_host = kwargs.get("api_host", "https://api.stability.ai")

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        cfg_scale: float = 7.0,
        **kwargs
    ) -> ImageGenerationResult:
        """Generate image using Stability AI"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_host}/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    json={
                        "text_prompts": [
                            {"text": prompt, "weight": 1},
                            {"text": negative_prompt, "weight": -1} if negative_prompt else None
                        ],
                        "cfg_scale": cfg_scale,
                        "height": height,
                        "width": width,
                        "steps": steps,
                    },
                    timeout=60.0
                )

                if response.status_code != 200:
                    return ImageGenerationResult(
                        success=False,
                        error=f"API error: {response.status_code}"
                    )

                data = response.json()
                images = []
                for artifact in data["artifacts"]:
                    if artifact.get("finishReason") == "SUCCESS":
                        # Save base64 image or get URL
                        images.append(f"data:image/png;base64,{artifact['base64']}")

                return ImageGenerationResult(success=True, images=images)
        except Exception as e:
            return ImageGenerationResult(success=False, error=str(e))

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """Generate using base interface"""
        result = await self.generate_image(prompt, **kwargs)
        return GenerationResult(
            success=result.success,
            error=result.error,
            data={"images": result.images}
        )

    async def test_connection(self) -> bool:
        """Test Stability AI connection"""
        try:
            result = await self.generate_image("A simple test", width=512, height=512, steps=10)
            return result.success
        except:
            return False


class MidjourneyService(BaseAIService):
    """Midjourney service (via API proxy or self-hosted)"""

    def __init__(self, api_key: str, base_url: str = None, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        # Midjourney doesn't have official API, use proxy service
        self.api_url = base_url or kwargs.get("api_url", "https://api.midjourney-proxy.com")

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        style: str = None,
        **kwargs
    ) -> ImageGenerationResult:
        """Generate image using Midjourney proxy"""
        try:
            # Build prompt with parameters
            full_prompt = prompt
            if aspect_ratio:
                full_prompt += f" --ar {aspect_ratio}"
            if style:
                full_prompt += f" --style {style}"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/imagine",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"prompt": full_prompt},
                    timeout=300.0
                )

                if response.status_code != 200:
                    return ImageGenerationResult(
                        success=False,
                        error=f"API error: {response.status_code}"
                    )

                data = response.json()
                images = data.get("imageUrls", [])

                return ImageGenerationResult(success=True, images=images)
        except Exception as e:
            return ImageGenerationResult(success=False, error=str(e))

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        result = await self.generate_image(prompt, **kwargs)
        return GenerationResult(
            success=result.success,
            error=result.error,
            data={"images": result.images}
        )

    async def test_connection(self) -> bool:
        try:
            result = await self.generate_image("A simple test image")
            return result.success
        except:
            return False


def get_image_service(provider: str, api_key: str, **kwargs) -> BaseAIService:
    """Factory function to get image generation service"""
    # 阿里云百炼图像生成
    if provider.lower() in ["wanx", "alibaba", "aliyun", "qwen-image"]:
        from .alibaba_cloud import WanxImageService, QwenImageService
        model = kwargs.get("model", "wanx2.1-turbo")
        if "qwen" in model.lower():
            return QwenImageService(api_key=api_key, model=model, **kwargs)
        return WanxImageService(api_key=api_key, model=model, **kwargs)

    services = {
        "dalle": DALLEService,
        "dall-e": DALLEService,
        "openai": DALLEService,
        "stability": StabilityAIService,
        "stable-diffusion": StabilityAIService,
        "midjourney": MidjourneyService
    }

    service_class = services.get(provider.lower())
    if not service_class:
        raise ValueError(f"Unknown image provider: {provider}")

    return service_class(api_key=api_key, **kwargs)
