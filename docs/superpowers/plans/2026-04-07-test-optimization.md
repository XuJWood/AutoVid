# 测试优化实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 ai-video-generator 项目建立完整的测试体系，包括分层测试架构、Mock服务、CI/CD流水线。

**Architecture:** 采用分层测试架构，单元测试mock服务层，集成测试使用TestClient测试API端点。使用内存SQLite隔离测试数据，GitHub Actions实现CI/CD自动化。

**Tech Stack:** pytest, pytest-asyncio, pytest-cov, httpx, unittest.mock

---

## 文件结构

```
tests/
├── __init__.py
├── conftest.py              # 公共fixtures
├── unit/
│   ├── __init__.py
│   └── services/
│       ├── __init__.py
│       ├── test_llm_service.py
│       ├── test_image_service.py
│       └── test_voice_service.py
├── integration/
│   ├── __init__.py
│   ├── test_projects.py
│   ├── test_characters.py
│   ├── test_model_config.py
│   ├── test_prompt_template.py
│   └── test_videos.py
└── e2e/
    └── __init__.py

pytest.ini
.github/workflows/test.yml
```

---

## Task 1: 测试基础设施 - pytest配置

**Files:**
- Create: `pytest.ini`
- Modify: `requirements.txt`

- [ ] **Step 1: 添加pytest依赖到requirements.txt**

在 `requirements.txt` 末尾添加:

```
# Testing (补充)
pytest-cov>=4.1.0
```

- [ ] **Step 2: 创建pytest.ini配置文件**

创建文件 `pytest.ini`:

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    unit: 单元测试
    integration: 集成测试
    e2e: 端到端测试
```

- [ ] **Step 3: 验证pytest配置**

Run: `cd /Users/a1/projects/ai-video-generator && source venv/bin/activate && pip install pytest-cov && pytest --collect-only`

Expected: 显示 "no tests collected" 或类似信息，无错误

- [ ] **Step 4: 提交**

```bash
git add pytest.ini requirements.txt
git commit -m "chore: 添加pytest配置和依赖"
```

---

## Task 2: 测试基础设施 - 目录结构

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/unit/services/__init__.py`
- Create: `tests/integration/__init__.py`
- Create: `tests/e2e/__init__.py`

- [ ] **Step 1: 创建测试目录结构**

```bash
mkdir -p tests/unit/services tests/integration tests/e2e
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/unit/services/__init__.py
touch tests/integration/__init__.py
touch tests/e2e/__init__.py
```

- [ ] **Step 2: 提交**

```bash
git add tests/
git commit -m "chore: 创建测试目录结构"
```

---

## Task 3: 测试基础设施 - conftest.py

**Files:**
- Create: `tests/conftest.py`

- [ ] **Step 1: 创建conftest.py基础结构**

创建文件 `tests/conftest.py`:

```python
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
        "is_default": True
    }
```

- [ ] **Step 2: 验证fixtures加载**

Run: `cd /Users/a1/projects/ai-video-generator && source venv/bin/activate && pytest --collect-only tests/`

Expected: 无错误，显示fixtures已加载

- [ ] **Step 3: 提交**

```bash
git add tests/conftest.py
git commit -m "feat: 添加测试公共fixtures配置"
```

---

## Task 4: 集成测试 - ModelConfig API

**Files:**
- Create: `tests/integration/test_model_config.py`

- [ ] **Step 1: 编写ModelConfig API测试**

创建文件 `tests/integration/test_model_config.py`:

