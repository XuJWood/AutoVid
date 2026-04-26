"""
Storyboard API endpoints — 漫剧剧集管理接口
Each row = one episode (~20s anime segment)
"""
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db, Storyboard, Project, ModelConfig, Character
from app.services.image_service import get_image_service
from app.services.video_service import get_video_service
from app.services.video_audio_service import (
    build_episode_dialogue_audio, get_voice_for_character, add_audio_to_video
)
from app.services.media_storage import (
    get_episode_dir, save_image_to_path, save_video_to_path, local_path_to_url
)


router = APIRouter()


def _build_character_visual_prompt(characters: list) -> str:
    """构建动漫角色外观描述文本"""
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


def _enrich_video_prompt(base_prompt: str, description: str, char_descriptions: str) -> str:
    """将角色外观描述融入视频提示词，生成日系动漫优化提示词"""
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


def _build_sexy_cover_prompt(episode_title: str, description: str, characters: list) -> str:
    """为剧集封面构建吸引眼球的动漫风格 prompt"""
    has_female = any(getattr(c, "gender", None) == "女" for c in characters)

    char_descs = []
    for c in characters:
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
        style = (
            f"Japanese anime style, 日系动漫风, 二次元, vibrant colors, "
            f"beautiful anime girl, sexy cute alluring, delicate features, "
            f"soft facial lines, charming expression, eye-catching pose, "
            f"high quality anime illustration, clean lineart, "
            f"soft lighting, masterpiece"
        )
    else:
        style = (
            f"Japanese anime style, 日系动漫风, 二次元, vibrant colors, "
            f"handsome anime guy, sharp features, cool demeanor, "
            f"high quality anime illustration, clean lineart, "
            f"soft lighting, masterpiece"
        )

    scene = f"{episode_title}, {description}, {char_text}"
    return f"{scene}, {style}"


class StoryboardResponse(BaseModel):
    """剧集响应模型"""
    id: int
    project_id: int
    episode_number: int
    scene_index: int
    shot_index: int
    title: Optional[str] = None
    episode_script: Optional[str] = None
    dialogue_lines: Optional[list] = None
    character_ids: Optional[list] = None
    shot_type: Optional[str] = None
    description: Optional[str] = None
    image_prompt: Optional[str] = None
    video_prompt: Optional[str] = None
    duration: int = 20
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    status: str = "pending"

    class Config:
        from_attributes = True


@router.get("/project/{project_id}", response_model=List[StoryboardResponse])
async def get_project_storyboard(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取项目的所有剧集"""
    result = await db.execute(
        select(Storyboard).where(Storyboard.project_id == project_id).order_by(Storyboard.episode_number)
    )
    return result.scalars().all()


@router.post("/project/{project_id}/generate", response_model=List[StoryboardResponse])
async def generate_storyboard(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """从剧本内容生成剧集（每集一个 Storyboard 行），自动映射出场角色"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    script = project.script_content
    if not script:
        raise HTTPException(status_code=400, detail="No script content to generate episodes")

    # 优先读取 episodes，回退到 scenes（向后兼容）
    episodes = script.get("episodes", [])
    if not episodes and script.get("scenes"):
        episodes = _convert_scenes_to_episodes(script.get("scenes", []))

    if not episodes:
        raise HTTPException(status_code=400, detail="No episodes or scenes found in script")

    # 加载项目角色，构建 name → id 映射
    char_result = await db.execute(
        select(Character).where(Character.project_id == project_id)
    )
    db_characters = char_result.scalars().all()
    char_name_to_id = {}
    for c in db_characters:
        if c.name:
            char_name_to_id[c.name] = c.id

    # 清除现有剧集
    await db.execute(
        delete(Storyboard).where(Storyboard.project_id == project_id)
    )

    # 创建剧集条目（每集一行）
    storyboards = []
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
        db.add(sb)
        storyboards.append(sb)

    await db.commit()
    for sb in storyboards:
        await db.refresh(sb)
    return storyboards


def _convert_scenes_to_episodes(scenes: list) -> list:
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
            "environment": scene.get("environment", ""),
            "time": scene.get("time", ""),
            "mood": scene.get("mood", ""),
            "description": scene.get("description", ""),
            "script": "\n".join(script_parts),
            "dialogues": dialogues,
            "duration": 15,
            "shots": shots
        })
    return episodes


