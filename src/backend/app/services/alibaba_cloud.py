"""
Alibaba Cloud Bailian (阿里云百炼) Services
Supports: 通义千问 (文本), 万相 (图像), CosyVoice (语音)
"""
import os
import json
import asyncio
import tempfile
import httpx
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI

from .base import BaseAIService, GenerationResult


class QwenService(BaseAIService):
    """通义千问文本生成服务 - OpenAI 兼容接口"""

    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(
        self,
        api_key: str,
        model: str = "qwen-plus",
        base_url: str = None,
        **kwargs
    ):
        # 确保 base_url 有默认值
        effective_base_url = base_url or self.DEFAULT_BASE_URL
        super().__init__(api_key, effective_base_url, **kwargs)
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=effective_base_url
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> GenerationResult:
        """生成文本"""
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

            # 尝试解析 JSON
            data = None
            try:
                # 处理可能的 markdown 代码块
                text = content.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
                data = json.loads(text)
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
        """测试连接"""
        try:
            result = await self.generate("你好", max_tokens=20)
            return result.success
        except:
            return False


class WanxImageService(BaseAIService):
    """万相图像生成服务"""

    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com"

    def __init__(
        self,
        api_key: str,
        model: str = "wanx2.1-turbo",
        base_url: str = None,
        **kwargs
    ):
        effective_base_url = base_url or self.DEFAULT_BASE_URL
        super().__init__(api_key, effective_base_url, **kwargs)
        self.model = model

    async def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        size: str = "1024*1024",
        n: int = 1,
        style: Optional[str] = None,
        project_id: Optional[int] = None,
        **kwargs
    ) -> GenerationResult:
        """生成图像

        Args:
            prompt: 图像描述
            negative_prompt: 负向提示词
            size: 图像尺寸 (512*512, 720*1280, 1024*1024 等)
            n: 生成数量
            style: 风格 (photography, portrait, 3d, anime, oil_painting, watercolor, sketch 等)
            project_id: 项目ID（提供时下载到本地项目文件夹）
        """
        try:
            url = f"{self.base_url}/api/v1/services/aigc/text2image/image-synthesis"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable"  # 异步模式
            }

            parameters = {
                "style": style,
                "size": size,
                "n": n,
                "seed": kwargs.get("seed"),
            }
            # 移除 None 值
            parameters = {k: v for k, v in parameters.items() if v is not None}

            if negative_prompt:
                parameters["negative_prompt"] = negative_prompt

            payload = {
                "model": self.model,
                "input": {
                    "prompt": prompt
                },
                "parameters": parameters
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                # 创建任务
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code != 200:
                    return GenerationResult(
                        success=False,
                        error=f"创建图像生成任务失败: {response.text}"
                    )

                result = response.json()
                task_id = result.get("output", {}).get("task_id")

                if not task_id:
                    return GenerationResult(
                        success=False,
                        error="未获取到任务ID"
                    )

                # 轮询任务状态
                task_url = f"{self.base_url}/api/v1/tasks/{task_id}"
                max_wait = 120  # 最大等待时间（秒）
                waited = 0

                while waited < max_wait:
                    await asyncio.sleep(3)
                    waited += 3

                    task_response = await client.get(
                        task_url,
                        headers={"Authorization": f"Bearer {self.api_key}"}
                    )

                    if task_response.status_code != 200:
                        continue

                    task_result = task_response.json()
                    status = task_result.get("output", {}).get("task_status")

                    if status == "SUCCEEDED":
                        results = task_result.get("output", {}).get("results", [])
                        urls = [r.get("url") for r in results if r.get("url")]

                        # 下载到本地项目文件夹
                        local_paths = []
                        if project_id and urls:
                            from .media_storage import download_and_save_image
                            for i, url in enumerate(urls):
                                local_path = await download_and_save_image(url, project_id, prefix=f"img_{i}")
                                if local_path:
                                    local_paths.append(local_path)

                        return GenerationResult(
                            success=True,
                            content=json.dumps(urls),
                            data={
                                "images": urls,
                                "urls": urls,
                                "task_id": task_id,
                                "local_paths": local_paths
                            }
                        )
                    elif status == "FAILED":
                        error_msg = task_result.get("output", {}).get("message", "生成失败")
                        return GenerationResult(success=False, error=error_msg)

                return GenerationResult(
                    success=False,
                    error="图像生成超时"
                )

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            result = await self.generate("一只猫", size="512*512")
            return result.success
        except:
            return False


class WanxVideoService(BaseAIService):
    """万相视频生成服务（wan2.7-i2v：图生视频 + 音频驱动口型同步）"""

    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com"

    def __init__(
        self,
        api_key: str,
        model: str = "wan2.7-i2v",
        base_url: str = None,
        **kwargs
    ):
        effective_base_url = base_url or self.DEFAULT_BASE_URL
        super().__init__(api_key, effective_base_url, **kwargs)
        self.model = model

    # Resolution to size mapping (t2v models support limited sizes)
    _SIZE_MAP = {
        "720P": "1280*720",
        "1080P": "1280*720",       # t2v only supports up to 720P
        "480P": "832*480",
        "720P_PORTRAIT": "720*1280",
        "1080P_PORTRAIT": "720*1280",
        "1:1_720P": "960*960",
    }

    async def generate(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        audio_url: Optional[str] = None,
        duration: int = 5,
        resolution: str = "720P",
        project_id: Optional[int] = None,
        **kwargs
    ) -> GenerationResult:
        """生成视频

        t2v (wanx2.1-t2v-turbo): 文生视频，5s，无 media
        i2v (wan2.7-i2v): 图生视频 + 音频驱动，2-15s，需要 media (HTTP URLs)
        """
        try:
            url = f"{self.base_url}/api/v1/services/aigc/video-generation/video-synthesis"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable"
            }

            input_data = {"prompt": prompt}
            is_i2v = "i2v" in self.model

            if is_i2v:
                media = []
                if image_url:
                    media.append({"url": image_url, "type": "first_frame"})
                if audio_url:
                    media.append({"url": audio_url, "type": "driving_audio"})
                if media:
                    input_data["media"] = media

            if is_i2v:
                parameters = {"resolution": resolution, "duration": duration, "prompt_extend": True}
            else:
                size = self._SIZE_MAP.get(resolution, "1280*720")
                parameters = {"size": size, "prompt_extend": True}

            payload = {
                "model": self.model,
                "input": input_data,
                "parameters": parameters
            }

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code != 200:
                    return GenerationResult(
                        success=False,
                        error=f"创建视频生成任务失败: {response.text}"
                    )

                result = response.json()
                task_id = result.get("output", {}).get("task_id")

                if not task_id:
                    return GenerationResult(success=False, error="未获取视频任务ID")

                # 轮询任务状态
                task_url = f"{self.base_url}/api/v1/tasks/{task_id}"
                max_wait = 600
                waited = 0

                while waited < max_wait:
                    await asyncio.sleep(5)
                    waited += 5

                    task_response = await client.get(
                        task_url,
                        headers={"Authorization": f"Bearer {self.api_key}"}
                    )

                    if task_response.status_code != 200:
                        continue

                    task_result = task_response.json()
                    status = task_result.get("output", {}).get("task_status")

                    if status == "SUCCEEDED":
                        video_url = task_result.get("output", {}).get("video_url")

                        local_path = None
                        if project_id and video_url:
                            from .media_storage import download_and_save_video
                            local_path = await download_and_save_video(video_url, project_id)

                        return GenerationResult(
                            success=True,
                            content=video_url,
                            data={
                                "video_url": video_url,
                                "task_id": task_id,
                                "local_path": local_path
                            }
                        )
                    elif status == "FAILED":
                        error_msg = task_result.get("output", {}).get("message", "视频生成失败")
                        return GenerationResult(success=False, error=error_msg)

                return GenerationResult(success=False, error="视频生成超时")

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    async def test_connection(self) -> bool:
        try:
            result = await self.generate("test", duration=2, resolution="480p")
            return result.success
        except:
            return False


