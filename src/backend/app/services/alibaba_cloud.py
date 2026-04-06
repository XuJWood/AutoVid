"""
Alibaba Cloud Bailian (阿里云百炼) Services
Supports: 通义千问 (文本), 万相 (图像), CosyVoice (语音)
"""
import json
import asyncio
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
        **kwargs
    ) -> GenerationResult:
        """生成图像

        Args:
            prompt: 图像描述
            negative_prompt: 负向提示词
            size: 图像尺寸 (512*512, 720*1280, 1024*1024 等)
            n: 生成数量
            style: 风格 (photography, portrait, 3d, anime, oil_painting, watercolor, sketch 等)
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

                        return GenerationResult(
                            success=True,
                            content=json.dumps(urls),
                            data={"urls": urls, "task_id": task_id}
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


class CosyVoiceService(BaseAIService):
    """CosyVoice 语音合成服务"""

    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com"

    def __init__(
        self,
        api_key: str,
        model: str = "cosyvoice-v1",
        voice: str = "longxiaochun",
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
            text: 要合成的文本
            voice: 音色 (longxiaochun, longwan, longyue 等)
            format: 音频格式 (wav, mp3)
            sample_rate: 采样率
        """
        try:
            url = f"{self.base_url}/api/v1/services/audio/tts"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "input": {
                    "text": text
                },
                "parameters": {
                    "voice": voice or self.default_voice,
                    "format": format,
                    "sample_rate": sample_rate
                }
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code != 200:
                    return GenerationResult(
                        success=False,
                        error=f"语音合成失败: {response.text}"
                    )

                result = response.json()

                # 获取音频URL或base64
                audio_url = result.get("output", {}).get("audio")
                audio_data = result.get("output", {}).get("audio_data")

                return GenerationResult(
                    success=True,
                    content=audio_url or audio_data,
                    data={
                        "audio_url": audio_url,
                        "audio_data": audio_data,
                        "format": format,
                        "sample_rate": sample_rate
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
                        return GenerationResult(
                            success=True,
                            content=json.dumps(urls),
                            data={"urls": urls, "task_id": task_id}
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
