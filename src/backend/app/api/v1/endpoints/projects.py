"""
Projects API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, AsyncGenerator
from datetime import datetime
import json
import asyncio

from app.core.database import get_db, Project, Character, ModelConfig
from app.services.llm_service import get_llm_service
from app.services.prompts import get_script_prompt

router = APIRouter()


# Pydantic models

class ProjectBase(BaseModel):
    name: str
    type: str  # drama, video
    description: Optional[str] = None
    genre: Optional[str] = None
    style: Optional[str] = None
    duration: Optional[int] = 180
    target_platform: Optional[str] = None


class ProjectCreate(ProjectBase):
    ai_model_config: Optional[Dict[str, Any]] = {}
    prompt_overrides: Optional[Dict[str, str]] = {}


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    style: Optional[str] = None
    duration: Optional[int] = None
    target_platform: Optional[str] = None
    status: Optional[str] = None
    ai_model_config: Optional[Dict[str, Any]] = None
    prompt_overrides: Optional[Dict[str, str]] = None
    script_content: Optional[Dict[str, Any]] = None


class ProjectResponse(ProjectBase):
    id: int
    status: str
    ai_model_config: Dict[str, Any]
    prompt_overrides: Dict[str, str]
    script_content: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScriptGenerateRequest(BaseModel):
    input: str = ""
    prompt_suffix: Optional[str] = ""


# API Endpoints

@router.get("", response_model=List[ProjectResponse])
async def get_projects(
    type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all projects"""
    query = select(Project)
    if type:
        query = query.where(Project.type == type)
    if status:
        query = query.where(Project.status == status)
    query = query.order_by(Project.updated_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific project"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """Create a new project"""
    db_project = Project(**project.model_dump())
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a project"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    db_project = result.scalar_one_or_none()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)

    await db.commit()
    await db.refresh(db_project)
    return db_project


@router.delete("/{project_id}")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a project"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()
    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/script/generate")
async def generate_script(
    project_id: int,
    request: ScriptGenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate script for a project using AI (Streaming response)"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    async def generate_stream() -> AsyncGenerator[str, None]:
        # 获取模型配置
        config_result = await db.execute(
            select(ModelConfig).where(ModelConfig.name == "text", ModelConfig.is_active == True)
        )
        model_config = config_result.scalar_one_or_none()

        # 发送开始状态
        yield f"data: {json.dumps({'status': 'starting', 'message': '正在准备生成剧本...', 'progress': 10}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        # 获取提示词
        system_prompt, user_prompt = get_script_prompt(
            name=project.name,
            type=project.type,
            style=project.style,
            genre=project.genre,
            duration=project.duration,
            platform=project.target_platform,
            description=project.description,
            user_input=request.input
        )

        # 添加用户额外提示词
        if request.prompt_suffix:
            user_prompt += f"\n\n## 用户额外要求\n{request.prompt_suffix}"

        yield f"data: {json.dumps({'status': 'generating', 'message': '正在调用AI生成剧本...', 'progress': 20}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        # 调用 AI 生成
        script_content = None
        message = ""

        if model_config and model_config.api_key:
            try:
                provider_name = {
                    "qwen": "通义千问",
                    "openai": "GPT",
                    "anthropic": "Claude",
                    "deepseek": "DeepSeek"
                }.get(model_config.provider.lower(), model_config.provider)

                yield f"data: {json.dumps({'status': 'generating', 'message': f'正在使用 {provider_name} 生成剧本，请耐心等待...', 'progress': 30}, ensure_ascii=False)}\n\n"

                llm_service = get_llm_service(
                    provider=model_config.provider,
                    api_key=model_config.api_key,
                    model=model_config.model,
                    base_url=model_config.base_url
                )

                generation_result = await llm_service.generate(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    temperature=0.8,
                    max_tokens=8000
                )

                if generation_result.success and generation_result.data:
                    script_content = generation_result.data
                    message = "✨ 剧本生成成功！"
                elif generation_result.success and generation_result.content:
                    # 尝试从内容解析 JSON
                    try:
                        content = generation_result.content.strip()
                        # 处理 markdown 代码块
                        if content.startswith("```json"):
                            content = content[7:]
                        elif content.startswith("```"):
                            content = content[3:]
                        if content.endswith("```"):
                            content = content[:-3]
                        script_content = json.loads(content.strip())
                        message = "✨ 剧本生成成功！"
                    except json.JSONDecodeError as e:
                        script_content = get_mock_script(project)
                        message = f"⚠️ AI 响应格式解析失败，已使用默认模板"
                else:
                    script_content = get_mock_script(project)
                    message = f"⚠️ AI 生成失败: {generation_result.error}，已使用默认模板"

            except Exception as e:
                script_content = get_mock_script(project)
                message = f"⚠️ AI 调用异常: {str(e)}，已使用默认模板"
        else:
            script_content = get_mock_script(project)
            message = "⚠️ 未配置 AI 模型，已使用默认模板。请在【设置-模型配置】中配置模型后重试。"

        # 保存到数据库
        yield f"data: {json.dumps({'status': 'saving', 'message': '正在保存剧本...', 'progress': 90}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.2)

        project.script_content = script_content
        project.status = "in_progress"
        await db.commit()

        # 返回最终结果
        yield f"data: {json.dumps({'status': 'completed', 'message': message, 'progress': 100, 'script': script_content}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


def get_mock_script(project: Project) -> Dict[str, Any]:
    """生成模拟剧本数据"""
    return {
        "title": project.name,
        "logline": f"一个关于{project.description or '人生'}的故事",
        "theme": "成长与选择",
        "total_duration": project.duration or 180,
        "characters": [
            {
                "name": "主角",
                "role": "主角",
                "age": 25,
                "gender": "male",
                "occupation": "程序员",
                "personality": {
                    "traits": ["温和", "内敛", "有责任心"],
                    "strengths": ["专注", "善良"],
                    "weaknesses": ["不善表达", "过于理想化"]
                },
                "appearance": {
                    "face": "清秀的脸庞，黑框眼镜",
                    "hair": "短发，略微凌乱",
                    "body": "清瘦身材",
                    "distinctive_features": "左手腕戴着一块旧手表"
                },
                "clothing": {
                    "style": "休闲简约",
                    "casual": "卫衣、牛仔裤",
                    "colors": ["深蓝", "灰色", "白色"]
                },
                "backstory": "一个刚毕业的程序员，怀揣梦想来到大城市"
            }
        ],
        "scenes": [
            {
                "id": 1,
                "name": "开场",
                "location": "城市街道",
                "environment": "繁华的都市街道，高楼林立，人流如织",
                "time": "清晨",
                "mood": "希望与迷茫交织",
                "description": "主角独自走在上班的路上",
                "shots": [
                    {
                        "id": 1,
                        "type": "远景",
                        "angle": "俯拍",
                        "movement": "缓慢推进",
                        "description": "城市全景，晨光初现，高楼林立",
                        "action": "镜头从高空缓缓下降",
                        "emotion": "平静",
                        "duration": 5,
                        "transition": "淡入"
                    },
                    {
                        "id": 2,
                        "type": "全景",
                        "angle": "平视",
                        "movement": "跟拍",
                        "description": "主角背着双肩包走在人群中",
                        "action": "快步前行，低头看手机",
                        "emotion": "匆忙",
                        "duration": 4,
                        "transition": "硬切"
                    }
                ]
            }
        ]
    }


@router.get("/{project_id}/characters", response_model=List["CharacterResponse"])
async def get_project_characters(project_id: int, db: AsyncSession = Depends(get_db)):
    """Get all characters in a project"""
    result = await db.execute(
        select(Character).where(Character.project_id == project_id)
    )
    return result.scalars().all()


# Import CharacterResponse from characters module
from .characters import CharacterResponse
