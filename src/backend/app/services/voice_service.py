"""
Voice/TTS Service - Text to Speech synthesis
"""
import base64
from typing import Optional, Dict, Any, List
from enum import Enum
import httpx

from .base import BaseAIService, GenerationResult


class VoiceResult:
    """Result of voice synthesis"""
    def __init__(self, success: bool, audio_url: str = None, audio_data: bytes = None, error: str = None):
        self.success = success
        self.audio_url = audio_url
        self.audio_data = audio_data
        self.error = error


class ElevenLabsService(BaseAIService):
    """ElevenLabs TTS service"""

    def __init__(self, api_key: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM", **kwargs):
        super().__init__(api_key, **kwargs)
        self.voice_id = voice_id
        self.api_url = "https://api.elevenlabs.io/v1"

    async def synthesize(
        self,
        text: str,
        voice_id: str = None,
        model: str = "eleven_multilingual_v2",
        stability: float = 0.5,
        **kwargs
    ) -> VoiceResult:
        """Synthesize speech from text"""
        voice = voice_id or self.voice_id

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/text-to-speech/{voice}",
                    headers={
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": text,
                        "model_id": model,
                        "voice_settings": {
                            "stability": stability,
                            "similarity_boost": 0.75
                        }
                    },
                    timeout=60.0
                )

                if response.status_code != 200:
                    return VoiceResult(
                        success=False,
                        error=f"API error: {response.status_code}"
                    )

                audio_data = response.content
                return VoiceResult(
                    success=True,
                    audio_data=audio_data
                )
        except Exception as e:
            return VoiceResult(success=False, error=str(e))

    async def get_voices(self) -> List[Dict[str, Any]]:
        """Get available voices"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/voices",
                    headers={"xi-api-key": self.api_key},
                    timeout=10.0
                )

                if response.status_code != 200:
                    return []

                data = response.json()
                return data.get("voices", [])
        except:
            return []

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        result = await self.synthesize(prompt, **kwargs)
        return GenerationResult(
            success=result.success,
            error=result.error,
            data={"audio_available": result.audio_data is not None}
        )

    async def test_connection(self) -> bool:
        try:
            voices = await self.get_voices()
            return len(voices) > 0
        except:
            return False


class AzureTTSService(BaseAIService):
    """Azure Cognitive Services TTS"""

    def __init__(self, api_key: str, region: str = "eastasia", voice: str = "zh-CN-YunxiNeural", **kwargs):
        super().__init__(api_key, **kwargs)
        self.region = region
        self.voice = voice
        self.api_url = f"https://{region}.tts.speech.microsoft.com"

    async def synthesize(
        self,
        text: str,
        voice: str = None,
        rate: float = 1.0,
        pitch: str = "+0Hz",
        **kwargs
    ) -> VoiceResult:
        """Synthesize speech from text"""
        voice_name = voice or self.voice

        try:
            ssml = f"""
            <speak version='1.0' xml:lang='zh-CN'>
                <voice name='{voice_name}'>
                    <prosody rate='{rate}' pitch='{pitch}'>
                        {text}
                    </prosody>
                </voice>
            </speak>
            """

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/cognitiveservices/v1",
                    headers={
                        "Ocp-Apim-Subscription-Key": self.api_key,
                        "Content-Type": "application/ssml+xml",
                        "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3"
                    },
                    content=ssml.encode('utf-8'),
                    timeout=60.0
                )

                if response.status_code != 200:
                    return VoiceResult(
                        success=False,
                        error=f"API error: {response.status_code}"
                    )

                audio_data = response.content
                return VoiceResult(
                    success=True,
                    audio_data=audio_data
                )
        except Exception as e:
            return VoiceResult(success=False, error=str(e))

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        result = await self.synthesize(prompt, **kwargs)
        return GenerationResult(
            success=result.success,
            error=result.error,
            data={"audio_available": result.audio_data is not None}
        )

    async def test_connection(self) -> bool:
        try:
            result = await self.synthesize("测试")
            return result.success
        except:
            return False


class OpenAITTSService(BaseAIService):
    """OpenAI TTS service"""

    def __init__(self, api_key: str, model: str = "tts-1", voice: str = "alloy", **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = model
        self.voice = voice
        self.api_url = "https://api.openai.com/v1"

    async def synthesize(
        self,
        text: str,
        voice: str = None,
        model: str = None,
        **kwargs
    ) -> VoiceResult:
        """Synthesize speech from text"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/audio/speech",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model or self.model,
                        "input": text,
                        "voice": voice or self.voice
                    },
                    timeout=60.0
                )

                if response.status_code != 200:
                    return VoiceResult(
                        success=False,
                        error=f"API error: {response.status_code}"
                    )

                audio_data = response.content
                return VoiceResult(
                    success=True,
                    audio_data=audio_data
                )
        except Exception as e:
            return VoiceResult(success=False, error=str(e))

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        result = await self.synthesize(prompt, **kwargs)
        return GenerationResult(
            success=result.success,
            error=result.error,
            data={"audio_available": result.audio_data is not None}
        )

    async def test_connection(self) -> bool:
        try:
            result = await self.synthesize("Hello")
            return result.success
        except:
            return False


def get_voice_service(provider: str, api_key: str, **kwargs) -> BaseAIService:
    """Factory function to get voice service"""
    # 阿里云百炼语音合成
    if provider.lower() in ["cosyvoice", "alibaba", "aliyun", "qwen-tts"]:
        from .alibaba_cloud import CosyVoiceService
        voice = kwargs.get("voice", "longxiaochun")
        return CosyVoiceService(api_key=api_key, voice=voice, **kwargs)

    services = {
        "elevenlabs": ElevenLabsService,
        "eleven": ElevenLabsService,
        "azure": AzureTTSService,
        "openai": OpenAITTSService,
        "tts": OpenAITTSService
    }

    service_class = services.get(provider.lower())
    if not service_class:
        raise ValueError(f"Unknown voice provider: {provider}")

    return service_class(api_key=api_key, **kwargs)
