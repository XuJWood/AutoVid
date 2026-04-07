"""
Storyboard API endpoints
分镜管理接口
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db, Storyboard, Project, ModelConfig
from app.services.image_service import get_image_service


from app.services.video_service import get_video_service


router = APIRouter()


class StoryboardResponse(BaseModel):
    """分镜响应模型"""
    id: int
    project_id: int
    scene_index: int
    shot_index: int
    shot_type: Optional[str]
    description: Optional[str]
    image_prompt: Optional[str]
    video_prompt: Optional[str]
    duration: int
    image_url: Optional[str]
    video_url: Optional[str]
    audio_url: Optional[str]
    status: str

    class Config:
        from_attributes = True


@router.get("/project/{project_id}", response_model=List[StoryboardResponse])
async def get_project_storyboard(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取项目的所有分镜"""
    result = await db.execute(
        select(Storyboard).where(Storyboard.project_id == project_id).order_by(Storyboard.scene_index, Storyboard.shot_index)
    )
    return result.scalars().all()


@router.post("/project/{project_id}/generate", response_model=List[StoryboardResponse])
async def generate_storyboard(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """从剧本内容生成分镜"""
    # 获取项目
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    script = project.script_content
    if not script or not script.get("scenes"):
        raise HTTPException(status_code=400, detail="No script content to generate storyboard")

    # 清除现有分镜
    await db.execute(
        delete(Storyboard).where(Storyboard.project_id == project_id)
    )

    # 创建分镜条目
    storyboards = []
    for scene_idx, scene in enumerate(script.get("scenes", [])):
        for shot_idx, shot in enumerate(scene.get("shots", [])):
            sb = Storyboard(
                project_id=project_id,
                scene_index=scene_idx,
                shot_index=shot_idx,
                shot_type=shot.get("type"),
                description=shot.get("description"),
                image_prompt=f"{shot.get('description', '')}, {shot.get('type', '')} shot, cinematic, high quality",
                video_prompt=f"{shot.get('description', '')}, {shot.get('movement', '')} camera, cinematic",
                duration=shot.get("duration", 5),
                status="pending"
            )
            db.add(sb)
            storyboards.append(sb)

    await db.commit()
    for sb in storyboards:
        await db.refresh(sb)
    return storyboards


@router.post("/{storyboard_id}/generate-image")
async def generate_storyboard_image(
    storyboard_id: int,
    db: AsyncSession = Depends(get_db)
):
    """为分镜生成图片"""
    result = await db.execute(select(Storyboard).where(Storyboard.id == storyboard_id))
    storyboard = result.scalar_one_or_none()
    if not storyboard:
        raise HTTPException(status_code=404, detail="Storyboard not found")

    # 获取图像模型配置
    config_result = await db.execute(
        select(ModelConfig).where(ModelConfig.name == "image", ModelConfig.is_active == True)
    )
    config = config_result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=400, detail="Image model not configured")

    # 生成图片
    service = get_image_service(
        provider=config.provider,
        api_key=config.api_key,
        **(config.params or {})
    )

    storyboard.status = "processing"
    await db.commit()

    try:
        result = await service.generate(prompt=storyboard.image_prompt)
        if result.success and result.data:
            images = result.data.get("images", [])
            storyboard.image_url = images[0] if images else None
            storyboard.status = "completed"
        else:
            storyboard.status = "failed"
    except Exception as e:
        storyboard.status = "failed"
        print(f"Failed to generate image: {e}")

        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

    storyboard.updated_at = datetime.utcnow()
    await db.commit()
    return {"status": storyboard.status, "image_url": storyboard.image_url}


@router.post("/{storyboard_id}/generate-video")
async def generate_storyboard_video(
    storyboard_id: int,
    db: AsyncSession = Depends(get_db)
):
    """为分镜生成视频"""
    result = await db.execute(select(Storyboard).where(Storyboard.id == storyboard_id))
    storyboard = result.scalar_one_or_none()
    if not storyboard:
        raise HTTPException(status_code=404, detail="Storyboard not found")

    # 获取视频模型配置
    config_result = await db.execute(
        select(ModelConfig).where(ModelConfig.name == "video", ModelConfig.is_active == True)
    )
    config = config_result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=400, detail="Video model not configured")

    # 生成视频
    service = get_video_service(
        provider=config.provider,
        api_key=config.api_key,
        **(config.params or {})
    )

    storyboard.status = "processing"
    await db.commit()

    try:
        result = await service.generate(prompt=storyboard.video_prompt)
        if result.success and result.data:
            storyboard.video_url = result.data.get("video_url") or result.data.get("video_id")
            storyboard.status = "completed"
        else:
            storyboard.status = "failed"
    except Exception as e:
        storyboard.status = "failed"
        print(f"Failed to generate video: {e}")
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")

    storyboard.updated_at = datetime.utcnow()
    await db.commit()
    return {"status": storyboard.status, "video_url": storyboard.video_url}


@router.delete("/{storyboard_id}")
async def delete_storyboard(
    storyboard_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除分镜"""
    result = await db.execute(select(Storyboard).where(Storyboard.id == storyboard_id))
    storyboard = result.scalar_one_or_none()
    if not storyboard:
        raise HTTPException(status_code=404, detail="Storyboard not found")

    await db.delete(storyboard)
    await db.commit()
    return {"message": "Storyboard deleted successfully"}
