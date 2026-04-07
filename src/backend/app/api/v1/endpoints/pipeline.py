"""
Pipeline API endpoints
一键生成流水线API
"""
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import asyncio

from app.core.database import get_db
from app.services.pipeline import VideoPipeline, PipelineProgress


router = APIRouter()


class PipelineStartRequest(BaseModel):
    """流水线启动请求"""
    project_id: int
    user_input: str
    prompt_suffix: Optional[str] = ""
    options: Optional[Dict[str, Any]] = None


class PipelineStatusResponse(BaseModel):
    """流水线状态响应"""
    project_id: int
    status: str
    progress: float
    message: str
    data: Optional[Dict[str, Any]] = None


# 存储运行中的流水线状态
_pipeline_status: Dict[int, Dict[str, Any]] = {}


@router.post("/start", response_model=Dict[str, Any])
async def start_pipeline(
    request: PipelineStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """启动一键生成流水线"""
    # 初始化状态
    _pipeline_status[request.project_id] = {
        "status": "running",
        "progress": 0.0,
        "message": "流水线启动中..."
    }

    # 后台运行流水线
    async def run_pipeline():
        pipeline = VideoPipeline(db)

        async def update_status(progress: PipelineProgress):
            _pipeline_status[request.project_id] = {
                "status": "running",
                "progress": progress.progress,
                "message": progress.message,
                "stage": progress.stage.value,
                "data": progress.data
            }

        pipeline.on_progress(update_status)

        try:
            result = await pipeline.generate_short_drama(
                project_id=request.project_id,
                user_input=request.user_input,
                options=request.options
            )
            _pipeline_status[request.project_id] = {
                "status": "completed",
                "progress": 1.0,
                "message": "生成完成",
                "result": result
            }
        except Exception as e:
            _pipeline_status[request.project_id] = {
                "status": "failed",
                "progress": 0.0,
                "message": str(e)
            }

    background_tasks.add_task(run_pipeline)

    return {
        "project_id": request.project_id,
        "status": "started",
        "message": "流水线已启动，请使用 /pipeline/status/{project_id} 查询进度"
    }


@router.get("/status/{project_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(project_id: int):
    """获取流水线状态"""
    status = _pipeline_status.get(project_id, {
        "status": "not_found",
        "progress": 0.0,
        "message": "未找到该项目的流水线任务"
    })

    return PipelineStatusResponse(
        project_id=project_id,
        status=status.get("status", "unknown"),
        progress=status.get("progress", 0.0),
        message=status.get("message", ""),
        data=status.get("data") or status.get("result")
    )


@router.post("/start/stream")
async def start_pipeline_stream(
    request: PipelineStartRequest,
    db: AsyncSession = Depends(get_db)
):
    """启动流水线并实时返回进度 (SSE)"""

    async def generate_stream():
        pipeline = VideoPipeline(db)

        progress_queue = []

        async def report_progress(progress: PipelineProgress):
            progress_queue.append(progress)

        pipeline.on_progress(report_progress)

        try:
            # 手动报告进度
            yield f"data: {json.dumps({
                'stage': 'script',
                'progress': 0.0,
                'message': '正在生成剧本...'
            }, ensure_ascii=False)}\n\n"

            result = await pipeline.generate_short_drama(
                project_id=request.project_id,
                user_input=request.user_input,
                options=request.options
            )

            # 发送收集到的进度
            for p in progress_queue:
                yield f"data: {json.dumps({
                    'stage': p.stage.value,
                    'progress': p.progress,
                    'message': p.message,
                    'data': p.data
                }, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({
                'stage': 'completed',
                'progress': 1.0,
                'message': '生成完成',
                'result': result
            }, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({
                'stage': 'failed',
                'progress': 0.0,
                'message': str(e)
            }, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.delete("/status/{project_id}")
async def clear_pipeline_status(project_id: int):
    """清除流水线状态"""
    if project_id in _pipeline_status:
        del _pipeline_status[project_id]
        return {"message": "Pipeline status cleared"}
    return {"message": "Pipeline status not found"}
