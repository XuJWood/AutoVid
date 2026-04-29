"""
Video Generation Service
"""
import asyncio
from typing import Optional, Dict, Any, List
from enum import Enum
import httpx

from .base import BaseAIService, GenerationResult


class VideoStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoGenerationResult:
    """Result of video generation"""
    def __init__(
        self,
        success: bool,
        video_id: str = None,
        video_url: str = None,
        status: VideoStatus = VideoStatus.PENDING,
        error: str = None
    ):
        self.success = success
        self.video_id = video_id
        self.video_url = video_url
        self.status = status
        self.error = error


class KlingAIService(BaseAIService):
    """可灵AI video generation service"""

    def __init__(self, api_key: str, base_url: str = None, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.api_url = base_url or "https://api.klingai.com/v1"

    async def generate_video(
        self,
        prompt: str,
        image_url: str = None,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        **kwargs
    ) -> VideoGenerationResult:
        """Generate video using Kling AI"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "prompt": prompt,
                    "duration": duration,
                    "aspect_ratio": aspect_ratio,
                }
                if image_url:
                    payload["image_url"] = image_url

                response = await client.post(
                    f"{self.api_url}/videos/generations",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=30.0
                )

                if response.status_code != 200:
                    return VideoGenerationResult(
                        success=False,
                        error=f"API error: {response.status_code}"
                    )

                data = response.json()
                return VideoGenerationResult(
                    success=True,
                    video_id=data.get("id"),
                    status=VideoStatus.PROCESSING
                )
        except Exception as e:
            return VideoGenerationResult(success=False, error=str(e))

    async def get_video_status(self, video_id: str) -> VideoGenerationResult:
        """Get video generation status"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/videos/generations/{video_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10.0
                )

                if response.status_code != 200:
                    return VideoGenerationResult(
                        success=False,
                        error=f"API error: {response.status_code}"
                    )

                data = response.json()
                status = VideoStatus(data.get("status", "pending"))

                return VideoGenerationResult(
                    success=True,
                    video_id=video_id,
                    video_url=data.get("video_url"),
                    status=status
                )
        except Exception as e:
            return VideoGenerationResult(success=False, error=str(e))

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        result = await self.generate_video(prompt, **kwargs)
        return GenerationResult(
            success=result.success,
            error=result.error,
            data={
                "video_id": result.video_id,
                "status": result.status.value
            }
        )

    async def test_connection(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/status",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10.0
                )
                return response.status_code == 200
        except:
            return False


class RunwayService(BaseAIService):
    """Runway Gen-2 video generation service"""

    def __init__(self, api_key: str, base_url: str = None, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.api_url = base_url or "https://api.runwayml.com/v1"

    async def generate_video(
        self,
        prompt: str,
        image_url: str = None,
        duration: int = 4,
        **kwargs
    ) -> VideoGenerationResult:
        """Generate video using Runway"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "prompt": prompt,
                    "duration": duration,
                }
                if image_url:
                    payload["image"] = image_url

                response = await client.post(
                    f"{self.api_url}/generations",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=30.0
                )

                if response.status_code not in [200, 201]:
                    return VideoGenerationResult(
                        success=False,
                        error=f"API error: {response.status_code}"
                    )

                data = response.json()
                return VideoGenerationResult(
                    success=True,
                    video_id=data.get("id"),
                    status=VideoStatus.PROCESSING
                )
        except Exception as e:
            return VideoGenerationResult(success=False, error=str(e))

    async def get_video_status(self, video_id: str) -> VideoGenerationResult:
        """Get video generation status"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/generations/{video_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10.0
                )

                data = response.json()
                status_map = {
                    "pending": VideoStatus.PENDING,
                    "processing": VideoStatus.PROCESSING,
                    "completed": VideoStatus.COMPLETED,
                    "failed": VideoStatus.FAILED
                }
                status = status_map.get(data.get("status"), VideoStatus.PENDING)

                return VideoGenerationResult(
                    success=True,
                    video_id=video_id,
                    video_url=data.get("videoUrl"),
                    status=status
                )
        except Exception as e:
            return VideoGenerationResult(success=False, error=str(e))

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        result = await self.generate_video(prompt, **kwargs)
        return GenerationResult(
            success=result.success,
            error=result.error,
            data={
                "video_id": result.video_id,
                "status": result.status.value
            }
        )

    async def test_connection(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/user",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10.0
                )
                return response.status_code == 200
        except:
            return False


class PikaService(BaseAIService):
    """Pika Art video generation service"""

    def __init__(self, api_key: str, base_url: str = None, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.api_url = base_url or "https://api.pika.art/v1"

    async def generate_video(
        self,
        prompt: str,
        image_url: str = None,
        fps: int = 24,
        **kwargs
    ) -> VideoGenerationResult:
        """Generate video using Pika"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "prompt": prompt,
                    "fps": fps,
                }
                if image_url:
                    payload["image"] = image_url

                response = await client.post(
                    f"{self.api_url}/generate",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=30.0
                )

                if response.status_code not in [200, 201]:
                    return VideoGenerationResult(
                        success=False,
                        error=f"API error: {response.status_code}"
                    )

                data = response.json()
                return VideoGenerationResult(
                    success=True,
                    video_id=data.get("id"),
                    status=VideoStatus.PROCESSING
                )
        except Exception as e:
            return VideoGenerationResult(success=False, error=str(e))

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        result = await self.generate_video(prompt, **kwargs)
        return GenerationResult(
            success=result.success,
            error=result.error,
            data={
                "video_id": result.video_id,
                "status": result.status.value
            }
        )

    async def test_connection(self) -> bool:
        return True  # Pika doesn't have a simple test endpoint


def get_video_service(provider: str, api_key: str, **kwargs) -> BaseAIService:
    """Factory function to get video generation service"""
    # 统一多模态服务
    if provider.lower() in ["multimodal", "generic"]:
        from .multimodal_service import MultimodalVideoAdapter
        return MultimodalVideoAdapter(api_key=api_key, **kwargs)

    # 阿里云百炼视频生成
    if provider.lower() in ["wanx", "alibaba", "aliyun", "wan"]:
        from .alibaba_cloud import WanxVideoService
        model = kwargs.pop("model", None) or "wan2.7-t2v"
        return WanxVideoService(api_key=api_key, model=model, **kwargs)

    # 火山引擎 Seedance 视频生成（视频+音频一体化）
    if provider.lower() in ["seedance", "volcano", "volcengine", "ark"]:
        from .seedance_video import SeedanceVideoService
        model = kwargs.pop("model", None) or "doubao-seedance-2-0-fast-260128"
        return SeedanceVideoService(api_key=api_key, model=model, **kwargs)

    services = {
        "kling": KlingAIService,
        "可灵": KlingAIService,
        "runway": RunwayService,
        "pika": PikaService
    }

    service_class = services.get(provider.lower())
    if not service_class:
        raise ValueError(f"Unknown video provider: {provider}")

    return service_class(api_key=api_key, **kwargs)
