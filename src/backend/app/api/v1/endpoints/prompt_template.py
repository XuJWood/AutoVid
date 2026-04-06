"""
Prompt Template API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

from app.core.database import get_db, PromptTemplate

router = APIRouter()


# Pydantic models

class PromptTemplateBase(BaseModel):
    name: str
    type: str  # script, character, storyboard, video
    template: str
    variables: Optional[List[str]] = []
    is_default: Optional[bool] = False


class PromptTemplateCreate(PromptTemplateBase):
    pass


class PromptTemplateUpdate(BaseModel):
    name: Optional[str] = None
    template: Optional[str] = None
    variables: Optional[List[str]] = None
    is_default: Optional[bool] = None


class PromptTemplateResponse(PromptTemplateBase):
    id: int
    is_system: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RenderTemplateRequest(BaseModel):
    template_id: int
    variables: Dict[str, Any]


class RenderTemplateResponse(BaseModel):
    rendered_prompt: str


# Default templates

DEFAULT_TEMPLATES = [
    {
        "name": "默认剧本模板",
        "type": "script",
        "is_system": True,
        "is_default": True,
        "template": """你是一位专业的短剧编剧。请根据用户输入生成完整的短剧剧本。

## 输出要求

1. **角色设定**
   - 每个角色的姓名、年龄、职业
   - 外貌特征描述（用于后续生成形象）
   - 性格特点、说话风格

2. **场景列表**
   - 场景名称、环境描述
   - 时间设定（白天/夜晚）
   - 氛围基调

3. **分镜脚本**
   - 每个镜头的：镜头类型、画面描述、角色动作、对白台词
   - 时长预估
   - 情绪标注

## 格式要求
请以JSON格式输出，结构如下：
{
  "title": "剧名",
  "characters": [...],
  "scenes": [...]
}

# 用户补充
{user_prompt}

# 用户输入
{user_input}""",
        "variables": ["user_prompt", "user_input", "genre", "duration", "character_count", "tone"]
    },
    {
        "name": "默认角色模板",
        "type": "character",
        "is_system": True,
        "is_default": True,
        "template": """请根据以下角色描述生成人物形象图。

## 角色信息
- 姓名：{character_name}
- 年龄：{character_age}
- 性别：{character_gender}
- 外貌：{character_appearance}
- 服装：{character_clothing}
- 气质：{character_temperament}

## 生成要求
- 生成{style_count}种不同风格：写实、动漫、电影质感、水墨风
- 每种风格生成{count_per_style}张
- 确保面部特征清晰，适合作为角色参考图
- 生成三视图：正面、侧面、背面

## 输出格式
高质量人物肖像，{aspect_ratio}，{quality}

# 用户补充
{user_prompt}""",
        "variables": ["character_name", "character_age", "character_gender", "character_appearance",
                     "character_clothing", "character_temperament", "style_count", "count_per_style",
                     "aspect_ratio", "quality", "user_prompt"]
    },
    {
        "name": "默认分镜模板",
        "type": "storyboard",
        "is_system": True,
        "is_default": True,
        "template": """请根据以下信息生成分镜图：

## 场景信息
- 场景名称：{scene_name}
- 环境描述：{environment}
- 时间：{time_of_day}
- 氛围：{mood}

## 镜头信息
- 镜头类型：{shot_type}
- 画面描述：{description}
- 角色动作：{action}
- 角色：{characters}

## 生成要求
- 保持角色面部特征一致
- 符合场景氛围
- 构图美观

# 用户补充
{user_prompt}""",
        "variables": ["scene_name", "environment", "time_of_day", "mood", "shot_type",
                     "description", "action", "characters", "user_prompt"]
    },
    {
        "name": "默认视频模板",
        "type": "video",
        "is_system": True,
        "is_default": True,
        "template": """请根据以下信息生成视频：

## 输入图像
{source_image}

## 动作描述
{action_description}

## 角色一致性参考
{character_reference}

## 视频参数
- 时长：{duration}秒
- 镜头运动：{camera_movement}
- 氛围：{mood}

## 生成要求
- 保持角色面部特征一致
- 动作自然流畅
- 符合物理规律

# 用户补充
{user_prompt}""",
        "variables": ["source_image", "action_description", "character_reference", "duration",
                     "camera_movement", "mood", "user_prompt"]
    }
]


# API Endpoints

@router.get("", response_model=List[PromptTemplateResponse])
async def get_prompt_templates(
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all prompt templates, optionally filtered by type"""
    query = select(PromptTemplate)
    if type:
        query = query.where(PromptTemplate.type == type)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template(template_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific prompt template"""
    result = await db.execute(select(PromptTemplate).where(PromptTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    return template


@router.post("", response_model=PromptTemplateResponse)
async def create_prompt_template(template: PromptTemplateCreate, db: AsyncSession = Depends(get_db)):
    """Create a new prompt template"""
    # Extract variables from template
    variables = re.findall(r'\{(\w+)\}', template.template)

    db_template = PromptTemplate(
        **template.model_dump(),
        variables=variables,
        is_system=False
    )
    db.add(db_template)
    await db.commit()
    await db.refresh(db_template)
    return db_template


@router.put("/{template_id}", response_model=PromptTemplateResponse)
async def update_prompt_template(
    template_id: int,
    template: PromptTemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a prompt template"""
    result = await db.execute(select(PromptTemplate).where(PromptTemplate.id == template_id))
    db_template = result.scalar_one_or_none()
    if not db_template:
        raise HTTPException(status_code=404, detail="Prompt template not found")

    if db_template.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system templates")

    update_data = template.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_template, field, value)

    # Update variables if template changed
    if template.template:
        db_template.variables = re.findall(r'\{(\w+)\}', template.template)

    await db.commit()
    await db.refresh(db_template)
    return db_template


@router.delete("/{template_id}")
async def delete_prompt_template(template_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a prompt template"""
    result = await db.execute(select(PromptTemplate).where(PromptTemplate.id == template_id))
    db_template = result.scalar_one_or_none()
    if not db_template:
        raise HTTPException(status_code=404, detail="Prompt template not found")

    if db_template.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system templates")

    await db.delete(db_template)
    await db.commit()
    return {"message": "Prompt template deleted successfully"}


@router.post("/render", response_model=RenderTemplateResponse)
async def render_template(request: RenderTemplateRequest, db: AsyncSession = Depends(get_db)):
    """Render a template with variables"""
    result = await db.execute(select(PromptTemplate).where(PromptTemplate.id == request.template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Prompt template not found")

    try:
        rendered = template.template.format(**request.variables)
        return RenderTemplateResponse(rendered_prompt=rendered)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing variable: {e}")


@router.post("/init-defaults")
async def init_default_templates(db: AsyncSession = Depends(get_db)):
    """Initialize default prompt templates"""
    for template_data in DEFAULT_TEMPLATES:
        # Check if already exists
        result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.name == template_data["name"])
        )
        existing = result.scalar_one_or_none()
        if not existing:
            template = PromptTemplate(**template_data)
            db.add(template)

    await db.commit()
    return {"message": "Default templates initialized"}