@router.post("/{storyboard_id}/generate-image")
async def generate_storyboard_image(
    storyboard_id: int,
    db: AsyncSession = Depends(get_db)
):
    """为剧集生成封面图（按出场角色定制 prompt，女性角色性感化）"""
    result = await db.execute(select(Storyboard).where(Storyboard.id == storyboard_id))
    storyboard = result.scalar_one_or_none()
    if not storyboard:
        raise HTTPException(status_code=404, detail="Episode not found")

    config_result = await db.execute(
        select(ModelConfig).where(ModelConfig.name == "image", ModelConfig.is_active == True)
    )
    config = config_result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=400, detail="Image model not configured")

    # 加载出场角色
    ep_characters = []
    if storyboard.character_ids:
        char_result = await db.execute(
            select(Character).where(Character.id.in_(storyboard.character_ids))
        )
        ep_characters = char_result.scalars().all()

    # 构建角色感知封面 prompt
    cover_prompt = _build_sexy_cover_prompt(
        episode_title=storyboard.title or "",
        description=storyboard.description or "",
        characters=ep_characters
    )

    service = get_image_service(
        provider=config.provider,
        api_key=config.api_key,
        model=config.model,
        base_url=config.base_url,
        **(config.params or {})
    )

    storyboard.status = "processing"
    await db.commit()

    try:
        result = await service.generate(prompt=cover_prompt, project_id=storyboard.project_id)
        if result.success and result.data:
            images = result.data.get("images", [])
            if images:
                # Save to episode folder
                ep_dir = get_episode_dir(storyboard.project_id, storyboard.episode_number)
                cover_path = os.path.join(ep_dir, "cover.png")
                saved = await save_image_to_path(images[0], cover_path)
                storyboard.image_url = saved if saved else images[0]
                storyboard.image_prompt = cover_prompt
                storyboard.status = "completed"
            else:
                storyboard.status = "failed"
        else:
            storyboard.status = "failed"
    except Exception as e:
        storyboard.status = "failed"
        print(f"Failed to generate cover image: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

    storyboard.updated_at = datetime.utcnow()
    await db.commit()
    return {"status": storyboard.status, "image_url": storyboard.image_url}


@router.post("/{storyboard_id}/generate-video")
async def generate_storyboard_video(
    storyboard_id: int,
    db: AsyncSession = Depends(get_db)
):
    """为剧集生成视频（自动适配 t2v/i2v 模型）"""
    result = await db.execute(select(Storyboard).where(Storyboard.id == storyboard_id))
    storyboard = result.scalar_one_or_none()
    if not storyboard:
        raise HTTPException(status_code=404, detail="Episode not found")

    config_result = await db.execute(
        select(ModelConfig).where(ModelConfig.name == "video", ModelConfig.is_active == True)
    )
    config = config_result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=400, detail="Video model not configured")

    is_i2v = "i2v" in (config.model or "")

    service = get_video_service(
        provider=config.provider,
        api_key=config.api_key,
        model=config.model,
        base_url=config.base_url,
        **(config.params or {})
    )

    storyboard.status = "processing"
    await db.commit()

    try:
        # 加载出场角色
        ep_characters = []
        if storyboard.character_ids:
            char_result = await db.execute(
                select(Character).where(Character.id.in_(storyboard.character_ids))
            )
            ep_characters = char_result.scalars().all()

        char_descriptions = _build_character_visual_prompt(ep_characters)

        # 构建视频 prompt（融入角色外观 + 动漫风格）
        enriched_prompt = _enrich_video_prompt(
            storyboard.video_prompt or "",
            storyboard.description or "",
            char_descriptions
        )

        # For i2v: prepare first_frame and driving_audio from TTS
        video_kwargs = {"prompt": enriched_prompt, "duration": 15, "resolution": "1080P",
                        "project_id": storyboard.project_id}

        if is_i2v:
            first_frame = None
            if storyboard.image_url:
                first_frame = storyboard.image_url
            elif ep_characters:
                for c in ep_characters:
                    if c.selected_image:
                        first_frame = c.selected_image
                        break
            video_kwargs["image_url"] = first_frame

            audio_data = None
            if storyboard.dialogue_lines:
                voice_config_result = await db.execute(
                    select(ModelConfig).where(ModelConfig.name == "voice", ModelConfig.is_active == True)
                )
                voice_config = voice_config_result.scalar_one_or_none()
                if voice_config and voice_config.api_key:
                    audio_data = await build_episode_dialogue_audio(
                        dialogue_lines=storyboard.dialogue_lines,
                        characters=ep_characters,
                        api_key=voice_config.api_key,
                        project_id=storyboard.project_id,
                        episode_number=storyboard.episode_number
                    )
            video_kwargs["audio_url"] = audio_data.get("audio_url") if audio_data else None

        vid_result = await service.generate(**video_kwargs)

        # Retry with clean prompt on content moderation failure (t2v only)
        if not is_i2v and not vid_result.success and vid_result.error and "Inappropriate" in str(vid_result.error):
            clean_prompt = f"Japanese anime style, anime characters, {storyboard.title}, dramatic scene, vibrant colors, smooth animation, high quality, 日系动漫风, 二次元, masterpiece"
            video_kwargs["prompt"] = clean_prompt
            vid_result = await service.generate(**video_kwargs)

        if vid_result.success and vid_result.data:
            video_url = vid_result.data.get("local_path") or vid_result.data.get("video_url")
            if video_url:
                ep_dir = get_episode_dir(storyboard.project_id, storyboard.episode_number)
                final_path = os.path.join(ep_dir, "final.mp4")
                if str(video_url).startswith("http"):
                    saved = await save_video_to_path(video_url, final_path)
                    storyboard.video_url = saved if saved else video_url
                else:
                    storyboard.video_url = video_url
                storyboard.video_prompt = enriched_prompt
                storyboard.status = "completed"
                storyboard.duration = 5 if not is_i2v else 15

                # For t2v: generate TTS audio separately and merge with FFmpeg
                if not is_i2v and storyboard.dialogue_lines and storyboard.video_url:
                    try:
                        voice_config_result = await db.execute(
                            select(ModelConfig).where(ModelConfig.name == "voice", ModelConfig.is_active == True)
                        )
                        voice_config = voice_config_result.scalar_one_or_none()
                        if voice_config and voice_config.api_key:
                            from app.services.video_audio_service import merge_video_audio
                            audio_data = await build_episode_dialogue_audio(
                                dialogue_lines=storyboard.dialogue_lines,
                                characters=ep_characters,
                                api_key=voice_config.api_key,
                                project_id=storyboard.project_id,
                                episode_number=storyboard.episode_number
                            )
                            if audio_data and audio_data.get("local_path"):
                                merged_path = os.path.join(ep_dir, "final_with_audio.mp4")
                                merged = await merge_video_audio(
                                    storyboard.video_url, audio_data["local_path"], merged_path
                                )
                                if merged:
                                    storyboard.video_url = merged
                                    storyboard.audio_url = merged
                    except Exception as e:
                        print(f"Audio merge failed (non-fatal): {e}")
            else:
                storyboard.status = "failed"
        else:
            storyboard.status = "failed"
            print(f"Video generation failed: {vid_result.error}")
    except Exception as e:
        storyboard.status = "failed"
        print(f"Failed to generate video: {e}")
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")

    storyboard.updated_at = datetime.utcnow()
    await db.commit()
    return {"status": storyboard.status, "video_url": storyboard.video_url}


