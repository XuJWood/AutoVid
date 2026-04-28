"""
Video Generation Pipeline
一键生成完整漫剧的流水线服务
"""
import os
from typing import Optional, Dict, Any, List, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from enum import Enum
from dataclasses import dataclass
import asyncio
import json

from app.core.database import Project, Character, ModelConfig, GeneratedVideo, Storyboard
from .llm_service import get_llm_service
from .base import GenerationResult
from .image_service import get_image_service
from .video_service import get_video_service
from .voice_service import get_voice_service
from .video_audio_service import (
    add_audio_to_video, get_voice_for_character,
    build_episode_dialogue_audio, generate_dialogue_audio_data
)
from .media_storage import get_episode_dir, save_image_to_path, save_video_to_path
from .prompts import get_script_prompt, get_character_prompt, get_storyboard_prompt
from .character_consistency import CharacterConsistencyService
from .cache_service import get_cache_service
from .resilience import retry


class PipelineStage(str, Enum):
    """流水线阶段"""
    SCRIPT = "script"
    CHARACTERS = "characters"
    EPISODES = "episodes"
    IMAGES = "images"
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


def _build_character_visual_prompt(characters: list) -> str:
    """构建角色外观描述文本，动漫风格"""
    parts = []
    for c in characters:
        if not c.appearance and not c.clothing:
            continue
        desc_parts = []
        if c.appearance:
            desc_parts.append(str(c.appearance))
        if c.clothing:
            desc_parts.append(f"穿着{c.clothing}")
        if c.gender:
            desc_parts.append(f"({c.gender})")
        parts.append(f"{c.name or '角色'}: {'; '.join(desc_parts)}")
    return "; ".join(parts) if parts else ""


def _enrich_video_prompt(
    base_prompt: str,
    description: str,
    char_descriptions: str
) -> str:
    """将角色外观描述融入视频提示词，生成中文动漫优化提示词"""

    if not char_descriptions:
        return f"日系动漫风，{description}，二次元，精致的色彩，流畅的动画，高画质"

    mentioned = []
    for char_desc in char_descriptions.split("; "):
        if ":" in char_desc:
            char_name = char_desc.split(":")[0].strip()
            if char_name and char_name in description:
                mentioned.append(char_desc)

    if not mentioned:
        mentioned = char_descriptions.split("; ")

    char_vis = "；".join(mentioned)
    return f"角色外观：{char_vis}。画面内容：{description}。日系动漫风，二次元，精致的色彩，流畅的动画，高画质"


def _extract_dialogue_from_episode(episode: dict) -> tuple:
    """从剧集数据中提取对话文本和角色。返回 (dialogue_text, speaker_list)。"""
    dialogues = episode.get("dialogues", [])
    if not dialogues:
        # 尝试从 script 文本中提取
        script = episode.get("script", "")
        if not script:
            return None, []
        return script, []

    lines = []
    speakers = []
    for d in dialogues:
        if isinstance(d, dict):
            speaker = d.get("speaker", "")
            text = d.get("text", "")
            if text:
                lines.append(f"{speaker}: {text}" if speaker else text)
                if speaker:
                    speakers.append(speaker)
        elif isinstance(d, str):
            lines.append(d)

    return "。".join(lines), speakers


def _match_voice_for_speaker(
    speaker: str,
    dialogue_text: str,
    char_by_name: dict
) -> str:
    """根据说话者匹配音色。返回音色名称。"""
    # 1. 优先使用明确的 speaker 字段匹配
    if speaker:
        for c_name, char_obj in char_by_name.items():
            if c_name and c_name in speaker:
                return get_voice_for_character(char_obj)

    # 2. 解析 "角色名：台词" 格式
    for prefix_sep in ["：", ": ", ":"]:
        if prefix_sep in dialogue_text:
            potential_name = dialogue_text.split(prefix_sep)[0].strip()
            for c_name, char_obj in char_by_name.items():
                if c_name and c_name in potential_name:
                    return get_voice_for_character(char_obj)
            break

    # 3. 检查对话文本中是否包含角色名
    for c_name, char_obj in char_by_name.items():
        if c_name and c_name in dialogue_text:
            return get_voice_for_character(char_obj)

    # 4. 默认
    if char_by_name:
        first_char = next(iter(char_by_name.values()))
        return get_voice_for_character(first_char)

    return "Cherry"


