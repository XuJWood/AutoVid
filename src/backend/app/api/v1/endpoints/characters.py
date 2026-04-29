"""
Characters API endpoints
"""
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from app.core.database import get_db, Character, Project, ModelConfig

router = APIRouter()


# Pydantic models

class CharacterDescription(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    personality: Optional[str] = None
    appearance: Optional[str] = None
    clothing: Optional[str] = None


class VoiceConfig(BaseModel):
    provider: Optional[str] = "azure"
    voice_id: Optional[str] = "zh-CN-YunxiNeural"
    speed: Optional[float] = 1.0
    pitch: Optional[int] = 0


class CharacterBase(BaseModel):
    name: str
    project_id: Optional[int] = None
    description: Optional[CharacterDescription] = None
    voice_config: Optional[VoiceConfig] = None


class CharacterCreate(CharacterBase):
    pass


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[CharacterDescription] = None
    selected_image: Optional[str] = None
    alternative_images: Optional[List[str]] = None
    three_views: Optional[Dict[str, Any]] = None
    style: Optional[str] = None
    voice_config: Optional[VoiceConfig] = None
    wardrobe: Optional[List[Dict[str, Any]]] = None


class CharacterResponse(BaseModel):
    id: int
    project_id: Optional[int]
    name: str
    age: Optional[int]
    gender: Optional[str]
    occupation: Optional[str]
    personality: Optional[str]
    appearance: Optional[str]
    clothing: Optional[str]
    selected_image: Optional[str]
    alternative_images: List[str]
    three_views: Optional[Dict[str, Any]] = None
    style: str
    character_id: Optional[str]
    voice_config: Dict[str, Any]
    wardrobe: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GenerateImageRequest(BaseModel):
    prompt_suffix: Optional[str] = ""
    styles: Optional[List[str]] = ["realistic"]
    count_per_style: Optional[int] = 4


class GenerateImageResponse(BaseModel):
    images: Dict[str, List[str]]
    message: str


class GenerateThreeViewsRequest(BaseModel):
    style: Optional[str] = "anime"
    prompt_suffix: Optional[str] = ""
    custom_prompt: Optional[str] = ""  # 自定义完整提示词（覆盖自动生成的）


# API Endpoints

def _normalize_url(url):
    """Convert any path/URL to /media/... format for frontend rendering."""
    if not url or not isinstance(url, str):
        return url
    if url.startswith("http://") or url.startswith("https://") or url.startswith("/media/"):
        return url
    if "/media/" in url:
        return url[url.index("/media/"):]
    # Absolute filesystem path → use local_path_to_url
    if url.startswith("/"):
        from app.services.media_storage import local_path_to_url
        normalized = local_path_to_url(url)
        return normalized if normalized else url
    return url


def _normalize_character(c: Character) -> None:
    """Normalize all image-bearing fields to /media/... URLs."""
    if c.selected_image:
        c.selected_image = _normalize_url(c.selected_image)
    if isinstance(c.alternative_images, list):
        c.alternative_images = [_normalize_url(u) for u in c.alternative_images if u]
    if isinstance(c.three_views, dict):
        c.three_views = {
            k: (_normalize_url(v) if isinstance(v, str) else v)
            for k, v in c.three_views.items()
        }


@router.get("", response_model=List[CharacterResponse])
async def get_characters(
    project_id: Optional[int] = None,
    style: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all characters, optionally filtered"""
    query = select(Character)
    if project_id:
        query = query.where(Character.project_id == project_id)
    if style:
        query = query.where(Character.style == style)
    result = await db.execute(query)
    characters = result.scalars().all()
    for c in characters:
        _normalize_character(c)
    return characters


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(character_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific character"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    _normalize_character(character)
    return character


@router.post("", response_model=CharacterResponse)
async def create_character(character: CharacterCreate, db: AsyncSession = Depends(get_db)):
    """Create a new character"""
    db_character = Character(
        name=character.name,
        project_id=character.project_id,
    )

    if character.description:
        db_character.age = character.description.age
        db_character.gender = character.description.gender
        db_character.occupation = character.description.occupation
        db_character.personality = character.description.personality
        db_character.appearance = character.description.appearance
        db_character.clothing = character.description.clothing

    if character.voice_config:
        db_character.voice_config = character.voice_config.model_dump()

    # Generate character ID for consistency
    db_character.character_id = f"char_{uuid.uuid4().hex[:8]}"

    db.add(db_character)
    await db.commit()
    await db.refresh(db_character)
    return db_character


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: int,
    character: CharacterUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a character"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    db_character = result.scalar_one_or_none()
    if not db_character:
        raise HTTPException(status_code=404, detail="Character not found")

    update_data = character.model_dump(exclude_unset=True)

    # Handle description fields
    if "description" in update_data and update_data["description"]:
        desc = update_data.pop("description")
        for field in ["age", "gender", "occupation", "personality", "appearance", "clothing"]:
            if field in desc:
                setattr(db_character, field, desc[field])

    for field, value in update_data.items():
        setattr(db_character, field, value)

    await db.commit()
    await db.refresh(db_character)
    return db_character


@router.delete("/{character_id}")
async def delete_character(character_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a character and clean up its media folder."""
    import shutil
    from app.services.media_storage import get_character_dir

    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Capture media path before deletion
    project_id = character.project_id
    name = character.name

    await db.delete(character)
    await db.commit()

    # Remove character's media folder (best-effort)
    if project_id and name:
        try:
            char_dir = get_character_dir(project_id, name)
            if os.path.isdir(char_dir):
                shutil.rmtree(char_dir)
        except Exception as e:
            print(f"[delete_character] Failed to remove media dir: {e}")

    return {"message": "Character deleted successfully", "character_id": character_id}


@router.post("/{character_id}/generate-image", response_model=GenerateImageResponse)
async def generate_character_image(
    character_id: int,
    request: GenerateImageRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate character images using AI"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取图像模型配置
    config_result = await db.execute(
        select(ModelConfig).where(ModelConfig.name == "image", ModelConfig.is_active == True)
    )
    config = config_result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=400, detail="图像模型未配置，请先在设置中配置图像模型")

    # 构建角色描述提示词
    appearance_parts = []
    if character.appearance:
        appearance_parts.append(f"appearance: {character.appearance}")
    if character.clothing:
        appearance_parts.append(f"clothing: {character.clothing}")
    if character.gender:
        appearance_parts.append(f"gender: {character.gender}")
    if character.age:
        appearance_parts.append(f"age: {character.age}")

    base_prompt = ", ".join(appearance_parts) if appearance_parts else character.name
    if request.prompt_suffix:
        base_prompt += f", {request.prompt_suffix}"

    # 调用图像生成服务
    from app.services.image_service import get_image_service

    service = get_image_service(
        provider=config.provider,
        api_key=config.api_key,
        model=config.model,
        base_url=config.base_url,
        **(config.params or {})
    )

    project_id = character.project_id

    generated_images = {}
    for style in request.styles:
        style_prompt = f"{base_prompt}, {style} style, character portrait, full body shot, high quality"
        try:
            gen_result = await service.generate(prompt=style_prompt, project_id=project_id)
            if gen_result.success and gen_result.data:
                images = gen_result.data.get("images", [])
                generated_images[style] = images
            else:
                generated_images[style] = []
        except Exception as e:
            generated_images[style] = []
            print(f"Image generation failed for style {style}: {e}")

    # 保存生成的图片
    all_images = []
    for imgs in generated_images.values():
        all_images.extend(imgs)
    character.alternative_images = all_images
    if all_images:
        character.selected_image = all_images[0]
    await db.commit()

    return GenerateImageResponse(
        images=generated_images,
        message=f"已生成 {len(all_images)} 张角色形象图"
    )


@router.get("/{character_id}/preview-three-views-prompt")
async def preview_three_views_prompt(
    character_id: int,
    style: Optional[str] = "anime",
    prompt_suffix: Optional[str] = "",
    db: AsyncSession = Depends(get_db)
):
    """预览三视图生成提示词（不实际生成，供用户编辑）"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    desc_parts = []
    if character.appearance:
        desc_parts.append(character.appearance)
    if character.clothing:
        desc_parts.append(f"wearing {character.clothing}")
    base_desc = ", ".join(desc_parts) if desc_parts else character.name
    if prompt_suffix:
        base_desc += f", {prompt_suffix}"

    effective_style = style or "anime"
    style_tags = "Japanese anime style, 日系动漫, vibrant colors, high quality, clean lineart"
    if character.gender == "女":
        style_tags += ", beautiful anime girl, sexy cute, alluring, delicate features, soft facial lines, eye-catching"

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

    return {"character_id": character_id, "prompt": combined_prompt, "style": effective_style}


@router.post("/{character_id}/generate-three-views")
async def generate_character_three_views(
    character_id: int,
    request: GenerateThreeViewsRequest = GenerateThreeViewsRequest(),
    db: AsyncSession = Depends(get_db)
):
    """生成角色三视图（正面/侧面/背面），保存到角色专属文件夹"""
    from app.services.character_consistency import CharacterConsistencyService

    service = CharacterConsistencyService(db)
    result = await service.generate_three_views(
        character_id=character_id,
        style=request.style or "anime",
        prompt_suffix=request.prompt_suffix or "",
        custom_prompt=request.custom_prompt or ""
    )

    if "error" in result:
        raise HTTPException(status_code=404 if "not found" in result["error"] else 400, detail=result["error"])

    return {
        "character_id": character_id,
        "views": result["views"],
        "selected_image": result["selected_image"],
        "message": "三视图生成完成"
    }


@router.post("/{character_id}/select-image")
async def select_character_image(
    character_id: int,
    image_url: str,
    db: AsyncSession = Depends(get_db)
):
    """Select an image for the character"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    character.selected_image = image_url
    await db.commit()
    return {"message": "Image selected successfully"}


@router.post("/{character_id}/upload-image")
async def upload_character_image(
    character_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload an image for the character"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # TODO: Implement actual file upload and storage
    # For now, return a mock URL
    mock_url = f"https://storage.example.com/characters/{character_id}/{file.filename}"
    character.selected_image = mock_url
    await db.commit()

    return {"url": mock_url, "message": "Image uploaded successfully"}
