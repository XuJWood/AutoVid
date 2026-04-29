"""
Storyboard API endpoints — 漫剧剧集管理接口
Episode→Segment→Video hierarchy: each ~60s episode has ~4 segments, each segment = 1 video
"""
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.database import get_db, Storyboard, Segment, Project, ModelConfig, Character
from app.services.image_service import get_image_service
from app.services.video_service import get_video_service
from app.services.media_storage import (
    get_episode_dir, save_image_to_path, save_video_to_path, local_path_to_url
)
from sqlalchemy.exc import OperationalError


router = APIRouter()


# ──────────────────────────────────────────────
# Helper: URL conversion
# ──────────────────────────────────────────────

def _to_http_url(maybe_path: str, req: Request) -> str:
    """将本地绝对路径转为完整 HTTP URL（供 API 下载用）"""
    if not maybe_path:
        return maybe_path
    if maybe_path.startswith("http://") or maybe_path.startswith("https://"):
        return maybe_path
    media_url = local_path_to_url(maybe_path)
    if media_url:
        return f"{req.base_url.scheme}://{req.base_url.netloc}{media_url}"
    return maybe_path


def _normalize_media_url(url: str) -> Optional[str]:
    """Normalize a media URL to /media/... format for frontend consumption"""
    if not url:
        return url
    if url.startswith("/media/"):
        return url
    if "/media/" in url:
        idx = url.index("/media/")
        return url[idx:]
    return url


# ──────────────────────────────────────────────
# Pydantic response models
# ──────────────────────────────────────────────

class SegmentResponse(BaseModel):
    id: int
    storyboard_id: int
    project_id: int
    segment_number: int
    visual_description: Optional[str] = None
    camera_movement: Optional[str] = None
    dialogue: Optional[str] = None
    character_ids: Optional[list] = None
    character_image_refs: Optional[dict] = None
    image_prompt: Optional[str] = None
    video_prompt: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    duration: int = 15
    model_provider: Optional[str] = None
    status: str = "pending"
    image_status: str = "pending"
    video_status: str = "pending"

    class Config:
        from_attributes = True


class StoryboardResponse(BaseModel):
    id: int
    project_id: int
    episode_number: int
    title: Optional[str] = None
    episode_script: Optional[str] = None
    dialogue_lines: Optional[list] = None
    character_ids: Optional[list] = None
    description: Optional[str] = None
    image_prompt: Optional[str] = None
    video_prompt: Optional[str] = None
    duration: int = 60
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    status: str = "pending"
    image_status: str = "pending"
    video_status: str = "pending"
    segments: Optional[List[SegmentResponse]] = None

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Episode CRUD
# ──────────────────────────────────────────────

