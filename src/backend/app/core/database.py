"""
Database configuration and session management
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean, ForeignKey
from datetime import datetime

from app.core.config import settings


# Async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


# Database Models

class Project(Base):
    """Project model"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # drama, video
    status = Column(String(50), default="draft")  # draft, in_progress, completed
    description = Column(Text, nullable=True)

    # Configuration
    genre = Column(String(100), nullable=True)
    style = Column(String(100), nullable=True)
    duration = Column(Integer, default=180)
    target_platform = Column(String(50), nullable=True)

    # Model config for this project
    ai_model_config = Column(JSON, default=dict)

    # Prompt overrides
    prompt_overrides = Column(JSON, default=dict)

    # Script content (JSON)
    script_content = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Character(Base):
    """Character model"""
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    name = Column(String(100), nullable=False)

    # Description
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    occupation = Column(String(100), nullable=True)
    personality = Column(Text, nullable=True)
    appearance = Column(Text, nullable=True)
    clothing = Column(Text, nullable=True)

    # Images
    selected_image = Column(String(500), nullable=True)
    alternative_images = Column(JSON, default=list)
    three_views = Column(JSON, default=dict)  # {front, side, back} → local paths
    style = Column(String(50), default="anime")

    # Character ID for consistency
    character_id = Column(String(100), nullable=True)

    # Voice config
    voice_config = Column(JSON, default=dict)

    # Wardrobe
    wardrobe = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModelConfig(Base):
    """Model configuration model"""
    __tablename__ = "model_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # script, image, video, voice
    provider = Column(String(100), nullable=False)
    model = Column(String(100), nullable=True)
    api_key = Column(String(500), nullable=True)
    base_url = Column(String(500), nullable=True)

    # Model parameters
    params = Column(JSON, default=dict)

    # Status
    is_active = Column(Boolean, default=True)
    last_test_at = Column(DateTime, nullable=True)
    test_status = Column(String(50), default="untested")  # untested, success, failed

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PromptTemplate(Base):
    """Prompt template model"""
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # script, character, storyboard, video
    template = Column(Text, nullable=False)
    variables = Column(JSON, default=list)
    is_default = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)  # System templates cannot be deleted

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GeneratedVideo(Base):
    """Generated video model"""
    __tablename__ = "generated_videos"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=True)

    # Video info
    file_path = Column(String(500), nullable=True)
    thumbnail_path = Column(String(500), nullable=True)
    duration = Column(Integer, default=5)
    resolution = Column(String(20), default="1080p")
    aspect_ratio = Column(String(20), default="16:9")

    # Generation info
    model_provider = Column(String(100), nullable=True)
    prompt_used = Column(Text, nullable=True)
    generation_params = Column(JSON, default=dict)

    # Status
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class Storyboard(Base):
    """Episode model — each row = one episode (~20s) of the anime short drama"""
    __tablename__ = "storyboards"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Episode ordering
    episode_number = Column(Integer, default=0)  # 1-based episode number
    scene_index = Column(Integer, default=0)     # kept for backward compat
    shot_index = Column(Integer, default=0)      # always 0 for episodes

    # Episode data
    title = Column(String(200))
    episode_script = Column(Text)          # Full mini-script for this episode
    dialogue_lines = Column(JSON, default=list)  # [{speaker, text, emotion}, ...]
    character_ids = Column(JSON, default=list)   # [1, 2] — character IDs appearing in this episode
    shot_type = Column(String(50))        # kept for backward compat
    description = Column(Text)            # Episode synopsis
    image_prompt = Column(Text)           # AI image prompt (anime style)
    video_prompt = Column(Text)           # AI video prompt (anime style, ~20s)
    duration = Column(Integer, default=20)  # Target ~20s per episode

    # Generated resources
    image_url = Column(String(500))
    video_url = Column(String(500))
    audio_url = Column(String(500))

    # Status
    status = Column(String(50), default="pending")  # pending/processing/completed/failed

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


async def get_db() -> AsyncSession:
    """Dependency for getting database session"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
