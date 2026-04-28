"""
Videos API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.database import get_db, GeneratedVideo, Project, Character

router = APIRouter()


# Pydantic models

class VideoGenerateRequest(BaseModel):
    project_id: Optional[int] = None
    character_id: Optional[int] = None
    scene_description: str
    action_description: Optional[str] = ""
    prompt_suffix: Optional[str] = ""
    duration: Optional[int] = 5
    aspect_ratio: Optional[str] = "16:9"
    resolution: Optional[str] = "1080p"
    model_provider: Optional[str] = None


class VideoResponse(BaseModel):
    id: int
    project_id: Optional[int]
    character_id: Optional[int]
    file_path: Optional[str]
    thumbnail_path: Optional[str]
    duration: int
    resolution: str
    aspect_ratio: str
    model_provider: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class VideoGenerateResponse(BaseModel):
    video_id: int
    status: str
    message: str


# API Endpoints

@router.get("", response_model=List[VideoResponse])
async def get_videos(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all videos, optionally filtered"""
    query = select(GeneratedVideo)
    if project_id:
        query = query.where(GeneratedVideo.project_id == project_id)
    if status:
        query = query.where(GeneratedVideo.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific video"""
    result = await db.execute(select(GeneratedVideo).where(GeneratedVideo.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(
    request: VideoGenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate a video using AI"""
    # Create video record
    video = GeneratedVideo(
        project_id=request.project_id,
        character_id=request.character_id,
        duration=request.duration,
        resolution=request.resolution,
        aspect_ratio=request.aspect_ratio,
        model_provider=request.model_provider,
        status="pending",
        generation_params={
            "scene_description": request.scene_description,
            "action_description": request.action_description,
            "prompt_suffix": request.prompt_suffix,
        }
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    # TODO: Implement actual video generation using AI service
    # This would typically be done in a background task with Celery

    return VideoGenerateResponse(
        video_id=video.id,
        status="pending",
        message="Video generation started"
    )


@router.post("/{video_id}/regenerate", response_model=VideoGenerateResponse)
async def regenerate_video(video_id: int, db: AsyncSession = Depends(get_db)):
    """Regenerate a video"""
    result = await db.execute(select(GeneratedVideo).where(GeneratedVideo.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    video.status = "pending"
    video.error_message = None
    await db.commit()

    return VideoGenerateResponse(
        video_id=video.id,
        status="pending",
        message="Video regeneration started"
    )


@router.delete("/{video_id}")
async def delete_video(video_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a video"""
    result = await db.execute(select(GeneratedVideo).where(GeneratedVideo.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # TODO: Delete actual video file from storage

    await db.delete(video)
    await db.commit()
    return {"message": "Video deleted successfully"}


@router.get("/{video_id}/status")
async def get_video_status(video_id: int, db: AsyncSession = Depends(get_db)):
    """Get video generation status"""
    result = await db.execute(select(GeneratedVideo).where(GeneratedVideo.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return {
        "video_id": video.id,
        "status": video.status,
        "progress": 0 if video.status == "pending" else 100,
        "error_message": video.error_message
    }
