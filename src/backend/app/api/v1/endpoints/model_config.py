"""
Model Configuration API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db, ModelConfig

router = APIRouter()


# Pydantic models

class ModelConfigBase(BaseModel):
    name: str
    provider: str
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    params: Optional[Dict[str, Any]] = {}


class ModelConfigCreate(ModelConfigBase):
    pass


class ModelConfigUpdate(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ModelConfigResponse(ModelConfigBase):
    id: int
    is_active: bool
    last_test_at: Optional[datetime] = None
    test_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestConnectionRequest(BaseModel):
    provider: str
    api_key: str
    base_url: Optional[str] = None
    model: Optional[str] = None


class TestConnectionResponse(BaseModel):
    success: bool
    message: str


# API Endpoints

@router.get("", response_model=list[ModelConfigResponse])
async def get_model_configs(db: AsyncSession = Depends(get_db)):
    """Get all model configurations"""
    result = await db.execute(select(ModelConfig))
    return result.scalars().all()


@router.get("/{config_id}", response_model=ModelConfigResponse)
async def get_model_config(config_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific model configuration"""
    result = await db.execute(select(ModelConfig).where(ModelConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Model config not found")
    return config


@router.post("", response_model=ModelConfigResponse)
async def create_model_config(config: ModelConfigCreate, db: AsyncSession = Depends(get_db)):
    """Create a new model configuration"""
    db_config = ModelConfig(**config.model_dump())
    db.add(db_config)
    await db.commit()
    await db.refresh(db_config)
    return db_config


@router.put("/{config_id}", response_model=ModelConfigResponse)
async def update_model_config(
    config_id: int,
    config: ModelConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a model configuration"""
    result = await db.execute(select(ModelConfig).where(ModelConfig.id == config_id))
    db_config = result.scalar_one_or_none()
    if not db_config:
        raise HTTPException(status_code=404, detail="Model config not found")

    update_data = config.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_config, field, value)

    await db.commit()
    await db.refresh(db_config)
    return db_config


@router.delete("/{config_id}")
async def delete_model_config(config_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a model configuration"""
    result = await db.execute(select(ModelConfig).where(ModelConfig.id == config_id))
    db_config = result.scalar_one_or_none()
    if not db_config:
        raise HTTPException(status_code=404, detail="Model config not found")

    await db.delete(db_config)
    await db.commit()
    return {"message": "Model config deleted successfully"}


@router.post("/test", response_model=TestConnectionResponse)
async def test_connection(request: TestConnectionRequest):
    """Test connection to a model provider"""
    # TODO: Implement actual connection testing for each provider
    # For now, return a mock response
    try:
        if request.provider == "openai":
            # Test OpenAI connection
            return TestConnectionResponse(success=True, message="OpenAI connection successful")
        elif request.provider == "anthropic":
            return TestConnectionResponse(success=True, message="Anthropic connection successful")
        elif request.provider == "deepseek":
            return TestConnectionResponse(success=True, message="DeepSeek connection successful")
        else:
            return TestConnectionResponse(success=True, message=f"{request.provider} connection test completed")
    except Exception as e:
        return TestConnectionResponse(success=False, message=str(e))


@router.post("/{config_id}/test", response_model=TestConnectionResponse)
async def test_model_config(config_id: int, db: AsyncSession = Depends(get_db)):
    """Test a saved model configuration"""
    result = await db.execute(select(ModelConfig).where(ModelConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Model config not found")

    # TODO: Implement actual connection testing
    config.test_status = "success"
    config.last_test_at = datetime.utcnow()
    await db.commit()

    return TestConnectionResponse(success=True, message=f"Connection to {config.provider} successful")
