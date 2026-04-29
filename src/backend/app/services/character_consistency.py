"""
Character Consistency Service
保持角色在多张图片中外观一致
"""
import os
import shutil
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib

from app.core.database import Character, ModelConfig
from .base import BaseAIService, GenerationResult
from .image_service import get_image_service
from .media_storage import get_character_dir, save_image_to_path, local_path_to_url


class CharacterConsistencyService:
    """角色一致性服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._reference_cache: Dict[int, str] = {}

    async def get_character_reference(self, character_id: int) -> Optional[str]:
        """获取角色参考图"""
        result = await self.db.execute(
            select(Character).where(Character.id == character_id)
        )
        character = result.scalar_one_or_none()
        if character and character.selected_image:
            return character.selected_image
        return None

    async def generate_consistent_image(
        self,
        character_id: int,
        prompt: str,
        scene_context: Optional[Dict[str, Any]] = None,
        style: str = "anime",
        project_id: Optional[int] = None
    ) -> GenerationResult:
        """
        生成角色一致的形象图

        Args:
            character_id: 角色ID
            prompt: 场景描述
            scene_context: 场景上下文
            style: 图像风格

        Returns:
            生成结果
        """
        # 获取角色信息
        result = await self.db.execute(
            select(Character).where(Character.id == character_id)
        )
        character = result.scalar_one_or_none()
        if not character:
            return GenerationResult(success=False, error="Character not found")

        # 获取模型配置
        config_result = await self.db.execute(
            select(ModelConfig).where(
                ModelConfig.name == "image",
                ModelConfig.is_active == True
            )
        )
        config = config_result.scalar_one_or_none()
        if not config:
            return GenerationResult(success=False, error="Image model not configured")

        # 构建一致性提示词
        consistency_prompt = self._build_consistency_prompt(
            character=character,
            scene_prompt=prompt,
            scene_context=scene_context or {},
            style=style
        )

        # 获取图像服务
        service = get_image_service(
            provider=config.provider,
            api_key=config.api_key,
            **(config.params or {})
        )

        # 使用 character.project_id
        pid = project_id or character.project_id

        # 如果有参考图，使用reference模式
        if character.selected_image:
            result = await self._generate_with_reference(
                service=service,
                prompt=consistency_prompt,
                reference_image=character.selected_image,
                strength=0.6,  # 保持60%的原角色特征
                project_id=pid
            )
        else:
            result = await service.generate(prompt=consistency_prompt, project_id=pid)

        return result

    async def _generate_with_reference(
        self,
        service: BaseAIService,
        prompt: str,
        reference_image: str,
        strength: float = 0.6,
        project_id: Optional[int] = None
    ) -> GenerationResult:
        """
        使用参考图生成图像
        """
        enhanced_prompt = f"{prompt}, consistent with reference image, maintain character features"
        result = await service.generate(prompt=enhanced_prompt, project_id=project_id)
        return result

    def _build_consistency_prompt(
        self,
        character: Character,
        scene_prompt: str,
        scene_context: Dict[str, Any],
        style: str
    ) -> str:
        """构建一致性提示词"""
        parts = []

        # 角色核心特征（必须包含）
        if character.appearance:
            parts.append(f"Character appearance: {character.appearance}")

        # 服装信息
        if character.clothing:
            parts.append(f"Clothing: {character.clothing}")

        # 场景描述
        parts.append(f"Scene: {scene_prompt}")

        # 场景上下文
        if scene_context:
            if "lighting" in scene_context:
                parts.append(f"Lighting: {scene_context['lighting']}")
            if "mood" in scene_context:
                parts.append(f"Mood: {scene_context['mood']}")

        # 风格
        parts.append(f"Style: {style}")

        # 质量标签
        parts.extend([
            "high quality",
            "detailed",
            "anime style",
            "Japanese animation",
            "consistent character design"
        ])

        return ", ".join(parts)

    async def batch_generate_scenes(
        self,
        character_id: int,
        scenes: List[Dict[str, Any]],
        style: str = "realistic"
    ) -> List[GenerationResult]:
        """
        批量生成角色的多个场景图

        Args:
            character_id: 角色ID
            scenes: 场景列表
            style: 图像风格

        Returns:
            生成结果列表
        """
        results = []
        for scene in scenes:
            result = await self.generate_consistent_image(
                character_id=character_id,
                prompt=scene.get("description", ""),
                scene_context=scene.get("context"),
                style=style
            )
            results.append(result)
        return results

    async def generate_three_views(
        self,
        character_id: int,
        style: str = "anime",
        prompt_suffix: str = "",
        custom_prompt: str = ""
    ) -> Dict[str, Any]:
        """
        生成角色设计图：三视图 + 表情特写 合并在同一张图上
        - 三视图：正面/侧面/背面全身
        - 表情特写：至少3个表情（开心/愤怒/惊讶/悲伤等）
        - 全部排列在一张角色设计表（character design sheet）上

        Directory: media/projects/{project_id}/characters/{name}/design_sheet.png

        If custom_prompt is provided, it overrides the auto-generated prompt.
        """
        result = await self.db.execute(
            select(Character).where(Character.id == character_id)
        )
        character = result.scalar_one_or_none()
        if not character:
            return {"error": "Character not found"}

        config_result = await self.db.execute(
            select(ModelConfig).where(
                ModelConfig.name == "image",
                ModelConfig.is_active == True
            )
        )
        config = config_result.scalar_one_or_none()
        if not config:
            return {"error": "Image model not configured"}

        if custom_prompt:
            combined_prompt = custom_prompt
        else:
            desc_parts = []
            if character.appearance:
                desc_parts.append(character.appearance)
            if character.clothing:
                desc_parts.append(f"wearing {character.clothing}")
            base_desc = ", ".join(desc_parts) if desc_parts else character.name
            if prompt_suffix:
                base_desc += f", {prompt_suffix}"

            effective_style = style or "anime"

            # Build style tags for female characters
            style_tags = "Japanese anime style, 日系动漫, vibrant colors, high quality, clean lineart"
            if character.gender == "女":
                style_tags += ", beautiful anime girl, sexy cute, alluring, delicate features, soft facial lines, eye-catching"

            # Single combined prompt for character design sheet
            # Generates a single image with: three full-body views + 4 facial expressions, arranged in a grid
            combined_prompt = (
                f"character design sheet, full body turnaround, "
                f"{base_desc}, "
                f"{effective_style} style, {style_tags}, "
                f"multiple views: front view full body standing straight looking at viewer, "
                f"side view full body standing at 45 degree angle, "
                f"back view full body from behind, "
                f"and facial expressions chart with 4 expressions: happy smiling, angry shouting, surprised shocked, sad crying, "
                f"all arranged in a clean professional character reference sheet layout, "
                f"clean white background, character design reference sheet, model sheet, high resolution"
            )

        service = get_image_service(
            provider=config.provider,
            api_key=config.api_key,
            model=config.model,
            base_url=config.base_url,
            **(config.params or {})
        )

        char_dir = get_character_dir(character.project_id, character.name)

        try:
            gen_result = await service.generate(prompt=combined_prompt, project_id=character.project_id)
            if gen_result.success and gen_result.data:
                images = gen_result.data.get("images", [])
                if images:
                    # Download as design_sheet.png
                    design_path = os.path.join(char_dir, "design_sheet.png")
                    saved = await save_image_to_path(images[0], design_path)

                    # Convert local absolute path → /media/... URL for storage & frontend rendering
                    design_url = local_path_to_url(saved) if saved else images[0]

                    views = {
                        "design_sheet": design_url,
                        "combined": True,
                        "expressions": ["happy", "angry", "surprised", "sad"],
                        "views": ["front", "side", "back"]
                    }

                    all_images = [design_url]

                    # Save a copy as reference.png for backward compatibility
                    if saved and os.path.exists(saved):
                        ref_path = os.path.join(char_dir, "reference.png")
                        shutil.copy(saved, ref_path)

                    character.three_views = views
                    character.alternative_images = all_images
                    character.selected_image = design_url
                    await self.db.commit()

                    return {
                        "character_id": character_id,
                        "views": views,
                        "selected_image": character.selected_image,
                        "three_views": character.three_views,
                        "prompt_used": combined_prompt,
                        "message": "三视图+表情设计图生成完成"
                    }
                else:
                    return {"error": "No images generated"}
            else:
                return {"error": f"Image generation failed: {gen_result.error}"}
        except Exception as e:
            print(f"Design sheet generation failed: {e}")
            return {"error": str(e)}

    async def update_character_reference(
        self,
        character_id: int,
        image_url: str
    ) -> bool:
        """
        更新角色参考图

        Args:
            character_id: 角色ID
            image_url: 新的参考图URL

        Returns:
            是否成功
        """
        result = await self.db.execute(
            select(Character).where(Character.id == character_id)
        )
        character = result.scalar_one_or_none()
        if not character:
            return False

        character.selected_image = image_url
        await self.db.commit()

        # 清除缓存
        if character_id in self._reference_cache:
            del self._reference_cache[character_id]

        return True

    def generate_character_hash(self, character: Character) -> str:
        """
        生成角色特征哈希，用于追踪一致性

        Args:
            character: 角色对象

        Returns:
            哈希字符串
        """
        features = {
            "appearance": character.appearance or "",
            "clothing": character.clothing or "",
            "gender": character.gender or "",
            "age": character.age or 0,
            "style": character.style or "anime"
        }
        content = str(sorted(features.items()))
        return hashlib.md5(content.encode()).hexdigest()[:12]
