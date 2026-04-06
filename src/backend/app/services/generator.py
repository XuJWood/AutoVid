"""
AI Generator - High-level generation service that coordinates all AI services
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import ModelConfig, PromptTemplate
from .llm_service import get_llm_service, GenerationResult
from .image_service import get_image_service, ImageGenerationResult
from .video_service import get_video_service, VideoGenerationResult
from .voice_service import get_voice_service, VoiceResult


class AIGenerator:
    """High-level AI generation coordinator"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_model_config(self, name: str) -> Optional[ModelConfig]:
        """Get model configuration from database"""
        result = await self.db.execute(
            select(ModelConfig).where(ModelConfig.name == name, ModelConfig.is_active == True)
        )
        return result.scalar_one_or_none()

    async def get_prompt_template(self, template_type: str) -> Optional[PromptTemplate]:
        """Get prompt template from database"""
        result = await self.db.execute(
            select(PromptTemplate).where(
                PromptTemplate.type == template_type,
                PromptTemplate.is_default == True
            )
        )
        return result.scalar_one_or_none()

    async def generate_script(
        self,
        user_input: str,
        prompt_suffix: str = "",
        params: Dict[str, Any] = None
    ) -> GenerationResult:
        """Generate script using LLM"""
        config = await self.get_model_config("script")
        if not config:
            return GenerationResult(success=False, error="Script model not configured")

        template = await self.get_prompt_template("script")
        default_prompt = template.template if template else ""

        # Build final prompt
        final_prompt = default_prompt.format(
            user_input=user_input,
            user_prompt=prompt_suffix,
            **(params or {})
        )

        service = get_llm_service(
            provider=config.provider,
            api_key=config.api_key,
            model=config.model,
            base_url=config.base_url
        )

        return await service.generate(
            prompt=final_prompt,
            temperature=config.params.get("temperature", 0.7),
            max_tokens=config.params.get("max_tokens", 4000)
        )

    async def generate_character_image(
        self,
        character_info: Dict[str, Any],
        prompt_suffix: str = "",
        styles: List[str] = None,
        count_per_style: int = 4
    ) -> Dict[str, List[str]]:
        """Generate character images in multiple styles"""
        config = await self.get_model_config("image")
        if not config:
            return {}

        template = await self.get_prompt_template("character")

        results = {}
        styles = styles or ["realistic"]

        for style in styles:
            # Build prompt for this style
            prompt_vars = {
                **character_info,
                "style": style,
                "count_per_style": count_per_style,
                "user_prompt": prompt_suffix,
                "style_count": len(styles)
            }

            if template:
                prompt = template.template.format(**prompt_vars)
            else:
                prompt = f"Generate a {style} style character image: {character_info.get('appearance', '')}"

            service = get_image_service(
                provider=config.provider,
                api_key=config.api_key,
                **config.params
            )

            result = await service.generate(
                prompt=prompt,
                n=count_per_style
            )

            if result.success and result.data:
                results[style] = result.data.get("images", [])

        return results

    async def generate_video(
        self,
        scene_description: str,
        character_image: str = None,
        action_description: str = "",
        prompt_suffix: str = "",
        params: Dict[str, Any] = None
    ) -> VideoGenerationResult:
        """Generate video from scene description"""
        config = await self.get_model_config("video")
        if not config:
            return VideoGenerationResult(success=False, error="Video model not configured")

        template = await self.get_prompt_template("video")

        prompt_vars = {
            "scene_description": scene_description,
            "action_description": action_description,
            "user_prompt": prompt_suffix,
            **(params or {})
        }

        if template:
            prompt = template.template.format(**prompt_vars)
        else:
            prompt = scene_description

        service = get_video_service(
            provider=config.provider,
            api_key=config.api_key,
            base_url=config.base_url,
            **config.params
        )

        return await service.generate_video(
            prompt=prompt,
            image_url=character_image,
            **(params or {})
        )

    async def synthesize_voice(
        self,
        text: str,
        voice_config: Dict[str, Any] = None
    ) -> VoiceResult:
        """Synthesize voice from text"""
        config = await self.get_model_config("voice")
        if not config:
            return VoiceResult(success=False, error="Voice model not configured")

        voice_config = voice_config or {}

        service = get_voice_service(
            provider=config.provider,
            api_key=config.api_key,
            **{**config.params, **voice_config}
        )

        return await service.synthesize(text=text, **voice_config)

    async def test_model_connection(self, model_name: str) -> bool:
        """Test connection for a specific model"""
        config = await self.get_model_config(model_name)
        if not config:
            return False

        try:
            if model_name == "script":
                service = get_llm_service(config.provider, config.api_key, config.model, config.base_url)
            elif model_name == "image":
                service = get_image_service(config.provider, config.api_key, **config.params)
            elif model_name == "video":
                service = get_video_service(config.provider, config.api_key, config.base_url)
            elif model_name == "voice":
                service = get_voice_service(config.provider, config.api_key, **config.params)
            else:
                return False

            return await service.test_connection()
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
