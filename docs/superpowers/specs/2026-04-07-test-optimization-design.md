# AI Video Generator 测试优化设计

## 概述

为 ai-video-generator 项目建立完整的测试体系，包括分层测试架构、Mock服务、CI/CD流水线。

## 设计决策

| 决策项 | 选择 |
|--------|------|
| 测试层面 | 全栈集成测试 |
| 测试范围 | 所有API端点 |
| 外部API | Mock处理 |
| CI/CD | 配置GitHub Actions |
| 架构风格 | 分层测试架构 |

## 测试架构

```
tests/
├── conftest.py           # 公共fixtures和配置
├── __init__.py
├── unit/                  # 单元测试（服务层mock）
│   ├── __init__.py
│   └── services/
│       ├── __init__.py
│       ├── test_llm_service.py
│       ├── test_image_service.py
│       └── test_voice_service.py
├── integration/           # 集成测试（API + DB）
│   ├── __init__.py
│   ├── test_projects.py
│   ├── test_characters.py
│   ├── test_model_config.py
│   ├── test_prompt_template.py
│   └── test_videos.py
└── e2e/                   # 端到端测试（预留）
    └── __init__.py
```

## 测试基础设施

### pytest 配置

文件: `pytest.ini`

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

### 公共 Fixtures

文件: `tests/conftest.py`

| Fixture名称 | 用途 |
|-------------|------|
| `test_app` | FastAPI TestClient实例 |
| `test_db` | 内存SQLite数据库会话 |
| `mock_llm_service` | Mock LLM服务 |
| `mock_image_service` | Mock图像生成服务 |
| `mock_voice_service` | Mock语音合成服务 |
| `sample_project` | 测试项目数据 |
| `sample_character` | 测试角色数据 |
| `sample_model_config` | 测试模型配置数据 |

### 测试数据库配置

使用内存SQLite进行测试隔离：

```python
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
```

## API集成测试用例

### test_projects.py

| 测试方法 | 描述 |
|----------|------|
| `test_create_project` | 创建项目 |
| `test_get_project` | 获取单个项目 |
| `test_get_projects_list` | 获取项目列表 |
| `test_update_project` | 更新项目 |
| `test_delete_project` | 删除项目 |
| `test_generate_script` | 剧本生成流程（mock LLM） |
| `test_generate_script_without_model_config` | 未配置模型时的降级处理 |

### test_characters.py

| 测试方法 | 描述 |
|----------|------|
| `test_create_character` | 创建角色 |
| `test_get_character` | 获取单个角色 |
| `test_get_characters_by_project` | 按项目获取角色列表 |
| `test_update_character` | 更新角色 |
| `test_delete_character` | 删除角色 |
| `test_generate_character_image` | 角色形象生成（mock图像服务） |

### test_model_config.py

| 测试方法 | 描述 |
|----------|------|
| `test_create_model_config` | 创建模型配置 |
| `test_get_model_config` | 获取模型配置 |
| `test_update_model_config` | 更新模型配置 |
| `test_delete_model_config` | 删除模型配置 |
| `test_get_active_config_by_name` | 按名称获取激活配置 |
| `test_model_config_validation` | 配置验证 |

### test_prompt_template.py

| 测试方法 | 描述 |
|----------|------|
| `test_create_prompt_template` | 创建提示词模板 |
| `test_get_prompt_template` | 获取提示词模板 |
| `test_update_prompt_template` | 更新提示词模板 |
| `test_delete_prompt_template` | 删除提示词模板 |
| `test_get_templates_by_type` | 按类型获取模板 |
| `test_template_variable_replacement` | 模板变量替换 |

### test_videos.py

| 测试方法 | 描述 |
|----------|------|
| `test_create_video_task` | 创建视频生成任务 |
| `test_get_video` | 获取视频信息 |
| `test_get_videos_by_project` | 按项目获取视频列表 |
| `test_update_video_status` | 更新视频状态 |
| `test_delete_video` | 删除视频记录 |

## Mock服务设计

### LLM服务Mock

```python
@pytest.fixture
def mock_llm_service():
    """Mock LLM服务，返回预设的剧本内容"""
    with patch("app.services.llm_service.get_llm_service") as mock:
        mock.return_value.generate = AsyncMock(return_value=GenerationResult(
            success=True,
            data={
                "title": "测试剧本",
                "logline": "一个关于测试的故事",
                "scenes": []
            }
        ))
        yield mock
```

### 图像服务Mock

```python
@pytest.fixture
def mock_image_service():
    """Mock图像生成服务"""
    with patch("app.services.image_service.get_image_service") as mock:
        mock.return_value.generate = AsyncMock(return_value=GenerationResult(
            success=True,
            data="https://example.com/mock-image.png"
        ))
        yield mock
```

### 语音服务Mock

```python
@pytest.fixture
def mock_voice_service():
    """Mock语音合成服务"""
    with patch("app.services.voice_service.get_voice_service") as mock:
        mock.return_value.synthesize = AsyncMock(return_value=GenerationResult(
            success=True,
            data="https://example.com/mock-audio.mp3"
        ))
        yield mock
```

## CI/CD配置

### GitHub Actions工作流

文件: `.github/workflows/test.yml`

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
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov httpx

      - name: Run tests
        run: pytest --cov=src/backend --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml
```

### Makefile更新

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

## 文件清单

### 新增文件

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
| `tests/e2e/__init__.py` | E2E测试包（预留） |
| `.github/workflows/test.yml` | GitHub Actions工作流 |

### 修改文件

| 文件路径 | 修改内容 |
|----------|----------|
| `requirements.txt` | 添加pytest-cov依赖 |
| `Makefile` | 添加测试命令 |

## 预期成果

1. 完整的API集成测试覆盖
2. Mock外部服务，测试快速稳定
3. CI/CD自动化测试流水线
4. 测试覆盖率报告
5. 清晰的测试文档和最佳实践
