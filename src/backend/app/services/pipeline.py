"""
Video Generation Pipeline
一键生成完整短剧的流水线服务
"""
from typing import Optional, Dict, Any, List, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from enum import Enum
from dataclasses import dataclass
import asyncio
import json

from app.core.database import Project, Character, ModelConfig, GeneratedVideo
from .llm_service import get_llm_service
from .base import GenerationResult
from .image_service import get_image_service
from .video_service import get_video_service
from .voice_service import get_voice_service
from .prompts import get_script_prompt, get_character_prompt, get_storyboard_prompt
from .character_consistency import CharacterConsistencyService
from .cache_service import get_cache_service
from .resilience import retry


class PipelineStage(str, Enum):
    """流水线阶段"""
    SCRIPT = "script"
    CHARACTERS = "characters"
    STORYBOARD = "storyboard"
    SCENES = "scenes"
    VIDEOS = "videos"
    AUDIO = "audio"
    COMPLETED = "completed"


@dataclass
class PipelineProgress:
    """流水线进度"""
    stage: PipelineStage
    progress: float  # 0.0 - 1.0
    message: str
    data: Optional[Dict[str, Any]] = None


class VideoPipeline:
    """一键生成流水线"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.consistency_service = CharacterConsistencyService(db)
        self._progress_callbacks: List[Callable] = []

    def on_progress(self, callback: Callable):
        """注册进度回调"""
        self._progress_callbacks.append(callback)

    async def _report_progress(self, progress: PipelineProgress):
        """报告进度"""
        for callback in self._progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(progress)
                else:
                    callback(progress)
            except Exception:
                pass

    @retry(max_attempts=3, base_delay=2.0)
    async def _generate_with_retry(
        self,
        service,
        prompt: str,
        **kwargs
    ) -> GenerationResult:
        """带重试的生成"""
        return await service.generate(prompt=prompt, **kwargs)

    async def generate_script(
        self,
        project_id: int,
        user_input: str,
        prompt_suffix: str = ""
    ) -> Dict[str, Any]:
        """生成剧本"""
        # 获取项目信息
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # 获取模型配置
        config_result = await self.db.execute(
            select(ModelConfig).where(
                ModelConfig.name == "text",
                ModelConfig.is_active == True
            )
        )
        config = config_result.scalar_one_or_none()
        if not config:
            raise ValueError("Text model not configured")

        # 构建提示词
        system_prompt, user_prompt = get_script_prompt(
            name=project.name,
            type=project.type,
            style=project.style,
            genre=project.genre,
            duration=project.duration,
            platform=project.target_platform,
            description=project.description,
            user_input=user_input
        )

        if prompt_suffix:
            user_prompt += f"\n\n## 用户额外要求\n{prompt_suffix}"

        # 调用LLM生成
        service = get_llm_service(
            provider=config.provider,
            api_key=config.api_key,
            model=config.model,
            base_url=config.base_url
        )

        generation_result = await self._generate_with_retry(
            service,
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.8,
            max_tokens=8000
        )

        if not generation_result.success:
            raise Exception(f"Script generation failed: {generation_result.error}")

        # 解析结果
        script_data = generation_result.data or {}

        # 如果没有data，尝试从content解析JSON
        if not script_data and generation_result.content:
            try:
                content = generation_result.content.strip()
                # 处理 markdown 代码块
                if content.startswith("```json"):
                    content = content[7:]
                elif content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                script_data = json.loads(content.strip())
            except json.JSONDecodeError:
                script_data = {"raw_content": generation_result.content}

        # 保存到项目
        project.script_content = script_data
        project.status = "in_progress"
        await self.db.commit()

        return script_data

    async def generate_character_images(
        self,
        project_id: int,
        characters: List[Dict[str, Any]],
        style: str = "realistic"
    ) -> List[Dict[str, Any]]:
        """生成角色形象图"""
        results = []

        for char_data in characters:
            # 创建角色记录
            appearance = char_data.get("appearance", {})
            if isinstance(appearance, dict):
                appearance_str = appearance.get("face", "")
            else:
                appearance_str = str(appearance)

            clothing = char_data.get("clothing", {})
            if isinstance(clothing, dict):
                clothing_str = clothing.get("style", "")
            else:
                clothing_str = str(clothing)

            character = Character(
                project_id=project_id,
                name=char_data.get("name", "未命名角色"),
                age=char_data.get("age"),
                gender=char_data.get("gender"),
                occupation=char_data.get("occupation"),
                personality=char_data.get("personality"),
                appearance=appearance_str,
                clothing=clothing_str,
                style=style
            )
            self.db.add(character)
            await self.db.flush()

            # 生成角色形象图
            try:
                image_result = await self.consistency_service.generate_consistent_image(
                    character_id=character.id,
                    prompt=f"Character portrait, {appearance_str}, {style} style",
                    style=style
                )

                if image_result.success and image_result.data:
                    # 获取第一个图片URL
                    if isinstance(image_result.data, dict):
                        images = image_result.data.get("images", [])
                        character.selected_image = images[0] if images else None
                    else:
                        character.selected_image = image_result.data
            except Exception as e:
                print(f"Failed to generate image for {char_data.get('name')}: {e}")

            results.append({
                "id": character.id,
                "name": character.name,
                "image": character.selected_image
            })

        await self.db.commit()
        return results

    async def generate_storyboard(
        self,
        project_id: int,
        scene_index: int = 0
    ) -> Dict[str, Any]:
        """生成分镜脚本"""
        # 获取项目
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project or not project.script_content:
            raise ValueError("Project or script not found")

        script = project.script_content
        scenes = script.get("scenes", [])

        if scene_index >= len(scenes):
            raise ValueError(f"Scene index {scene_index} out of range")

        scene = scenes[scene_index]

        # 获取模型配置
        config_result = await self.db.execute(
            select(ModelConfig).where(
                ModelConfig.name == "text",
                ModelConfig.is_active == True
            )
        )
        config = config_result.scalar_one_or_none()
        if not config:
            raise ValueError("Text model not configured")

        # 构建提示词
        system_prompt, user_prompt = get_storyboard_prompt(
            script_content=script,
            scene_name=scene.get("name", ""),
            environment=scene.get("environment", ""),
            time=scene.get("time", ""),
            mood=scene.get("mood", "")
        )

        # 调用LLM生成
        service = get_llm_service(
            provider=config.provider,
            api_key=config.api_key,
            model=config.model,
            base_url=config.base_url
        )

        generation_result = await self._generate_with_retry(
            service,
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=4000
        )

        if not generation_result.success:
            raise Exception(f"Storyboard generation failed: {generation_result.error}")

        # 解析结果
        storyboard_data = generation_result.data or {}
        if not storyboard_data and generation_result.content:
            try:
                content = generation_result.content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                elif content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                storyboard_data = json.loads(content.strip())
            except json.JSONDecodeError:
                storyboard_data = {"raw_content": generation_result.content}

        return storyboard_data

    async def generate_short_drama(
        self,
        project_id: int,
        user_input: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        一键生成短剧

        Args:
            project_id: 项目ID
            user_input: 用户输入
            options: 生成选项

        Returns:
            生成结果
        """
        options = options or {}
        result = {
            "project_id": project_id,
            "stages": {}
        }

        try:
            # 阶段1: 剧本生成
            await self._report_progress(PipelineProgress(
                stage=PipelineStage.SCRIPT,
                progress=0.0,
                message="正在生成剧本..."
            ))

            script = await self.generate_script(
                project_id=project_id,
                user_input=user_input,
                prompt_suffix=options.get("prompt_suffix", "")
            )
            result["stages"]["script"] = script

            await self._report_progress(PipelineProgress(
                stage=PipelineStage.SCRIPT,
                progress=1.0,
                message="剧本生成完成",
                data={"character_count": len(script.get("characters", []))}
            ))

            # 阶段2: 角色形象生成
            characters = script.get("characters", [])
            if characters:
                await self._report_progress(PipelineProgress(
                    stage=PipelineStage.CHARACTERS,
                    progress=0.0,
                    message=f"正在生成{len(characters)}个角色形象..."
                ))

                character_images = await self.generate_character_images(
                    project_id=project_id,
                    characters=characters,
                    style=options.get("image_style", "realistic")
                )
                result["stages"]["characters"] = character_images

                await self._report_progress(PipelineProgress(
                    stage=PipelineStage.CHARACTERS,
                    progress=1.0,
                    message="角色形象生成完成"
                ))

            # 阶段3-5: 场景和视频生成 (可选)
            if options.get("generate_videos", False):
                # TODO: 实现场景图和视频生成
                pass

            # 完成
            await self._report_progress(PipelineProgress(
                stage=PipelineStage.COMPLETED,
                progress=1.0,
                message="短剧生成完成"
            ))

            return result

        except Exception as e:
            await self._report_progress(PipelineProgress(
                stage=PipelineStage.COMPLETED,
                progress=0.0,
                message=f"生成失败: {str(e)}"
            ))
            raise