class GenerateAudioRequest(BaseModel):
    dialogue: str = ""
    voice: Optional[str] = None


@router.post("/{storyboard_id}/generate-audio")
async def generate_storyboard_audio(
    storyboard_id: int,
    request: GenerateAudioRequest = GenerateAudioRequest(),
    db: AsyncSession = Depends(get_db)
):
    """为剧集视频生成配音（TTS + 可选 FFmpeg 合并，或仅返回音频 URL）"""
    result = await db.execute(select(Storyboard).where(Storyboard.id == storyboard_id))
    storyboard = result.scalar_one_or_none()
    if not storyboard:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Build dialogue text
    dialogue = request.dialogue
    if not dialogue:
        dialogue_lines = storyboard.dialogue_lines or []
        if isinstance(dialogue_lines, list) and dialogue_lines:
            parts = []
            for d in dialogue_lines:
                if isinstance(d, dict):
                    speaker = d.get("speaker", "")
                    text = d.get("text", "")
                    parts.append(f"{speaker}: {text}" if speaker else text)
                elif isinstance(d, str):
                    parts.append(d)
            dialogue = "。".join(parts)
    if not dialogue:
        dialogue = storyboard.episode_script or storyboard.description or ""

    if not dialogue:
        raise HTTPException(status_code=400, detail="No dialogue text provided")

    voice_config = await db.execute(
        select(ModelConfig).where(ModelConfig.name == "voice", ModelConfig.is_active == True)
    )
    voice_config = voice_config.scalar_one_or_none()
    if not voice_config or not voice_config.api_key:
        raise HTTPException(status_code=400, detail="Voice model not configured")

    # Match voice to character
    voice = request.voice or "Cherry"
    if not request.voice:
        char_result = await db.execute(
            select(Character).where(Character.project_id == storyboard.project_id)
        )
        characters = char_result.scalars().all()
        if characters:
            char_by_name = {}
            for c in characters:
                if c.name:
                    char_by_name[c.name] = c

            matched = False
            for prefix_sep in ["：", ": ", ":"]:
                if prefix_sep in dialogue:
                    potential_name = dialogue.split(prefix_sep)[0].strip()
                    for c_name, char_obj in char_by_name.items():
                        if c_name and c_name in potential_name:
                            voice = get_voice_for_character(char_obj)
                            matched = True
                            break
                    if matched:
                        break

            if not matched:
                voice = get_voice_for_character(characters[0])

    storyboard.status = "processing"
    await db.commit()

    try:
        # Try new flow: TTS → driving_audio for lip sync
        audio_url = None
        try:
            from app.services.video_audio_service import generate_dialogue_audio_data
            audio_data = await generate_dialogue_audio_data(
                text=dialogue,
                voice=voice,
                api_key=voice_config.api_key
            )
            if audio_data:
                audio_url = audio_data.get("audio_url")
        except Exception:
            pass

        # Fall back to FFmpeg merge if video exists
        if storyboard.video_url and audio_url:
            from app.services.video_audio_service import add_audio_to_video
            merged = await add_audio_to_video(
                video_url=storyboard.video_url,
                dialogue=dialogue,
                voice=voice,
                project_id=storyboard.project_id,
                api_key=voice_config.api_key,
                shot_prefix=f"episode{storyboard.episode_number}"
            )
            if merged:
                storyboard.video_url = merged

        storyboard.audio_url = audio_url or storyboard.audio_url
        storyboard.status = "completed"
    except Exception as e:
        storyboard.status = "failed"
        print(f"Audio generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")

    storyboard.updated_at = datetime.utcnow()
    await db.commit()
    return {"status": storyboard.status, "video_url": storyboard.video_url, "audio_url": storyboard.audio_url}


@router.delete("/{storyboard_id}")
async def delete_storyboard(
    storyboard_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除剧集"""
    result = await db.execute(select(Storyboard).where(Storyboard.id == storyboard_id))
    storyboard = result.scalar_one_or_none()
    if not storyboard:
        raise HTTPException(status_code=404, detail="Episode not found")

    await db.delete(storyboard)
    await db.commit()
    return {"message": "Episode deleted successfully"}
