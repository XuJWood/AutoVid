"""
API v1 router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import model_config, prompt_template, projects, characters, videos

api_router = APIRouter()

api_router.include_router(model_config.router, prefix="/model-config", tags=["Model Config"])
api_router.include_router(prompt_template.router, prefix="/prompt-templates", tags=["Prompt Templates"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(characters.router, prefix="/characters", tags=["Characters"])
api_router.include_router(videos.router, prefix="/videos", tags=["Videos"])