```python
"""
ModelConfig API 集成测试
"""
import pytest
from httpx import AsyncClient

from app.core.database import ModelConfig


pytestmark = pytest.mark.integration


class TestModelConfigAPI:
    """模型配置API测试"""

    async def test_create_model_config(
        self,
        client: AsyncClient,
        sample_model_config_data: dict
    ):
        """测试创建模型配置"""
        response = await client.post(
            "/api/v1/model-config",
            json=sample_model_config_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_model_config_data["name"]
        assert data["provider"] == sample_model_config_data["provider"]
        assert data["is_active"] is True
        assert "id" in data

    async def test_get_model_config(
        self,
        client: AsyncClient,
        sample_model_config_data: dict
    ):
        """测试获取模型配置"""
        # 先创建
        create_response = await client.post(
            "/api/v1/model-config",
            json=sample_model_config_data
        )
        config_id = create_response.json()["id"]

        # 再获取
        response = await client.get(f"/api/v1/model-config/{config_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == config_id
        assert data["name"] == sample_model_config_data["name"]

    async def test_get_all_model_configs(
        self,
        client: AsyncClient,
        sample_model_config_data: dict
    ):
        """测试获取所有模型配置"""
        # 创建多个配置
        for name in ["text", "image", "video"]:
            await client.post(
                "/api/v1/model-config",
                json={**sample_model_config_data, "name": name}
            )

        response = await client.get("/api/v1/model-config")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    async def test_update_model_config(
        self,
        client: AsyncClient,
        sample_model_config_data: dict
    ):
        """测试更新模型配置"""
        # 先创建
        create_response = await client.post(
            "/api/v1/model-config",
            json=sample_model_config_data
        )
        config_id = create_response.json()["id"]

        # 更新
        update_data = {"model": "gpt-4-turbo", "is_active": False}
        response = await client.put(
            f"/api/v1/model-config/{config_id}",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "gpt-4-turbo"
        assert data["is_active"] is False

    async def test_delete_model_config(
        self,
        client: AsyncClient,
        sample_model_config_data: dict
    ):
        """测试删除模型配置"""
        # 先创建
        create_response = await client.post(
            "/api/v1/model-config",
            json=sample_model_config_data
        )
        config_id = create_response.json()["id"]

        # 删除
        response = await client.delete(f"/api/v1/model-config/{config_id}")
        assert response.status_code == 200

        # 确认已删除
        get_response = await client.get(f"/api/v1/model-config/{config_id}")
        assert get_response.status_code == 404

    async def test_get_active_config_by_name(
        self,
        client: AsyncClient,
        sample_model_config_data: dict
    ):
        """测试按名称获取激活配置"""
        # 创建配置
        await client.post(
            "/api/v1/model-config",
            json=sample_model_config_data
        )

        response = await client.get("/api/v1/model-config/text/active")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "text"
        assert data["is_active"] is True
```

- [ ] **Step 2: 运行测试验证**

Run: `cd /Users/a1/projects/ai-video-generator && source venv/bin/activate && pytest tests/integration/test_model_config.py -v`

Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add tests/integration/test_model_config.py
git commit -m "test: 添加ModelConfig API集成测试"
```

---

## Task 5: 集成测试 - PromptTemplate API

**Files:**
- Create: `tests/integration/test_prompt_template.py`

- [ ] **Step 1: 编写PromptTemplate API测试**

创建文件 `tests/integration/test_prompt_template.py`:

```python
"""
PromptTemplate API 集成测试
"""
import pytest
from httpx import AsyncClient

from app.core.database import PromptTemplate


pytestmark = pytest.mark.integration