class CosyVoiceService(BaseAIService):
    """语音合成服务 — 使用 Qwen TTS (DashScope 原生接口)"""

    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com"

    AVAILABLE_VOICES = [
        "Cherry", "Ethan", "Jennifer", "Ryan", "Katerina", "Elias",
        "Nofish", "Chelsie", "Serena", "Jada", "Dylan", "Sunny",
        "Li", "Marcus", "Roy", "Peter", "Rocky",
    ]

    def __init__(
        self,
        api_key: str,
        model: str = "qwen3-tts-flash",
        voice: str = "Cherry",
        base_url: str = None,
        **kwargs
    ):
        effective_base_url = base_url or self.DEFAULT_BASE_URL
        super().__init__(api_key, effective_base_url, **kwargs)
        self.model = model
        self.default_voice = voice

    async def generate(
        self,
        text: str,
        voice: Optional[str] = None,
        format: str = "wav",
        sample_rate: int = 22050,
        **kwargs
    ) -> GenerationResult:
        """合成语音

        Args:
            text: 要合成的文本 (最大600字符)
            voice: 音色 (Cherry, Ethan, Jennifer 等)
            format: 音频格式 (wav, mp3)
            sample_rate: 采样率
        """
        try:
            url = f"{self.base_url}/api/v1/services/aigc/multimodal-generation/generation"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "input": {
                    "text": text,
                    "voice": voice or self.default_voice,
                    "language_type": "Chinese"
                }
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code != 200:
                    return GenerationResult(
                        success=False,
                        error=f"语音合成失败: {response.text[:300]}"
                    )

                result = response.json()
                audio_output = result.get("output", {}).get("audio", {})
                audio_url = audio_output.get("url") if isinstance(audio_output, dict) else None

                if not audio_url:
                    return GenerationResult(
                        success=False,
                        error="语音合成成功但未获取到音频URL"
                    )

                return GenerationResult(
                    success=True,
                    content=audio_url,
                    data={
                        "audio_url": audio_url,
                        "format": format,
                        "sample_rate": sample_rate,
                        "characters": result.get("usage", {}).get("characters", 0)
                    }
                )

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            result = await self.generate("测试")
            return result.success
        except:
            return False