class VideoPipeline:
    """一键生成流水线（漫剧版）"""

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
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        config_result = await self.db.execute(
            select(ModelConfig).where(
                ModelConfig.name == "text",
                ModelConfig.is_active == True
            )
        )
        config = config_result.scalar_one_or_none()
        if not config:
            raise ValueError("Text model not configured")

        system_prompt, user_prompt = get_script_prompt(
            name=project.name,
            type=project.type,
            style=project.style,
            genre=project.genre,
            duration=project.duration,
            platform=project.target_platform,
            description=project.description,
            user_input=user_input,
            prompt_suffix=prompt_suffix,
            episode_tier=kwargs.get("episode_tier", "short")
        )

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
            max_tokens=32000
        )

        if not generation_result.success:
            raise Exception(f"Script generation failed: {generation_result.error}")

        script_data = generation_result.data or {}

        if not script_data and generation_result.content:
            try:
                content = generation_result.content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                elif content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                script_data = json.loads(content.strip())
            except json.JSONDecodeError:
                script_data = {"raw_content": generation_result.content}

        project.script_content = script_data
        project.status = "in_progress"
        await self.db.commit()

        return script_data

    async def generate_character_images(
        self,
        project_id: int,
        characters: List[Dict[str, Any]],
        style: str = "anime"
    ) -> List[Dict[str, Any]]:
        """生成角色形象图（动漫风格）"""
        results = []

        for char_data in characters:
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
                personality=str(char_data.get("personality", "")) if char_data.get("personality") else None,
                appearance=appearance_str,
                clothing=clothing_str,
                style=style
            )
            self.db.add(character)
            await self.db.flush()

            try:
                image_result = await self.consistency_service.generate_consistent_image(
                    character_id=character.id,
                    prompt=f"Anime character portrait, {appearance_str}, Japanese animation style, 日系动漫风",
                    style=style,
                    project_id=project_id
                )

                if image_result.success and image_result.data:
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

    async def generate_episodes(
        self,
        project_id: int,
    ) -> List[Storyboard]:
        """从剧本生成剧集（每集一个 Storyboard 行）"""
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project or not project.script_content:
            raise ValueError("Project or script not found")

        script = project.script_content

        # 优先读取 episodes，回退到 scenes（向后兼容）
        episodes = script.get("episodes", [])
        if not episodes and script.get("scenes"):
            episodes = self._convert_scenes_to_episodes(script.get("scenes", []))

        if not episodes:
            raise ValueError("No episodes found in script")

        from sqlalchemy import delete

        # 加载项目角色，构建 name → id 映射
        char_result = await self.db.execute(
            select(Character).where(Character.project_id == project_id)
        )
        db_characters = char_result.scalars().all()
        char_name_to_id = {}
        for c in db_characters:
            if c.name:
                char_name_to_id[c.name] = c.id

        await self.db.execute(
            delete(Storyboard).where(Storyboard.project_id == project_id)
        )

        episode_records = []
        for ep_idx, episode in enumerate(episodes):
            dialogues = episode.get("dialogues", [])

            description = episode.get("description", "")
            environment = episode.get("environment", "")
            time = episode.get("time", "")
            mood = episode.get("mood", "")
            title = episode.get("title", f"第{ep_idx + 1}集")

            # Map which characters appear in this episode
            episode_char_ids = []
            for d in dialogues:
                speaker = d.get("speaker", "") if isinstance(d, dict) else ""
                if speaker and speaker in char_name_to_id:
                    cid = char_name_to_id[speaker]
                    if cid not in episode_char_ids:
                        episode_char_ids.append(cid)

            image_prompt = (
                f"日系动漫风，二次元，{title}，{description}，"
                f"{environment}，{time}，精致的色彩，柔和的光影，高画质动漫插画"
            )

            video_prompt = (
                f"日系动漫，二次元动画风格，{title}，{description}，"
                f"{environment}，{mood}氛围，15秒动漫片段，"
                f"精致的动画，流畅的动作，高画质，日系动漫风"
            )

            sb = Storyboard(
                project_id=project_id,
                episode_number=ep_idx + 1,
                scene_index=ep_idx,
                shot_index=0,
                title=title,
                episode_script=episode.get("script", ""),
                dialogue_lines=dialogues,
                character_ids=episode_char_ids,
                description=description,
                image_prompt=image_prompt,
                video_prompt=video_prompt,
                duration=episode.get("duration", 15),
                status="pending"
            )
            self.db.add(sb)
            episode_records.append(sb)

        await self.db.commit()
        for sb in episode_records:
            await self.db.refresh(sb)
        return episode_records

    def _convert_scenes_to_episodes(self, scenes: list) -> list:
        """向后兼容：将旧格式 scenes 转换为 episodes"""
        episodes = []
        for scene in scenes:
            dialogues = []
            shots = scene.get("shots", [])
            for shot in shots:
                dialogue = shot.get("dialogue", "")
                if dialogue:
                    if isinstance(dialogue, dict):
                        dialogues.append({
                            "speaker": dialogue.get("speaker", ""),
                            "text": dialogue.get("content", ""),
                            "emotion": dialogue.get("emotion", "")
                        })
                    elif isinstance(dialogue, str):
                        dialogues.append({"speaker": "", "text": dialogue, "emotion": ""})

            script_parts = []
            for shot in shots:
                desc = shot.get("description", "")
                dia = shot.get("dialogue", "")
                if desc:
                    script_parts.append(desc)
                if dia:
                    if isinstance(dia, dict):
                        script_parts.append(f"{dia.get('speaker', '')}: {dia.get('content', '')}")
                    else:
                        script_parts.append(str(dia))

            episodes.append({
                "episode_number": scene.get("id", 1),
                "title": scene.get("name", ""),
                "location": scene.get("location", ""),
                "environment": scene.get("environment", ""),
                "time": scene.get("time", ""),
                "mood": scene.get("mood", ""),
                "conflict": scene.get("conflict", ""),
                "twist": scene.get("twist", ""),
                "description": scene.get("description", ""),
                "script": "\n".join(script_parts),
                "dialogues": dialogues,
                "duration": 20,
                "shots": shots
            })
        return episodes

    async def generate_short_drama(
        self,
        project_id: int,
        user_input: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        一键生成漫剧

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
                message="正在生成漫剧剧本..."
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
                    message=f"正在生成{len(characters)}个动漫角色形象..."
                ))

                character_images = await self.generate_character_images(
                    project_id=project_id,
                    characters=characters,
                    style=options.get("image_style", "anime")
                )
                result["stages"]["characters"] = character_images

                await self._report_progress(PipelineProgress(
                    stage=PipelineStage.CHARACTERS,
                    progress=1.0,
                    message="动漫角色形象生成完成"
                ))

            # 阶段3: 剧集生成
            await self._report_progress(PipelineProgress(
                stage=PipelineStage.EPISODES,
                progress=0.0,
                message="正在生成剧集..."
            ))

            episode_records = await self.generate_episodes(
                project_id=project_id,
            )
            result["stages"]["episodes"] = len(episode_records)

            await self._report_progress(PipelineProgress(
                stage=PipelineStage.EPISODES,
                progress=1.0,
                message=f"剧集生成完成，共 {len(episode_records)} 集",
                data={"episode_count": len(episode_records)}
            ))

            # 阶段4: 剧集封面生成（按出场角色定制 prompt，女性性感化）
            if options.get("generate_images", False) and episode_records:
                image_config = await self.db.execute(
                    select(ModelConfig).where(
                        ModelConfig.name == "image",
                        ModelConfig.is_active == True
                    )
                )
                image_config = image_config.scalar_one_or_none()

                if image_config:
                    await self._report_progress(PipelineProgress(
                        stage=PipelineStage.IMAGES,
                        progress=0.0,
                        message=f"正在生成 {len(episode_records)} 集的封面图..."
                    ))

                    image_service = get_image_service(
                        provider=image_config.provider,
                        api_key=image_config.api_key,
                        model=image_config.model,
                        base_url=image_config.base_url,
                        **(image_config.params or {})
                    )

                    # Build character lookup for per-episode cover prompts
                    char_result = await self.db.execute(
                        select(Character).where(Character.project_id == project_id)
                    )
                    all_chars = char_result.scalars().all()
                    char_by_id = {c.id: c for c in all_chars}

                    total_eps = len(episode_records)
                    for i, ep in enumerate(episode_records):
                        await self._report_progress(PipelineProgress(
                            stage=PipelineStage.IMAGES,
                            progress=(i + 1) / total_eps if total_eps else 0,
                            message=f"正在生成第 {ep.episode_number} 集封面图..."
                        ))
                        try:
                            # Get characters for this episode
                            ep_chars = [char_by_id[cid] for cid in (ep.character_ids or []) if cid in char_by_id]

                            # Build character-aware anime cover prompt
                            has_female = any(getattr(c, "gender", None) == "女" for c in ep_chars)
                            char_descs = []
                            for c in ep_chars:
                                parts = []
                                if c.name:
                                    parts.append(c.name)
                                if c.appearance:
                                    parts.append(str(c.appearance))
                                if c.clothing:
                                    parts.append(f"穿着{c.clothing}")
                                if parts:
                                    char_descs.append("，".join(parts))
                            char_text = "；".join(char_descs) if char_descs else ""

                            if has_female:
                                style_tags = (
                                    "beautiful anime girl, sexy cute alluring, delicate features, "
                                    "soft facial lines, charming expression, eye-catching pose, "
                                    "vibrant colors, high quality anime illustration, clean lineart"
                                )
                            else:
                                style_tags = (
                                    "handsome anime guy, sharp features, cool demeanor, "
                                    "vibrant colors, high quality anime illustration, clean lineart"
                                )

                            cover_prompt = (
                                f"Japanese anime style, 日系动漫风, 二次元, "
                                f"{ep.title or ''}, {ep.description or ''}, {char_text}, "
                                f"{style_tags}, masterpiece, soft lighting"
                            )

                            img_result = await image_service.generate(prompt=cover_prompt, project_id=project_id)
                            if img_result.success and img_result.data:
                                images = img_result.data.get("images", [])
                                if images:
                                    # Save to episode folder
                                    ep_dir = get_episode_dir(project_id, ep.episode_number)
                                    cover_path = os.path.join(ep_dir, "cover.png")
                                    saved = await save_image_to_path(images[0], cover_path)
                                    ep.image_url = saved if saved else images[0]
                                    ep.image_prompt = cover_prompt
                                    ep.status = "completed"
                        except Exception as e:
                            print(f"Cover generation failed for episode {ep.episode_number}: {e}")

                    await self.db.commit()

                    await self._report_progress(PipelineProgress(
                        stage=PipelineStage.IMAGES,
                        progress=1.0,
                        message="剧集封面图生成完成"
                    ))

            # 阶段5: 剧集视频生成（每集 TTS 配音 + 视频口型同步）
            if options.get("generate_videos", False) and episode_records:
                video_config = await self.db.execute(
                    select(ModelConfig).where(
                        ModelConfig.name == "video",
                        ModelConfig.is_active == True
                    )
                )
                video_config = video_config.scalar_one_or_none()

                voice_config = None
                if options.get("generate_audio", True):
                    vc = await self.db.execute(
                        select(ModelConfig).where(
                            ModelConfig.name == "voice",
                            ModelConfig.is_active == True
                        )
                    )
                    voice_config = vc.scalar_one_or_none()

                if video_config:
                    await self._report_progress(PipelineProgress(
                        stage=PipelineStage.VIDEOS,
                        progress=0.0,
                        message=f"正在生成 {len(episode_records)} 集的视频..."
                    ))

                    video_service = get_video_service(
                        provider=video_config.provider,
                        api_key=video_config.api_key,
                        model=video_config.model,
                        base_url=video_config.base_url,
                        **(video_config.params or {})
                    )

                    char_result = await self.db.execute(
                        select(Character).where(Character.project_id == project_id)
                    )
                    db_characters = char_result.scalars().all()
                    char_by_id = {c.id: c for c in db_characters}

                    total_eps = len(episode_records)
                    for i, ep in enumerate(episode_records):
                        await self._report_progress(PipelineProgress(
                            stage=PipelineStage.VIDEOS,
                            progress=(i + 1) / total_eps if total_eps else 0,
                            message=f"正在生成第 {ep.episode_number} 集视频..."
                        ))
                        try:
                            # Get characters for this episode
                            ep_chars = [char_by_id[cid] for cid in (ep.character_ids or []) if cid in char_by_id]
                            char_descriptions = _build_character_visual_prompt(ep_chars)

                            enriched_prompt = _enrich_video_prompt(
                                ep.video_prompt or "",
                                ep.description or "",
                                char_descriptions
                            )

                            # First frame: episode cover image, fallback to character front view
                            first_frame = None
                            if ep.image_url:
                                first_frame = ep.image_url
                            elif ep_chars:
                                for c in ep_chars:
                                    if c.selected_image:
                                        first_frame = c.selected_image
                                        break

                            # Generate TTS for driving_audio (lip sync)
                            driving_audio = None
                            if ep.dialogue_lines and voice_config and voice_config.api_key:
                                audio_data = await build_episode_dialogue_audio(
                                    dialogue_lines=ep.dialogue_lines,
                                    characters=ep_chars,
                                    api_key=voice_config.api_key,
                                    project_id=project_id,
                                    episode_number=ep.episode_number
                                )
                                if audio_data:
                                    driving_audio = audio_data.get("audio_url")

                            vid_result = await video_service.generate(
                                prompt=enriched_prompt,
                                image_url=first_frame,
                                audio_url=driving_audio,
                                duration=15,
                                resolution="1080P",
                                project_id=project_id
                            )
                            if vid_result.success and vid_result.data:
                                video_url = vid_result.data.get("local_path") or vid_result.data.get("video_url")
                                if video_url:
                                    ep.video_url = video_url
                                    ep.video_prompt = enriched_prompt
                                    ep.status = "completed"
                                    ep.duration = 15
                        except Exception as e:
                            print(f"Video generation failed for episode {ep.episode_number}: {e}")

                    await self.db.commit()

                    await self._report_progress(PipelineProgress(
                        stage=PipelineStage.VIDEOS,
                        progress=1.0,
                        message="剧集视频生成完成（配音 + 口型同步）"
                    ))

            # 阶段6: 配音（仅用于补配音 — 正常流程已集成到阶段5）
            if options.get("generate_audio_standalone", False) and episode_records:
                voice_config = await self.db.execute(
                    select(ModelConfig).where(
                        ModelConfig.name == "voice",
                        ModelConfig.is_active == True
                    )
                )
                voice_config = voice_config.scalar_one_or_none()

                if voice_config:
                    await self._report_progress(PipelineProgress(
                        stage=PipelineStage.AUDIO,
                        progress=0.0,
                        message=f"正在为 {len(episode_records)} 集补充配音..."
                    ))

                    char_result = await self.db.execute(
                        select(Character).where(Character.project_id == project_id)
                    )
                    characters = char_result.scalars().all()
                    char_by_name = {}
                    for c in characters:
                        if c.name:
                            char_by_name[c.name] = c

                    total_eps = len(episode_records)
                    audio_count = 0
                    for i, ep in enumerate(episode_records):
                        if not ep.video_url or ep.status != "completed":
                            continue

                        combined_text = None
                        if ep.dialogue_lines:
                            parts = []
                            for d in ep.dialogue_lines:
                                if isinstance(d, dict):
                                    speaker = d.get("speaker", "")
                                    text = d.get("text", "")
                                    parts.append(f"{speaker}: {text}" if speaker else text)
                            combined_text = "。".join(parts)

                        if not combined_text:
                            combined_text = ep.episode_script or ep.description or ""

                        if not combined_text:
                            continue

                        try:
                            speaker = ""
                            if ep.dialogue_lines and len(ep.dialogue_lines) > 0:
                                d0 = ep.dialogue_lines[0]
                                if isinstance(d0, dict):
                                    speaker = d0.get("speaker", "")
                            voice = _match_voice_for_speaker(speaker, combined_text, char_by_name)

                            merged_path = await add_audio_to_video(
                                video_url=ep.video_url,
                                dialogue=combined_text,
                                voice=voice,
                                project_id=project_id,
                                api_key=voice_config.api_key,
                                shot_prefix=f"episode{ep.episode_number}"
                            )
                            if merged_path:
                                ep.video_url = merged_path
                                ep.audio_url = merged_path
                                audio_count += 1
                        except Exception as e:
                            print(f"Audio generation failed for episode {ep.episode_number}: {e}")

                    await self.db.commit()

                    await self._report_progress(PipelineProgress(
                        stage=PipelineStage.AUDIO,
                        progress=1.0,
                        message=f"补充配音完成, {audio_count} 集已配音"
                    ))

            # 完成
            await self._report_progress(PipelineProgress(
                stage=PipelineStage.COMPLETED,
                progress=1.0,
                message="漫剧生成完成"
            ))

            return result

        except Exception as e:
            await self._report_progress(PipelineProgress(
                stage=PipelineStage.COMPLETED,
                progress=0.0,
                message=f"生成失败: {str(e)}"
            ))
            raise