class TestPromptTemplateAPI:
    """提示词模板API测试"""

    async def test_create_prompt_template(
        self,
        client: AsyncClient,
        sample_prompt_template_data: dict
    ):
        """测试创建提示词模板"""
        response = await client.post(
            "/api/v1/prompt-templates",
            json=sample_prompt_template_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_prompt_template_data["name"]
        assert data["type"] == sample_prompt_template_data["type"]
        assert data["is_default"] is True
        assert "id" in data

    async def test_get_prompt_template(
        self,
        client: AsyncClient,
        sample_prompt_template_data: dict
    ):
        """测试获取提示词模板"""
        # 先创建
        create_response = await client.post(
            "/api/v1/prompt-templates",
            json=sample_prompt_template_data
        )
        template_id = create_response.json()["id"]

        # 再获取
        response = await client.get(f"/api/v1/prompt-templates/{template_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        assert data["name"] == sample_prompt_template_data["name"]

    async def test_get_templates_by_type(
        self,
        client: AsyncClient,
        sample_prompt_template_data: dict
    ):
        """测试按类型获取模板"""
        # 创建多个模板
        for template_type in ["script", "character", "storyboard"]:
            await client.post(
                "/api/v1/prompt-templates",
                json={**sample_prompt_template_data, "type": template_type, "name": f"{template_type}_template"}
            )

        response = await client.get("/api/v1/prompt-templates?type=script")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        for item in data:
            assert item["type"] == "script"

    async def test_update_prompt_template(
        self,
        client: AsyncClient,
        sample_prompt_template_data: dict
    ):
        """测试更新提示词模板"""
        # 先创建
        create_response = await client.post(
            "/api/v1/prompt-templates",
            json=sample_prompt_template_data
        )
        template_id = create_response.json()["id"]

        # 更新
        update_data = {"template": "新的模板内容: {topic}"}
        response = await client.put(
            f"/api/v1/prompt-templates/{template_id}",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["template"] == "新的模板内容: {topic}"

    async def test_delete_prompt_template(
        self,
        client: AsyncClient,
        sample_prompt_template_data: dict
    ):
        """测试删除提示词模板"""
        # 先创建
        create_response = await client.post(
            "/api/v1/prompt-templates",
            json=sample_prompt_template_data
        )
        template_id = create_response.json()["id"]

        # 删除
        response = await client.delete(f"/api/v1/prompt-templates/{template_id}")
        assert response.status_code == 200

        # 确认已删除
        get_response = await client.get(f"/api/v1/prompt-templates/{template_id}")
        assert get_response.status_code == 404

    async def test_get_all_templates(
        self,
        client: AsyncClient,
        sample_prompt_template_data: dict
    ):
        """测试获取所有模板"""
        # 创建多个模板
        for i in range(3):
            await client.post(
                "/api/v1/prompt-templates",
                json={**sample_prompt_template_data, "name": f"template_{i}"}
            )

        response = await client.get("/api/v1/prompt-templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
```

- [ ] **Step 2: 运行测试验证**

Run: `cd /Users/a1/projects/ai-video-generator && source venv/bin/activate && pytest tests/integration/test_prompt_template.py -v`

Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add tests/integration/test_prompt_template.py
git commit -m "test: 添加PromptTemplate API集成测试"
```

---

## Task 6: 集成测试 - Projects API

**Files:**
- Create: `tests/integration/test_projects.py`

- [ ] **Step 1: 编写Projects API测试**

创建文件 `tests/integration/test_projects.py`:

```python
"""
Projects API 集成测试
"""
import pytest
from httpx import AsyncClient

from app.core.database import Project


pytestmark = pytest.mark.integration


class TestProjectsAPI:
    """项目API测试"""

    async def test_create_project(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试创建项目"""
        response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_project_data["name"]
        assert data["type"] == sample_project_data["type"]
        assert data["status"] == "draft"
        assert "id" in data

    async def test_get_project(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试获取单个项目"""
        # 先创建
        create_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = create_response.json()["id"]

        # 再获取
        response = await client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == sample_project_data["name"]

    async def test_get_projects_list(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试获取项目列表"""
        # 创建多个项目
        for i in range(3):
            await client.post(
                "/api/v1/projects",
                json={**sample_project_data, "name": f"项目{i}"}
            )

        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    async def test_get_projects_filter_by_type(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试按类型筛选项目"""
        # 创建不同类型项目
        await client.post(
            "/api/v1/projects",
            json={**sample_project_data, "type": "drama", "name": "短剧项目"}
        )
        await client.post(
            "/api/v1/projects",
            json={**sample_project_data, "type": "video", "name": "视频项目"}
        )

        response = await client.get("/api/v1/projects?type=drama")
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["type"] == "drama"

    async def test_update_project(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试更新项目"""
        # 先创建
        create_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = create_response.json()["id"]

        # 更新
        update_data = {
            "name": "更新后的名称",
            "status": "in_progress"
        }
        response = await client.put(
            f"/api/v1/projects/{project_id}",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的名称"
        assert data["status"] == "in_progress"

    async def test_delete_project(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试删除项目"""
        # 先创建
        create_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = create_response.json()["id"]

        # 删除
        response = await client.delete(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200

        # 确认已删除
        get_response = await client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 404

    async def test_get_project_not_found(
        self,
        client: AsyncClient
    ):
        """测试获取不存在的项目"""
        response = await client.get("/api/v1/projects/99999")
        assert response.status_code == 404


class TestScriptGeneration:
    """剧本生成测试"""

    async def test_generate_script_with_mock(
        self,
        client: AsyncClient,
        sample_project_data: dict,
        mock_llm_service
    ):
        """测试剧本生成（mock LLM）"""
        # 创建项目
        create_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = create_response.json()["id"]

        # 生成剧本
        response = await client.post(
            f"/api/v1/projects/{project_id}/script/generate",
            json={"input": "测试输入", "prompt_suffix": ""}
        )
        assert response.status_code == 200
        # SSE响应检查
        assert "text/event-stream" in response.headers.get("content-type", "")
```

- [ ] **Step 2: 运行测试验证**

Run: `cd /Users/a1/projects/ai-video-generator && source venv/bin/activate && pytest tests/integration/test_projects.py -v`

Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add tests/integration/test_projects.py
git commit -m "test: 添加Projects API集成测试"
```

---

## Task 7: 集成测试 - Characters API

**Files:**
- Create: `tests/integration/test_characters.py`

- [ ] **Step 1: 编写Characters API测试**

创建文件 `tests/integration/test_characters.py`:

```python
"""
Characters API 集成测试
"""
import pytest
from httpx import AsyncClient

from app.core.database import Character, Project


pytestmark = pytest.mark.integration


class TestCharactersAPI:
    """角色API测试"""

    async def test_create_character(
        self,
        client: AsyncClient,
        sample_character_data: dict,
        sample_project_data: dict
    ):
        """测试创建角色"""
        # 先创建项目
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        # 创建角色
        response = await client.post(
            "/api/v1/characters",
            json={**sample_character_data, "project_id": project_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_character_data["name"]
        assert data["project_id"] == project_id
        assert "id" in data

    async def test_get_character(
        self,
        client: AsyncClient,
        sample_character_data: dict,
        sample_project_data: dict
    ):
        """测试获取单个角色"""
        # 创建项目和角色
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        create_response = await client.post(
            "/api/v1/characters",
            json={**sample_character_data, "project_id": project_id}
        )
        character_id = create_response.json()["id"]

        # 获取角色
        response = await client.get(f"/api/v1/characters/{character_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == character_id
        assert data["name"] == sample_character_data["name"]

    async def test_get_characters_by_project(
        self,
        client: AsyncClient,
        sample_character_data: dict,
        sample_project_data: dict
    ):
        """测试按项目获取角色列表"""
        # 创建项目
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        # 创建多个角色
        for i in range(3):
            await client.post(
                "/api/v1/characters",
                json={**sample_character_data, "name": f"角色{i}", "project_id": project_id}
            )

        response = await client.get(f"/api/v1/projects/{project_id}/characters")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    async def test_update_character(
        self,
        client: AsyncClient,
        sample_character_data: dict,
        sample_project_data: dict
    ):
        """测试更新角色"""
        # 创建项目和角色
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        create_response = await client.post(
            "/api/v1/characters",
            json={**sample_character_data, "project_id": project_id}
        )
        character_id = create_response.json()["id"]

        # 更新角色
        update_data = {"name": "更新后的角色名", "age": 30}
        response = await client.put(
            f"/api/v1/characters/{character_id}",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的角色名"
        assert data["age"] == 30

    async def test_delete_character(
        self,
        client: AsyncClient,
        sample_character_data: dict,
        sample_project_data: dict
    ):
        """测试删除角色"""
        # 创建项目和角色
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        create_response = await client.post(
            "/api/v1/characters",
            json={**sample_character_data, "project_id": project_id}
        )
        character_id = create_response.json()["id"]

        # 删除角色
        response = await client.delete(f"/api/v1/characters/{character_id}")
        assert response.status_code == 200

        # 确认已删除
        get_response = await client.get(f"/api/v1/characters/{character_id}")
        assert get_response.status_code == 404

    async def test_create_character_without_project(
        self,
        client: AsyncClient,
        sample_character_data: dict
    ):
        """测试创建无项目关联的角色"""
        response = await client.post(
            "/api/v1/characters",
            json=sample_character_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_character_data["name"]
        assert data.get("project_id") is None
```

- [ ] **Step 2: 运行测试验证**

Run: `cd /Users/a1/projects/ai-video-generator && source venv/bin/activate && pytest tests/integration/test_characters.py -v`

Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add tests/integration/test_characters.py
git commit -m "test: 添加Characters API集成测试"
```

---

## Task 8: 集成测试 - Videos API

**Files:**
- Create: `tests/integration/test_videos.py`

- [ ] **Step 1: 编写Videos API测试**

创建文件 `tests/integration/test_videos.py`:

```python
"""
Videos API 集成测试
"""
import pytest
from httpx import AsyncClient

from app.core.database import GeneratedVideo, Project, Character


pytestmark = pytest.mark.integration


class TestVideosAPI:
    """视频API测试"""

    async def test_create_video_task(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试创建视频生成任务"""
        # 创建项目
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        # 创建视频任务
        response = await client.post(
            "/api/v1/videos",
            json={
                "project_id": project_id,
                "duration": 5,
                "resolution": "1080p",
                "aspect_ratio": "16:9"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id
        assert data["status"] == "pending"
        assert "id" in data

    async def test_get_video(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试获取单个视频信息"""
        # 创建项目和视频
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        create_response = await client.post(
            "/api/v1/videos",
            json={"project_id": project_id}
        )
        video_id = create_response.json()["id"]

        # 获取视频
        response = await client.get(f"/api/v1/videos/{video_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == video_id
        assert data["status"] == "pending"

    async def test_get_videos_by_project(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试按项目获取视频列表"""
        # 创建项目
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        # 创建多个视频任务
        for i in range(3):
            await client.post(
                "/api/v1/videos",
                json={"project_id": project_id}
            )

        response = await client.get(f"/api/v1/videos?project_id={project_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    async def test_update_video_status(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试更新视频状态"""
        # 创建项目和视频
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        create_response = await client.post(
            "/api/v1/videos",
            json={"project_id": project_id}
        )
        video_id = create_response.json()["id"]

        # 更新状态
        update_data = {
            "status": "completed",
            "file_path": "/videos/test.mp4"
        }
        response = await client.put(
            f"/api/v1/videos/{video_id}",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["file_path"] == "/videos/test.mp4"

    async def test_delete_video(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试删除视频记录"""
        # 创建项目和视频
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        create_response = await client.post(
            "/api/v1/videos",
            json={"project_id": project_id}
        )
        video_id = create_response.json()["id"]

        # 删除视频
        response = await client.delete(f"/api/v1/videos/{video_id}")
        assert response.status_code == 200

        # 确认已删除
        get_response = await client.get(f"/api/v1/videos/{video_id}")
        assert get_response.status_code == 404

    async def test_get_all_videos(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试获取所有视频"""
        # 创建项目
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        # 创建多个视频
        for i in range(3):
            await client.post(
                "/api/v1/videos",
                json={"project_id": project_id}
            )

        response = await client.get("/api/v1/videos")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
```

- [ ] **Step 2: 运行测试验证**

Run: `cd /Users/a1/projects/ai-video-generator && source venv/bin/activate && pytest tests/integration/test_videos.py -v`

Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add tests/integration/test_videos.py
git commit -m "test: 添加Videos API集成测试"
```

---

## Task 9: 单元测试 - LLM Service

**Files:**
- Create: `tests/unit/services/test_llm_service.py`

- [ ] **Step 1: 编写LLM服务单元测试**

创建文件 `tests/unit/services/test_llm_service.py`:

```python
"""
LLM Service 单元测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.llm_service import get_llm_service
from app.services.base import GenerationResult


pytestmark = pytest.mark.unit


class TestLLMService:
    """LLM服务测试"""

    def test_get_llm_service_openai(self):
        """测试获取OpenAI服务"""
        service = get_llm_service(
            provider="openai",
            api_key="test-key",
            model="gpt-4"
        )
        assert service is not None

    def test_get_llm_service_anthropic(self):
        """测试获取Anthropic服务"""
        service = get_llm_service(
            provider="anthropic",
            api_key="test-key",
            model="claude-3-opus"
        )
        assert service is not None

    def test_get_llm_service_qwen(self):
        """测试获取通义千问服务"""
        service = get_llm_service(
            provider="qwen",
            api_key="test-key",
            model="qwen-plus",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        assert service is not None

    def test_get_llm_service_deepseek(self):
        """测试获取DeepSeek服务"""
        service = get_llm_service(
            provider="deepseek",
            api_key="test-key",
            model="deepseek-chat"
        )
        assert service is not None


class TestLLMServiceGenerate:
    """LLM生成测试"""

    @pytest.mark.asyncio
    async def test_openai_generate_success(self):
        """测试OpenAI生成成功"""
        with patch("app.services.llm_service.AsyncOpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"title": "测试剧本"}'
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            service = get_llm_service(
                provider="openai",
                api_key="test-key",
                model="gpt-4"
            )
            result = await service.generate(
                prompt="测试提示词",
                system_prompt="系统提示词"
            )

            assert result.success is True
            assert result.content is not None

    @pytest.mark.asyncio
    async def test_openai_generate_with_error(self):
        """测试OpenAI生成失败"""
        with patch("app.services.llm_service.AsyncOpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("API Error")
            )
            mock_openai.return_value = mock_client

            service = get_llm_service(
                provider="openai",
                api_key="test-key",
                model="gpt-4"
            )
            result = await service.generate(
                prompt="测试提示词"
            )

            assert result.success is False
            assert result.error is not None
```

- [ ] **Step 2: 运行测试验证**

Run: `cd /Users/a1/projects/ai-video-generator && source venv/bin/activate && pytest tests/unit/services/test_llm_service.py -v`

Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add tests/unit/services/test_llm_service.py
git commit -m "test: 添加LLM服务单元测试"
```

---

## Task 10: 单元测试 - Image Service

**Files:**
- Create: `tests/unit/services/test_image_service.py`

- [ ] **Step 1: 编写Image服务单元测试**

创建文件 `tests/unit/services/test_image_service.py`:

```python
"""
Image Service 单元测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.image_service import get_image_service
from app.services.base import GenerationResult


pytestmark = pytest.mark.unit


class TestImageService:
    """图像服务测试"""

    def test_get_image_service_dalle(self):
        """测试获取DALL-E服务"""
        service = get_image_service(
            provider="dalle",
            api_key="test-key"
        )
        assert service is not None

    def test_get_image_service_stability(self):
        """测试获取Stability AI服务"""
        service = get_image_service(
            provider="stability",
            api_key="test-key"
        )
        assert service is not None

    def test_get_image_service_wanx(self):
        """测试获取万相服务"""
        service = get_image_service(
            provider="wanx",
            api_key="test-key"
        )
        assert service is not None


class TestImageServiceGenerate:
    """图像生成测试"""

    @pytest.mark.asyncio
    async def test_dalle_generate_success(self):
        """测试DALL-E生成成功"""
        with patch("app.services.image_service.AsyncOpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.data = [MagicMock()]
            mock_response.data[0].url = "https://example.com/image.png"
            mock_client.images.generate = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            service = get_image_service(
                provider="dalle",
                api_key="test-key"
            )
            result = await service.generate(
                prompt="一个美丽的风景"
            )

            assert result.success is True
            assert result.data is not None

    @pytest.mark.asyncio
    async def test_image_generate_with_error(self):
        """测试图像生成失败"""
        with patch("app.services.image_service.AsyncOpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.images.generate = AsyncMock(
                side_effect=Exception("API Error")
            )
            mock_openai.return_value = mock_client

            service = get_image_service(
                provider="dalle",
                api_key="test-key"
            )
            result = await service.generate(
                prompt="测试提示词"
            )

            assert result.success is False
            assert result.error is not None
```

- [ ] **Step 2: 运行测试验证**

Run: `cd /Users/a1/projects/ai-video-generator && source venv/bin/activate && pytest tests/unit/services/test_image_service.py -v`

Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add tests/unit/services/test_image_service.py
git commit -m "test: 添加Image服务单元测试"
```

---

## Task 11: 单元测试 - Voice Service

**Files:**
- Create: `tests/unit/services/test_voice_service.py`

- [ ] **Step 1: 编写Voice服务单元测试**

创建文件 `tests/unit/services/test_voice_service.py`:

```python
"""
Voice Service 单元测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.voice_service import get_voice_service
from app.services.base import GenerationResult


pytestmark = pytest.mark.unit


class TestVoiceService:
    """语音服务测试"""

    def test_get_voice_service_openai(self):
        """测试获取OpenAI TTS服务"""
        service = get_voice_service(
            provider="openai",
            api_key="test-key"
        )
        assert service is not None

    def test_get_voice_service_elevenlabs(self):
        """测试获取ElevenLabs服务"""
        service = get_voice_service(
            provider="elevenlabs",
            api_key="test-key"
        )
        assert service is not None

    def test_get_voice_service_cosyvoice(self):
        """测试获取CosyVoice服务"""
        service = get_voice_service(
            provider="cosyvoice",
            api_key="test-key"
        )
        assert service is not None


class TestVoiceServiceSynthesize:
    """语音合成测试"""

    @pytest.mark.asyncio
    async def test_openai_synthesize_success(self):
        """测试OpenAI TTS合成成功"""
        with patch("app.services.voice_service.AsyncOpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = b"fake_audio_data"
            mock_client.audio.speech.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            service = get_voice_service(
                provider="openai",
                api_key="test-key"
            )
            result = await service.synthesize(
                text="测试文本",
                voice="alloy"
            )

            assert result.success is True
            assert result.data is not None

    @pytest.mark.asyncio
    async def test_voice_synthesize_with_error(self):
        """测试语音合成失败"""
        with patch("app.services.voice_service.AsyncOpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.audio.speech.create = AsyncMock(
                side_effect=Exception("API Error")
            )
            mock_openai.return_value = mock_client

            service = get_voice_service(
                provider="openai",
                api_key="test-key"
            )
            result = await service.synthesize(
                text="测试文本"
            )

            assert result.success is False
            assert result.error is not None
```

- [ ] **Step 2: 运行测试验证**

Run: `cd /Users/a1/projects/ai-video-generator && source venv/bin/activate && pytest tests/unit/services/test_voice_service.py -v`

Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add tests/unit/services/test_voice_service.py
git commit -m "test: 添加Voice服务单元测试"
```

---

## Task 12: CI/CD - GitHub Actions

**Files:**
- Create: `.github/workflows/test.yml`

- [ ] **Step 1: 创建GitHub Actions工作流**

创建目录和文件 `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: pytest tests/ -v --cov=src/backend --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml
          fail_ci_if_error: false
```

- [ ] **Step 2: 提交**

```bash
git add .github/workflows/test.yml
git commit -m "ci: 添加GitHub Actions测试工作流"
```

---

## Task 13: Makefile更新

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: 更新Makefile测试命令**

在 `Makefile` 中找到 `test:` 目标，替换为:

```makefile
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src/backend --cov-report=html

test-unit:
	pytest tests/unit/ -v -m unit

test-integration:
	pytest tests/integration/ -v -m integration
```

- [ ] **Step 2: 验证Makefile**

Run: `cd /Users/a1/projects/ai-video-generator && make help`

Expected: 显示新的测试命令

- [ ] **Step 3: 提交**

```bash
git add Makefile
git commit -m "chore: 更新Makefile测试命令"
```

---

## Task 14: 运行全量测试

**Files:**
- None

- [ ] **Step 1: 运行所有测试**

Run: `cd /Users/a1/projects/ai-video-generator && source venv/bin/activate && pytest tests/ -v --cov=src/backend --cov-report=term-missing`

Expected: 所有测试通过，显示覆盖率报告

- [ ] **Step 2: 最终提交**

```bash
git push origin main
```

---

## 文件清单

### 新增文件 (16个)

| 文件路径 | 描述 |
|----------|------|
| `pytest.ini` | pytest配置 |
| `tests/__init__.py` | 测试包初始化 |
| `tests/conftest.py` | 公共fixtures |
| `tests/unit/__init__.py` | 单元测试包 |
| `tests/unit/services/__init__.py` | 服务测试包 |
| `tests/unit/services/test_llm_service.py` | LLM服务测试 |
| `tests/unit/services/test_image_service.py` | 图像服务测试 |
| `tests/unit/services/test_voice_service.py` | 语音服务测试 |
| `tests/integration/__init__.py` | 集成测试包 |
| `tests/integration/test_projects.py` | 项目API测试 |
| `tests/integration/test_characters.py` | 角色API测试 |
| `tests/integration/test_model_config.py` | 模型配置API测试 |
| `tests/integration/test_prompt_template.py` | 提示词模板API测试 |
| `tests/integration/test_videos.py` | 视频API测试 |
| `tests/e2e/__init__.py` | E2E测试包 |
| `.github/workflows/test.yml` | GitHub Actions工作流 |

### 修改文件 (2个)

| 文件路径 | 修改内容 |
|----------|----------|
| `requirements.txt` | 添加pytest-cov依赖 |
| `Makefile` | 添加测试命令 |
