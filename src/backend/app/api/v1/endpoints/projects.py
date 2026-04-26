"""
Projects API endpoints
"""
from __future__ import annotations
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
from app.api.v1.endpoints.characters import CharacterResponse

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
            user_input=request.input,
            prompt_suffix=request.prompt_suffix or ""
        )

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

        # 自动创建角色记录
        if script_content.get("characters"):
            for char_data in script_content["characters"]:
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
                    style="anime"
                )
                db.add(character)
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
    """生成模拟漫剧剧本数据"""
    return {
        "title": project.name,
        "logline": f"一个关于{project.description or '命运'}的日系动漫短剧",
        "theme": "成长与选择",
        "total_duration": project.duration or 180,
        "art_style": "日系动漫风，二次元，精致的线条和色彩",
        "hook_description": "神秘转学生突然出现在教室，她身上的秘密即将揭开",
        "twist_points": ["反转1：转学生的真实身份", "反转2：主角隐藏的能力觉醒", "反转3：真正的敌人是最亲近的人"],
        "characters": [
            {
                "name": "小樱",
                "role": "主角",
                "age": 17,
                "gender": "女",
                "occupation": "高中生",
                "personality": "活泼开朗、善良勇敢、偶尔冒失",
                "appearance": "精致的瓜子脸，大而有神的紫色眼眸，粉色双马尾长发，纤细的身材，白皙的皮肤",
                "clothing": "日系学院风，白色水手服配蓝色短裙，日常穿可爱的连衣裙，战斗时穿魔法少女装",
                "background": "看似普通的高中女生，其实体内隐藏着远古的魔力",
                "archetype": "觉醒少女"
            },
            {
                "name": "夜",
                "role": "男主",
                "age": 18,
                "gender": "男",
                "occupation": "高中生/暗影守卫",
                "personality": "冷酷寡言、深情专一、行动力强",
                "appearance": "俊朗的面容，深邃的蓝色眼睛，银色短发，修长的身材，皮肤偏白",
                "clothing": "黑色校服外套，日常穿深色系休闲装，战斗时穿暗影风衣",
                "background": "被派来保护小樱的暗影守卫，但逐渐对她产生真正的感情",
                "archetype": "冷面守护者"
            }
        ],
        "episodes": [
            {
                "episode_number": 1,
                "title": "神秘的转学生",
                "location": "樱花高中",
                "environment": "日系动漫风格的校园，樱花飘落的教室，温暖的光线",
                "time": "清晨",
                "mood": "好奇与期待",
                "conflict": "小樱对新来的转学生感到莫名的熟悉又不安",
                "twist": "转学生夜其实一直在暗中观察小樱",
                "description": "新学期第一天，神秘转学生夜出现在小樱的班上",
                "script": "小樱走在樱花飘落的校园小路上。教室里，老师介绍新来的转学生夜。夜的眼神碰到小樱的瞬间，小樱心中涌起一种奇妙的感觉。课后，小樱发现自己被一群黑衣人跟踪。",
                "dialogues": [
                    {"speaker": "老师", "text": "今天有一位新同学加入我们班", "emotion": "平和"},
                    {"speaker": "夜", "text": "我叫夜，请多关照", "emotion": "冷淡"},
                    {"speaker": "小樱", "text": "这个人...我好像在哪里见过？", "emotion": "疑惑"},
                    {"speaker": "小樱", "text": "你们是谁？为什么跟着我？", "emotion": "紧张"}
                ],
                "shots": [
                    {
                        "id": 1,
                        "type": "全景",
                        "angle": "平视",
                        "movement": "跟拍",
                        "description": "樱花飘落的校园，小樱走在路上，日系动漫风格的清新画面",
                        "action": "小樱抬头看樱花，微笑",
                        "dialogue": "小樱：又是樱花盛开的季节呢",
                        "emotion": "温馨",
                        "duration": 5,
                        "transition": "淡入"
                    },
                    {
                        "id": 2,
                        "type": "近景",
                        "angle": "平视",
                        "movement": "推",
                        "description": "教室内，老师介绍新同学，夜站在黑板前，画面聚焦他的眼神",
                        "action": "夜的视线转向小樱",
                        "dialogue": "夜：我叫夜，请多关照",
                        "emotion": "好奇",
                        "duration": 6,
                        "transition": "硬切"
                    },
                    {
                        "id": 3,
                        "type": "特写",
                        "angle": "平视",
                        "movement": "固定",
                        "description": "小樱的脸部特写，她的眼神中闪过惊讶和困惑",
                        "action": "小樱微微皱眉，手不由自主地握紧",
                        "dialogue": "小樱：这个人...我好像在哪里见过？",
                        "emotion": "疑惑",
                        "duration": 4,
                        "transition": "硬切"
                    },
                    {
                        "id": 4,
                        "type": "中景",
                        "angle": "平视",
                        "movement": "跟拍",
                        "description": "放学后，小樱被黑衣人跟踪，日系动漫的紧张氛围",
                        "action": "黑衣人逼近小樱",
                        "dialogue": "小樱：你们是谁？为什么跟着我？",
                        "emotion": "紧张",
                        "duration": 5,
                        "transition": "硬切"
                    }
                ]
            },
            {
                "episode_number": 2,
                "title": "觉醒的力量",
                "location": "学校后山",
                "environment": "夕阳下的山丘，金色光辉洒满画面，日系动漫的浪漫场景",
                "time": "黄昏",
                "mood": "紧张与感动",
                "conflict": "黑衣人围攻小樱，她的魔法力量首次觉醒",
                "description": "夜在关键时刻出手相救，小樱发现自己的特殊力量",
                "script": "黑衣人围住小樱。危机时刻夜突然出现击退了黑衣人。小樱的魔法力量意外觉醒，周围绽放出耀眼的光芒。夜向震惊的小樱解释了一切。",
                "dialogues": [
                    {"speaker": "夜", "text": "退下，她是受暗影议会保护的人", "emotion": "威严"},
                    {"speaker": "小樱", "text": "夜？！你到底是什么人？", "emotion": "震惊"},
                    {"speaker": "夜", "text": "我是暗影守卫，而你是我们一直在寻找的'光之继承者'", "emotion": "认真"},
                    {"speaker": "小樱", "text": "光之...继承者？", "emotion": "迷茫"}
                ],
                "shots": [
                    {
                        "id": 1,
                        "type": "中景",
                        "angle": "仰拍",
                        "movement": "推",
                        "description": "黑衣人包围小樱，她孤立无援地站在夕阳下的山丘上",
                        "action": "黑衣人缓缓逼近",
                        "emotion": "紧张",
                        "duration": 5,
                        "transition": "硬切"
                    },
                    {
                        "id": 2,
                        "type": "近景",
                        "angle": "平视",
                        "movement": "跟拍",
                        "description": "夜从高处跳下挡在小樱身前，暗影风衣随风飘扬",
                        "action": "夜单手挡开黑衣人",
                        "dialogue": "夜：退下，她是受暗影议会保护的人",
                        "emotion": "酷",
                        "duration": 5,
                        "transition": "硬切"
                    },
                    {
                        "id": 3,
                        "type": "特写",
                        "angle": "平视",
                        "movement": "固定-拉",
                        "description": "小樱的身体周围开始绽放粉色光芒，魔法纹路浮现",
                        "action": "小樱惊讶地看着自己的双手发光",
                        "dialogue": "小樱：这是...什么力量？",
                        "emotion": "震惊",
                        "duration": 6,
                        "transition": "叠化"
                    },
                    {
                        "id": 4,
                        "type": "近景",
                        "angle": "平视",
                        "movement": "固定",
                        "description": "夜向小樱单膝跪下，夕阳给他们镀上金色光辉",
                        "action": "夜单膝跪地",
                        "dialogue": "夜：我是暗影守卫，而你是我们一直在寻找的'光之继承者'",
                        "emotion": "感动",
                        "duration": 4,
                        "transition": "淡出"
                    }
                ]
            }
        ]
    }


@router.get("/{project_id}/characters", response_model=List[CharacterResponse])
async def get_project_characters(project_id: int, db: AsyncSession = Depends(get_db)):
    """Get all characters in a project"""
    result = await db.execute(
        select(Character).where(Character.project_id == project_id)
    )
    return result.scalars().all()
