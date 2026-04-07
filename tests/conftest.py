"""
测试配置和公共fixtures
"""
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.services.base import GenerationResult


# 测试数据库配置
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session


@pytest.fixture
def test_app(test_db: AsyncSession):
    """创建测试应用，覆盖数据库依赖"""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """创建异步HTTP客户端"""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# Mock服务fixtures

@pytest.fixture
def mock_llm_service():
    """Mock LLM服务"""
    with patch("app.services.llm_service.get_llm_service") as mock:
        mock.return_value.generate = AsyncMock(return_value=GenerationResult(
            success=True,
            data={
                "title": "测试剧本",
                "logline": "一个关于测试的故事",
                "theme": "测试",
                "total_duration": 180,
                "characters": [],
                "scenes": []
            },
            content=None,
            error=None
        ))
        yield mock


@pytest.fixture
def mock_image_service():
    """Mock图像生成服务"""
    with patch("app.services.image_service.get_image_service") as mock:
        mock.return_value.generate = AsyncMock(return_value=GenerationResult(
            success=True,
            data="https://example.com/mock-image.png",
            content=None,
            error=None
        ))
        yield mock


@pytest.fixture
def mock_voice_service():
    """Mock语音合成服务"""
    with patch("app.services.voice_service.get_voice_service") as mock:
        mock.return_value.synthesize = AsyncMock(return_value=GenerationResult(
            success=True,
            data="https://example.com/mock-audio.mp3",
            content=None,
            error=None
        ))
        yield mock


# 测试数据fixtures

@pytest.fixture
def sample_project_data():
    """测试项目数据"""
    return {
        "name": "测试短剧",
        "type": "drama",
        "description": "这是一个测试项目",
        "genre": "都市",
        "style": "现代",
        "duration": 180,
        "target_platform": "抖音"
    }


@pytest.fixture
def sample_character_data():
    """测试角色数据"""
    return {
        "name": "测试角色",
        "age": 25,
        "gender": "male",
        "occupation": "程序员",
        "personality": "温和内敛",
        "appearance": "清秀的脸庞",
        "clothing": "休闲简约"
    }


@pytest.fixture
def sample_model_config_data():
    """测试模型配置数据"""
    return {
        "name": "text",
        "provider": "openai",
        "model": "gpt-4",
        "api_key": "test-api-key",
        "base_url": "https://api.openai.com/v1",
        "is_active": True
    }


@pytest.fixture
def sample_prompt_template_data():
    """测试提示词模板数据"""
    return {
        "name": "剧本生成模板",
        "type": "script",
        "template": "生成一个关于{topic}的{style}风格剧本",
        "variables": ["topic", "style"],
        "is_default": True,
        "is_system": False
    }