@router.get("/project/{project_id}", response_model=List[StoryboardResponse])
async def get_project_storyboard(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取项目的所有剧集（含片段）"""
    result = await db.execute(
        select(Storyboard).where(Storyboard.project_id == project_id).order_by(Storyboard.episode_number)
    )
    storyboards = result.scalars().all()
    out = []
    for sb in storyboards:
        segments = []
        try:
            seg_result = await db.execute(
                select(Segment).where(
                    Segment.storyboard_id == sb.id,
                    Segment.project_id == project_id
                ).order_by(Segment.segment_number)
            )
            segments = seg_result.scalars().all()
        except OperationalError:
            segments = []
        for seg in segments:
            seg.image_url = _normalize_media_url(seg.image_url)
            seg.video_url = _normalize_media_url(seg.video_url)

        sb_dict = {
            "id": sb.id,
            "project_id": sb.project_id,
            "episode_number": sb.episode_number,
            "title": sb.title,
            "episode_script": sb.episode_script,
            "dialogue_lines": sb.dialogue_lines,
            "character_ids": sb.character_ids,
            "description": sb.description,
            "image_prompt": sb.image_prompt,
            "video_prompt": sb.video_prompt,
            "duration": sb.duration or 60,
            "image_url": _normalize_media_url(sb.image_url),
            "video_url": _normalize_media_url(sb.video_url),
            "audio_url": _normalize_media_url(sb.audio_url),
            "status": sb.status,
            "image_status": sb.image_status,
            "video_status": sb.video_status,
            "segments": [
                {
                    "id": seg.id,
                    "storyboard_id": seg.storyboard_id,
                    "project_id": seg.project_id,
                    "segment_number": seg.segment_number,
                    "visual_description": seg.visual_description,
                    "camera_movement": seg.camera_movement,
                    "dialogue": seg.dialogue,
                    "character_ids": seg.character_ids,
                    "character_image_refs": seg.character_image_refs,
                    "image_prompt": seg.image_prompt,
                    "video_prompt": seg.video_prompt,
                    "image_url": seg.image_url,
                    "video_url": seg.video_url,
                    "duration": seg.duration,
                    "model_provider": seg.model_provider,
                    "status": seg.status,
                    "image_status": seg.image_status,
                    "video_status": seg.video_status,
                }
                for seg in segments
            ]
        }
        out.append(sb_dict)
    return out


@router.post("/project/{project_id}/generate", response_model=List[StoryboardResponse])
async def generate_storyboard(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """从剧本内容生成剧集和片段（Episode→Segment 两级结构）"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    script = project.script_content
    if not script:
        raise HTTPException(status_code=400, detail="No script content to generate episodes")

    episodes = script.get("episodes", [])
    if not episodes and script.get("scenes"):
        episodes = _convert_scenes_to_episodes(script.get("scenes", []))

    if not episodes:
        raise HTTPException(status_code=400, detail="No episodes or scenes found in script")

    # Load project characters: build name→id mapping
    char_result = await db.execute(
        select(Character).where(Character.project_id == project_id)
    )
    db_characters = char_result.scalars().all()
    char_name_to_obj = {}
    char_name_to_id = {}
    for c in db_characters:
        if c.name:
            char_name_to_obj[c.name] = c
            char_name_to_id[c.name] = c.id

    # Clear existing episodes and segments
    existing_eps = await db.execute(
        select(Storyboard.id).where(Storyboard.project_id == project_id)
    )
    ep_ids = [row[0] for row in existing_eps.fetchall()]
    if ep_ids:
        await db.execute(delete(Segment).where(Segment.storyboard_id.in_(ep_ids)))
    await db.execute(delete(Storyboard).where(Storyboard.project_id == project_id))
    await db.commit()

    # Create episodes and segments
    storyboards = []
    for ep_idx, episode in enumerate(episodes):
        episode_number = ep_idx + 1
        dialogues = episode.get("dialogues", [])
        description = episode.get("description", "")
        environment = episode.get("environment", "")
        time = episode.get("time", "")
        mood = episode.get("mood", "")
        title = episode.get("title", f"第{episode_number}集")
        segments_data = episode.get("segments", [])

        # Map characters in this episode
        episode_char_ids = []
        for d in dialogues:
            speaker = d.get("speaker", "") if isinstance(d, dict) else ""
            if speaker and speaker in char_name_to_id:
                cid = char_name_to_id[speaker]
                if cid not in episode_char_ids:
                    episode_char_ids.append(cid)

        # Build cover image prompt
        image_prompt = (
            f"日系动漫风，二次元，{title}，{description}，"
            f"{environment}，{time}，精致的色彩，柔和的光影，高画质动漫插画"
        )

        sb = Storyboard(
            project_id=project_id,
            episode_number=episode_number,
            scene_index=ep_idx,
            shot_index=0,
            title=title,
            episode_script=episode.get("script", ""),
            dialogue_lines=dialogues,
            character_ids=episode_char_ids,
            description=description,
            image_prompt=image_prompt,
            video_prompt="",
            duration=60,
            status="pending",
            image_status="pending",
            video_status="pending"
        )
        db.add(sb)
        await db.flush()  # Get sb.id for segments

        # Create segments
        for seg_idx, seg_data in enumerate(segments_data):
            seg_number = seg_data.get("segment_number", seg_idx + 1)
            visual_desc = seg_data.get("visual_description", "")
            camera_movement = seg_data.get("camera_movement", "fixed")
            dialogue = seg_data.get("dialogue", "")
            emotion = seg_data.get("emotion", "")
            seg_duration = seg_data.get("duration", 15)

            # Map characters for this segment
            seg_char_ids = []
            seg_char_refs = {}
            if dialogue:
                for char_name, char_obj in char_name_to_obj.items():
                    if char_name and char_name in dialogue:
                        if char_obj.id not in seg_char_ids:
                            seg_char_ids.append(char_obj.id)
                        if char_obj.selected_image:
                            seg_char_refs[str(char_obj.id)] = char_obj.selected_image

            # Also include episode character IDs
            for cid in episode_char_ids:
                if cid not in seg_char_ids:
                    seg_char_ids.append(cid)
                    char_obj = next((c for c in db_characters if c.id == cid), None)
                    if char_obj and char_obj.selected_image:
                        seg_char_refs[str(cid)] = char_obj.selected_image

            # Build segment video prompt (includes dialogue for audio)
            video_prompt = (
                f"{visual_desc}, {camera_movement} camera movement, "
                f"Japanese anime style, 日系动漫风, 二次元, smooth animation, "
                f"vibrant colors, character design consistent with reference image, "
                f"high quality anime video, detailed background, dynamic lighting, "
                f"dialogue: {dialogue}" if dialogue else
                f"{visual_desc}, {camera_movement} camera movement, "
                f"Japanese anime style, 日系动漫风, 二次元, smooth animation, "
                f"vibrant colors, high quality anime video, detailed background, dynamic lighting"
            )

            segment = Segment(
                storyboard_id=sb.id,
                project_id=project_id,
                segment_number=seg_number,
                visual_description=visual_desc,
                camera_movement=camera_movement,
                dialogue=dialogue,
                character_ids=seg_char_ids,
                character_image_refs=seg_char_refs,
                video_prompt=video_prompt,
                duration=seg_duration,
                status="pending",
                image_status="pending",
                video_status="pending"
            )
            db.add(segment)

        storyboards.append(sb)

    await db.commit()
    for sb in storyboards:
        await db.refresh(sb)

    # Return with segments
    return await get_project_storyboard(project_id, db)


def _convert_scenes_to_episodes(scenes: list) -> list:
    """向后兼容：将旧格式 scenes 转换为 episodes（带默认 segments）"""
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

        # Convert old shots to segments (4 segments per episode)
        old_shots = shots[:4] if len(shots) >= 4 else shots
        segments = []
        for i, shot in enumerate(old_shots):
            dia = shot.get("dialogue", "")
            dia_text = ""
            if isinstance(dia, dict):
                dia_text = f"{dia.get('speaker', '')}: {dia.get('content', '')}"
            elif isinstance(dia, str):
                dia_text = dia

            segments.append({
                "segment_number": i + 1,
                "visual_description": shot.get("description", ""),
                "camera_movement": shot.get("movement", "fixed"),
                "dialogue": dia_text,
                "emotion": shot.get("emotion", ""),
                "duration": shot.get("duration", 15)
            })

        # Pad to 4 segments
        while len(segments) < 4:
            segments.append({
                "segment_number": len(segments) + 1,
                "visual_description": scene.get("description", ""),
                "camera_movement": "fixed",
                "dialogue": "",
                "emotion": "neutral",
                "duration": 15
            })

        episodes.append({
            "episode_number": scene.get("id", 1),
            "title": scene.get("name", ""),
            "environment": scene.get("environment", ""),
            "time": scene.get("time", ""),
            "mood": scene.get("mood", ""),
            "description": scene.get("description", ""),
            "script": "\n".join(script_parts),
            "dialogues": dialogues,
            "duration": 60,
            "segments": segments
        })
    return episodes


# ──────────────────────────────────────────────
# Episode cover image generation
# ──────────────────────────────────────────────

@router.post("/{storyboard_id}/generate-image")
async def generate_storyboard_image(
    storyboard_id: int,
    db: AsyncSession = Depends(get_db)
):
    """为剧集生成封面图"""
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

    ep_characters = []
    if storyboard.character_ids:
        char_result = await db.execute(
            select(Character).where(Character.id.in_(storyboard.character_ids))
        )
        ep_characters = char_result.scalars().all()

    has_female = any(getattr(c, "gender", None) == "女" for c in ep_characters)
    style = (
        f"Japanese anime style, 日系动漫风, 二次元, vibrant colors, "
        f"beautiful anime girl, sexy cute alluring, delicate features, "
        f"high quality anime illustration, clean lineart, masterpiece"
        if has_female else
        f"Japanese anime style, 日系动漫风, 二次元, vibrant colors, "
        f"handsome anime guy, sharp features, high quality anime illustration, masterpiece"
    )
    cover_prompt = f"{storyboard.title}, {storyboard.description}, {style}"

    service = get_image_service(
        provider=config.provider, api_key=config.api_key,
        model=config.model, base_url=config.base_url,
        **(config.params or {})
    )

    storyboard.image_status = "processing"
    await db.commit()

    try:
        result = await service.generate(prompt=cover_prompt, project_id=storyboard.project_id)
        if result.success and result.data:
            images = result.data.get("images", [])
            if images:
                ep_dir = get_episode_dir(storyboard.project_id, storyboard.episode_number)
                cover_path = os.path.join(ep_dir, "cover.png")
                saved = await save_image_to_path(images[0], cover_path)
                storyboard.image_url = local_path_to_url(saved) if saved else images[0]
                storyboard.image_prompt = cover_prompt
                storyboard.image_status = "completed"
            else:
                storyboard.image_status = "failed"
        else:
            storyboard.image_status = "failed"
    except Exception as e:
        storyboard.image_status = "failed"
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

    storyboard.updated_at = datetime.utcnow()
    await db.commit()
    return {"status": storyboard.image_status, "image_url": storyboard.image_url}


# ──────────────────────────────────────────────
# Segment video generation (Seedance / other)
# ──────────────────────────────────────────────

class GenerateSegmentVideoRequest(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    duration: Optional[int] = None
    ratio: Optional[str] = None
    resolution: Optional[str] = None
    generate_audio: Optional[bool] = None
    watermark: Optional[bool] = None


@router.post("/segment/{segment_id}/generate-video")
async def generate_segment_video(
    segment_id: int,
    req: Request,
    request: GenerateSegmentVideoRequest = GenerateSegmentVideoRequest(),
    db: AsyncSession = Depends(get_db)
):
    """为单个片段生成视频（使用 Seedance 或其他视频模型，视频+音频一体化）

    生成参数优先级（从高到低）:
      1. 请求体显式传入的参数
      2. ModelConfig.params 中保存的用户默认值
      3. 服务自身的默认值
    """
    result = await db.execute(select(Segment).where(Segment.id == segment_id))
    segment = result.scalar_one_or_none()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    # Load ModelConfig to get user-configured defaults
    config_result = await db.execute(
        select(ModelConfig).where(ModelConfig.name == "video", ModelConfig.is_active == True)
    )
    config = config_result.scalar_one_or_none()
    if not config and not request.api_key:
        raise HTTPException(status_code=400, detail="Video model not configured. Please configure it in Settings → Model Config.")

    cfg_params = (config.params if config else {}) or {}

    # Resolve credentials & model name
    provider = request.provider or (config.provider if config else "seedance")
    api_key = request.api_key or (config.api_key if config else None)
    model = request.model or (config.model if config else None)
    base_url = config.base_url if config else None

    if not api_key:
        raise HTTPException(status_code=400, detail="Video model API key not configured")

    # Resolve generation params (request → config.params → defaults)
    duration = request.duration if request.duration is not None else cfg_params.get("duration", 15)
    ratio = request.ratio or cfg_params.get("ratio", "16:9")
    resolution = request.resolution or cfg_params.get("resolution", "1080p")
    generate_audio = request.generate_audio if request.generate_audio is not None else cfg_params.get("generate_audio", True)
    watermark = request.watermark if request.watermark is not None else cfg_params.get("watermark", False)

    # Pass non-generation params (e.g. timeouts) to service constructor only
    constructor_params = {k: v for k, v in cfg_params.items()
                          if k not in ("duration", "ratio", "resolution", "generate_audio", "watermark")}

    service = get_video_service(
        provider=provider,
        api_key=api_key,
        model=model,
        base_url=base_url,
        **constructor_params
    )

    segment.video_status = "processing"
    segment.model_provider = provider
    await db.commit()

    try:
        # Prepare reference image — order of preference:
        #   1. live character.selected_image (current — may have been (re)generated after segment was created)
        #   2. cached segment.character_image_refs
        #   3. episode cover image as i2v first frame
        # Each candidate is normalized for Ark inside SeedanceVideoService (local → base64).
        ref_image = None

        seg_char_ids = segment.character_ids or []
        # 1. Pull the current selected_image from any character in this segment
        if seg_char_ids:
            char_q = await db.execute(
                select(Character.selected_image)
                .where(Character.id.in_(seg_char_ids))
                .order_by(Character.id)
            )
            for img in char_q.scalars().all():
                if img:
                    ref_image = img
                    break

        # 2. Fall back to cached segment refs
        if not ref_image:
            char_refs = segment.character_image_refs or {}
            if char_refs:
                ref_image = next(iter(char_refs.values()))

        # 3. Fall back to episode cover image — but skip expired DashScope OSS URLs
        if not ref_image:
            ep_res = await db.execute(
                select(Storyboard.image_url).where(Storyboard.id == segment.storyboard_id)
            )
            cover = ep_res.scalar_one_or_none()
            if cover and "Expires=" not in cover:  # skip pre-signed OSS URLs
                ref_image = cover

        # Build a high-quality anime video prompt
        from app.services.seedance_video import build_seedance_anime_prompt
        video_prompt = build_seedance_anime_prompt(
            visual_description=segment.visual_description or segment.video_prompt or "",
            camera_movement=segment.camera_movement or "fixed",
            dialogue=segment.dialogue or "",
            emotion="",
        )

        # Get episode number for organized storage path
        ep_num_res = await db.execute(
            select(Storyboard.episode_number).where(Storyboard.id == segment.storyboard_id)
        )
        episode_number = ep_num_res.scalar_one_or_none() or 0

        # Duration priority: request body → ModelConfig.params → defaults
        # segment.duration is narrative intent only, not a model constraint
        effective_duration = request.duration if request.duration is not None else duration

        vid_result = await service.generate(
            prompt=video_prompt,
            image_url=ref_image,
            duration=effective_duration,
            ratio=ratio,
            resolution=resolution,
            generate_audio=generate_audio,
            watermark=watermark,
            project_id=segment.project_id,
            episode_number=episode_number,
            segment_number=segment.segment_number
        )

        if vid_result.success and vid_result.data:
            local_path = vid_result.data.get("local_path")
            remote_url = vid_result.data.get("video_url")
            if local_path and not str(local_path).startswith("http"):
                segment.video_url = local_path_to_url(local_path)
            elif local_path:
                segment.video_url = local_path
            elif remote_url:
                segment.video_url = remote_url
            segment.video_prompt = video_prompt
            segment.video_status = "completed" if segment.video_url else "failed"
        else:
            segment.video_status = "failed"
            error_msg = vid_result.error or "Unknown error"
            print(f"Segment video generation failed: {error_msg}")
            segment.updated_at = datetime.utcnow()
            await db.commit()
            return {"status": "failed", "video_url": None, "error": error_msg}
    except Exception as e:
        segment.video_status = "failed"
        error_msg = str(e)
        print(f"Failed to generate segment video: {error_msg}")
        segment.updated_at = datetime.utcnow()
        await db.commit()
        return {"status": "failed", "video_url": None, "error": error_msg}

    segment.updated_at = datetime.utcnow()
    await db.commit()
    return {"status": segment.video_status, "video_url": segment.video_url}


@router.post("/{storyboard_id}/generate-all-segments")
async def generate_all_segment_videos(
    storyboard_id: int,
    req: Request,
    request: GenerateSegmentVideoRequest = GenerateSegmentVideoRequest(),
    db: AsyncSession = Depends(get_db)
):
    """为剧集的所有片段生成视频"""
    result = await db.execute(select(Storyboard).where(Storyboard.id == storyboard_id))
    storyboard = result.scalar_one_or_none()
    if not storyboard:
        raise HTTPException(status_code=404, detail="Episode not found")

    seg_result = await db.execute(
        select(Segment).where(
            Segment.storyboard_id == storyboard_id,
            Segment.project_id == storyboard.project_id
        ).order_by(Segment.segment_number)
    )
    segments = seg_result.scalars().all()

    if not segments:
        raise HTTPException(status_code=400, detail="No segments found for this episode")

    results = []
    for seg in segments:
        try:
            r = await generate_segment_video(seg.id, req, request, db)
            results.append({"segment_id": seg.id, "status": r["status"], "video_url": r["video_url"]})
        except Exception as e:
            results.append({"segment_id": seg.id, "status": "failed", "error": str(e)})

    # Update episode status based on segments
    all_completed = all(r["status"] == "completed" for r in results)
    any_failed = any(r["status"] == "failed" for r in results)

    if all_completed:
        storyboard.video_status = "completed"
        storyboard.status = "completed"
    elif any_failed:
        storyboard.video_status = "partial"
        storyboard.status = "in_progress"
    else:
        storyboard.video_status = "processing"
        storyboard.status = "in_progress"

    storyboard.updated_at = datetime.utcnow()
    await db.commit()

    return {"results": results, "episode_status": storyboard.video_status}


# ──────────────────────────────────────────────
# Legacy video generation (episode-level, deprecated)
# ──────────────────────────────────────────────

@router.post("/{storyboard_id}/generate-video")
async def generate_storyboard_video(
    storyboard_id: int,
    req: Request,
    db: AsyncSession = Depends(get_db)
):
    """（已弃用）为剧集生成视频 — 优先使用片段模式，旧库无 segments 时回退到单集模式"""
    try:
        seg_result = await db.execute(
            select(Segment).where(Segment.storyboard_id == storyboard_id)
        )
        segments = seg_result.scalars().all()
        if segments:
            req_data = GenerateSegmentVideoRequest()
            return await generate_all_segment_videos(storyboard_id, req, req_data, db)
    except OperationalError:
        pass

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

    service = get_video_service(
        provider=config.provider, api_key=config.api_key,
        model=config.model, base_url=config.base_url,
        **(config.params or {})
    )

    storyboard.video_status = "processing"
    await db.commit()

    try:
        vid_result = await service.generate(
            prompt=storyboard.video_prompt or storyboard.description or "",
            duration=15,
            resolution="720p",
            project_id=storyboard.project_id,
            episode_number=storyboard.episode_number
        )

        if vid_result.success and vid_result.data:
            video_url = vid_result.data.get("local_path") or vid_result.data.get("video_url")
            if video_url:
                ep_dir = get_episode_dir(storyboard.project_id, storyboard.episode_number)
                final_path = os.path.join(ep_dir, "final.mp4")
                if str(video_url).startswith("http"):
                    saved = await save_video_to_path(video_url, final_path)
                    storyboard.video_url = local_path_to_url(saved) if saved else video_url
                else:
                    storyboard.video_url = local_path_to_url(video_url) if os.path.isabs(str(video_url)) else video_url
                storyboard.video_status = "completed"
            else:
                storyboard.video_status = "failed"
                raise HTTPException(status_code=500, detail="Video generation failed: missing video url")
        else:
            storyboard.video_status = "failed"
            raise HTTPException(status_code=500, detail=f"Video generation failed: {vid_result.error or 'unknown error'}")
    except HTTPException:
        raise
    except Exception as e:
        storyboard.video_status = "failed"
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")
    finally:
        storyboard.updated_at = datetime.utcnow()
        await db.commit()

    return {"status": storyboard.video_status, "video_url": storyboard.video_url}


# ──────────────────────────────────────────────
# Delete
# ──────────────────────────────────────────────

@router.delete("/segment/{segment_id}")
async def delete_segment(
    segment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除片段"""
    result = await db.execute(select(Segment).where(Segment.id == segment_id))
    segment = result.scalar_one_or_none()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    await db.delete(segment)
    await db.commit()
    return {"message": "Segment deleted successfully"}


@router.delete("/{storyboard_id}")
async def delete_storyboard(
    storyboard_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除剧集（含所有片段）"""
    result = await db.execute(select(Storyboard).where(Storyboard.id == storyboard_id))
    storyboard = result.scalar_one_or_none()
    if not storyboard:
        raise HTTPException(status_code=404, detail="Episode not found")

    await db.execute(delete(Segment).where(Segment.storyboard_id == storyboard_id))
    await db.delete(storyboard)
    await db.commit()
    return {"message": "Episode deleted successfully"}