class QwenImageService(BaseAIService):
    """千问图像生成服务 (Qwen-Image)"""

    def __init__(
        self,
        api_key: str,
        model: str = "qwen-image",
        base_url: str = "https://dashscope.aliyuncs.com",
        **kwargs
    ):
        super().__init__(api_key, base_url, **kwargs)
        self.model = model

    async def generate(
        self,
        prompt: str,
        size: str = "1024*1024",
        n: int = 1,
        project_id: Optional[int] = None,
        **kwargs
    ) -> GenerationResult:
        """生成图像"""
        try:
            url = f"{self.base_url}/api/v1/services/aigc/text2image/image-synthesis"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable"
            }

            payload = {
                "model": self.model,
                "input": {"prompt": prompt},
                "parameters": {
                    "size": size,
                    "n": n
                }
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code != 200:
                    return GenerationResult(
                        success=False,
                        error=f"创建任务失败: {response.text}"
                    )

                result = response.json()
                task_id = result.get("output", {}).get("task_id")

                if not task_id:
                    return GenerationResult(success=False, error="未获取任务ID")

                # 轮询
                task_url = f"{self.base_url}/api/v1/tasks/{task_id}"
                max_wait = 120
                waited = 0

                while waited < max_wait:
                    await asyncio.sleep(3)
                    waited += 3

                    task_response = await client.get(
                        task_url,
                        headers={"Authorization": f"Bearer {self.api_key}"}
                    )

                    if task_response.status_code != 200:
                        continue

                    task_result = task_response.json()
                    status = task_result.get("output", {}).get("task_status")

                    if status == "SUCCEEDED":
                        results = task_result.get("output", {}).get("results", [])
                        urls = [r.get("url") for r in results if r.get("url")]

                        local_paths = []
                        if project_id and urls:
                            from .media_storage import download_and_save_image
                            for i, url in enumerate(urls):
                                local_path = await download_and_save_image(url, project_id, prefix=f"img_{i}")
                                if local_path:
                                    local_paths.append(local_path)

                        return GenerationResult(
                            success=True,
                            content=json.dumps(urls),
                            data={"images": urls, "urls": urls, "task_id": task_id, "local_paths": local_paths}
                        )
                    elif status == "FAILED":
                        return GenerationResult(
                            success=False,
                            error=task_result.get("output", {}).get("message", "生成失败")
                        )

                return GenerationResult(success=False, error="生成超时")

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    async def test_connection(self) -> bool:
        try:
            result = await self.generate("一只猫", size="512*512")
            return result.success
        except:
            return False


def get_qwen_service(api_key: str, model: str = "qwen-plus", **kwargs) -> QwenService:
    """获取通义千问服务"""
    return QwenService(api_key=api_key, model=model, **kwargs)


def get_wanx_service(api_key: str, model: str = "wanx2.1-turbo", **kwargs) -> WanxImageService:
    """获取万相图像生成服务"""
    return WanxImageService(api_key=api_key, model=model, **kwargs)


def get_cosyvoice_service(api_key: str, voice: str = "longxiaochun", **kwargs) -> CosyVoiceService:
    """获取语音合成服务"""
    return CosyVoiceService(api_key=api_key, voice=voice, **kwargs)
