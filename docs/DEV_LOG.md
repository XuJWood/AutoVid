# AutoVid 项目开发日志

> 初始化日期：2026-04-28
> 环境：conda env `lg_1.0` (Python 3.11)
> 工作目录：`/mnt/ddata2/cc009/aidt/langraph/tool_nodes/tools/web_search`

---

## 一、项目概述

AutoVid 是一站式 AI 漫剧（Anime Short Drama）创作平台。从文字输入到成品视频全链路自动化：AI 生成剧本 → 创建动漫角色 → 生成角色三视图 → 生成剧集封面 → 文生视频 → TTS 配音 → 最终成品。

核心定位：面向 AI 视频创作者/供应商，支持抖音/快手/B站等短视频平台的快节奏日系动漫短剧生产（每集约 15-20 秒）。

### 技术栈

| 层 | 技术 |
|---|------|
| 后端框架 | FastAPI (Python 3.11) |
| 前端框架 | Vue 3 + Vite + TailwindCSS |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |
| 文本模型 | 通义千问 qwen-plus (DashScope) |
| 图像模型 | 万相 wanx2.1-t2i-turbo |
| 视频模型 | 万相 wanx2.1-t2v-turbo / wan2.7-i2v |
| 语音模型 | Qwen TTS (qwen3-tts-flash / cosyvoice) |
| 音频处理 | FFmpeg |
| 异步任务 | Celery + Redis |

---

## 二、目录结构

```
web_search/
├── .env                        # 环境变量（含 DashScope API Key）
├── .env.example                # 环境变量模板
├── requirements.txt            # Python 依赖
├── Makefile                    # 常用命令
├── docker-compose.yml          # Docker 编排
├── Dockerfile.backend          # 后端 Dockerfile
├── Dockerfile.frontend         # 前端 Dockerfile
├── pytest.ini                  # Pytest 配置
├── test_script.py              # 独立测试脚本
│
├── src/
│   ├── backend/app/
│   │   ├── main.py             # FastAPI 入口，lifespan 事件建表
│   │   ├── core/
│   │   │   ├── config.py       # pydantic-settings 配置（读 .env）
│   │   │   └── database.py     # SQLAlchemy async 引擎 + 7 个 ORM 模型
│   │   ├── api/v1/
│   │   │   ├── __init__.py     # 路由汇总（7 个模块）
│   │   │   └── endpoints/
│   │   │       ├── projects.py          # 项目管理 CRUD + SSE 流式剧本生成
│   │   │       ├── characters.py        # 角色管理 + 三视图生成
│   │   │       ├── storyboard.py        # 剧集封面/视频生成 + 配音合成
│   │   │       ├── pipeline.py          # 一键全链路生成（SSE 推送进度）
│   │   │       ├── model_config.py      # 模型配置 CRUD + 连接测试
│   │   │       ├── prompt_template.py   # 提示词模板管理
│   │   │       └── videos.py            # 视频查询/下载
│   │   └── services/
│   │       ├── base.py                 # BaseAIService 抽象基类 + GenerationResult
│   │       ├── alibaba_cloud.py        # DashScope SDK 封装（Qwen/Wanx/CosyVoice）
│   │       ├── llm_service.py          # LLM 工厂（OpenAI/Claude/DeepSeek/Qwen）
│   │       ├── image_service.py        # 图像生成服务工厂
│   │       ├── video_service.py        # 视频生成服务工厂
│   │       ├── voice_service.py        # 语音合成服务工厂
│   │       ├── video_audio_service.py  # TTS + FFmpeg 配音合成
│   │       ├── pipeline.py             # VideoPipeline: 6 阶段流水线
│   │       ├── media_storage.py        # 文件存储（角色/剧集/音频目录管理）
│   │       ├── character_consistency.py# 角色一致性服务
│   │       ├── prompts.py              # 提示词模板（剧本/角色/分镜）
│   │       ├── generator.py            # 通用生成器
│   │       ├── cache_service.py        # 缓存服务
│   │       ├── resilience.py           # 重试装饰器
│   │       └── multimodal_service.py   # 多模态服务
│   ├── frontend/               # Vue 3 前端（待探索）
│   └── ai/                     # AI 模块（空壳 __init__.py）
│
├── tests/
│   ├── conftest.py             # 全局 fixtures（test DB, mock services）
│   ├── unit/services/          # 单元测试（3 个文件，mock 所有外部调用）
│   └── integration/            # 集成测试（7 个文件，含 pipeline 端到端）
│
├── docs/
│   ├── product_spec.md         # 产品需求文档（PRD v2.1）
│   ├── research_report.md      # 调研报告
│   ├── ui_design.md            # UI 设计文档
│   └── ui-screens/             # HTML 原型页面（6 个页面 + README）
│
└── media/                      # 生成内容存储（不入 git）
    └── projects/{id}/
        ├── characters/{name}/  # front.png, side.png, back.png
        ├── episodes/ep{XX}/    # cover.png, final_with_audio.mp4
        └── audio/              # 临时音频
```

---

## 三、数据库模型 (7 个表)

| 模型 | 表名 | 用途 |
|------|------|------|
| **Project** | projects | 项目主表（名称/类型/状态/剧本 JSON/模型配置） |
| **Character** | characters | 角色（名称/外观/服装/性别/选中图片/三视图/配音配置） |
| **Storyboard** | storyboards | 剧集（每行=1集，标题/对话JSON/封面/视频/音频/状态） |
| **ModelConfig** | model_configs | 模型配置（文本/图像/视频/语音四类，含 API Key/base_url） |
| **PromptTemplate** | prompt_templates | 提示词模板（剧本/角色/分镜/视频，含变量定义） |
| **GeneratedVideo** | generated_videos | 生成的视频记录（路径/缩略图/参数/状态） |
| ─ | ─ | SQLite 开发 / PostgreSQL 生产 |

---

## 四、API 路由一览 (v1)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/projects` | 项目列表 |
| POST | `/api/v1/projects` | 创建项目 |
| POST | `/api/v1/projects/{id}/generate-script` | SSE 流式生成剧本 |
| GET/POST/PUT/DELETE | `/api/v1/characters` | 角色 CRUD |
| POST | `/api/v1/characters/{id}/generate-three-views` | 生成角色三视图 |
| GET/POST/PUT/DELETE | `/api/v1/storyboard/` | 剧集 CRUD |
| POST | `/api/v1/storyboard/{id}/generate-image` | 生成剧集封面 |
| POST | `/api/v1/storyboard/{id}/generate-video` | 生成剧集视频 + 配音 |
| POST | `/api/v1/pipeline/start` | 一键全链路生成（SSE） |
| GET | `/api/v1/pipeline/status/{project_id}` | 流水线进度查询 |
| GET/POST/PUT/DELETE | `/api/v1/model-config/` | 模型配置 CRUD |
| GET/POST/PUT/DELETE | `/api/v1/prompt-templates/` | 提示词模板 CRUD |
| GET/POST/DELETE | `/api/v1/videos/` | 视频记录 CRUD |
| GET | `/health` | 健康检查 |

---

## 五、核心流水线 (VideoPipeline)

一键生成流程分为 6 个阶段，通过 SSE 推送实时进度：

```
Stage 1: SCRIPT     → AI 生成剧本 + 角色设定（通义千问）
Stage 2: CHARACTERS → 生成角色形象图（万相 wanx2.1-turbo）
Stage 3: EPISODES   → 拆分为剧集，存入 Storyboard 表
Stage 4: IMAGES     → 逐集生成剧集封面（动漫风格，含角色一致性 prompt）
Stage 5: VIDEOS     → 逐集文生视频（可选：图+音频驱动口型同步）
Stage 6: AUDIO      → 补充配音旁白（TTS → FFmpeg 合成）
```

关键设计点：
- **角色一致性**：每个角色的 appearance/clothing/gender 融入视频 prompt
- **口型同步**：i2v 模型接受 image_url + driving_audio_url，生成带口型的视频
- **异步轮询**：DashScope 图像/视频生成是异步的，服务层循环 poll 任务状态（最长等 120s/600s）
- **重试机制**：`@retry(max_attempts=3, base_delay=2.0)` 装饰器

---

## 六、AI 服务层架构

```
BaseAIService (抽象基类)
├── QwenService       → 通义千问文本（OpenAI 兼容接口）
├── WanxImageService  → 万相图像（DashScope REST API）
├── WanxVideoService  → 万相视频（t2v/i2v）
├── CosyVoiceService  → Qwen TTS 语音合成
├── OpenAIService     → OpenAI GPT
├── ClaudeService     → Anthropic Claude
└── DeepSeekService   → DeepSeek (OpenAI 兼容)
```

工厂函数 `get_llm_service(provider, api_key, ...)` 根据 provider 参数路由到对应实现。`qwen/tongyi/alibaba/aliyun` 均映射到阿里云百炼。

---

## 七、环境配置

### 已配置的环境变量 (`.env`)

- `DASHSCOPE_API_KEY` — 阿里云百炼 API Key
- `DASHSCOPE_BASE_URL` — `https://dashscope.aliyuncs.com/compatible-mode/v1`
- `DATABASE_URL` — SQLite 本地开发
- 其余配置见 `.env.example`

### API Key 使用方式

API Key 可以两种方式传入：
1. 环境变量 `DASHSCOPE_API_KEY`（作为默认值）
2. 前端 UI 配置 → 存入 `model_configs` 表 → Pipeline 从 DB 读取

当前 `config.py` 已新增 `DASHSCOPE_API_KEY` 和 `DASHSCOPE_BASE_URL` 字段。

---

## 八、测试体系

- **测试框架**: Pytest + pytest-asyncio + pytest-cov
- **测试数据库**: SQLite in-memory (`sqlite+aiosqlite:///:memory:`)
- **Mock 策略**: 所有外部 AI 服务调用均通过 `unittest.mock` patch

```
tests/
├── unit/services/              # 3 个单元测试（LLM/图像/语音服务）
├── integration/                # 7 个集成测试
│   ├── test_projects.py        # 项目 CRUD + 剧本生成
│   ├── test_characters.py      # 角色 CRUD + 三视图生成
│   ├── test_storyboard.py      # 剧集 + 封面 + 视频/音频生成
│   ├── test_pipeline.py        # 端到端全链路
│   ├── test_model_config.py    # 模型配置 CRUD
│   ├── test_prompt_template.py # 提示词模板 CRUD
│   └── test_videos.py          # 视频记录
└── e2e/                        # 端到端测试（待补充）
```

运行命令：`pytest tests/ -v` 或 `make test`

---

## 九、启动方式

```bash
# 1. 激活环境
conda activate lg_1.0

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动后端
cd src/backend
PYTHONPATH=src/backend python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 4. 启动前端（另一个终端）
cd src/frontend
npm install && npm run dev
```

访问：
- 前端: `http://localhost:5173`
- API 文档: `http://localhost:8000/docs`

---

## 十、待办 / 已知问题

- [ ] 前端实际代码待确认（`src/frontend/` 下是否有完整 Vue 项目）
- [ ] ModelConfig 连接测试接口 (`/test`) 目前是 Mock，待实现真正的 provider 连通性检查
- [ ] DashScope API Key 在 `model_configs` 表中的 seed 数据待补充
- [ ] Celery 任务队列在本地开发中简化（当前仅 SQLite，无 Redis）
- [ ] 部分服务文件的 `__init__.py` 仅空壳，需要确认是否存在
- [ ] 视频生成部分的口型同步功能需要确保 TTS 音频 URL 能被 DashScope 访问（非 localhost）

---

## 十一、2026-04-28 更新日志

### 11.1 剧本生成 — 集数档位 + 提示词重写

**文件**: `src/backend/app/services/prompts.py`

- 新增 `_episode_tier_config(tier)` 函数，返回 short/medium/long 三档配置：
  - 短篇 (short): 8-20集，快节奏，每3集大转折，至少5个反转
  - 中篇 (medium): 20-50集，有支线，每5-8集大转折，至少8个反转
  - 长篇 (long): 80-120集，多线叙事，四幕结构，至少15个反转
- `SCRIPT_SYSTEM_PROMPT` 升级到 v5.0，新增"集数规划"章节
- `SCRIPT_USER_PROMPT` 新增 `{episode_requirements}` 和 `{twist_requirement}` 占位符
- 硬性要求加强：角色 appearance/clothing 80字以上，environment 60字以上
- `get_script_prompt()` 新增 `episode_tier` 参数

**文件**: `src/backend/app/api/v1/endpoints/projects.py`
- `ScriptGenerateRequest` 新增 `episode_tier: str = "short"` 字段
- SSE 剧本生成接口传递 `episode_tier` 到 prompt 构建

**文件**: `src/backend/app/services/pipeline.py`
- `run_script_generation()` 传递 `episode_tier` 参数

### 11.2 分镜提示词 — 场景环境细节增强

**文件**: `src/backend/app/services/prompts.py`

- `STORYBOARD_SYSTEM_PROMPT` 升级到 v4.0，新增"场景描述黄金公式"
- `STORYBOARD_USER_PROMPT` 重构：
  - 新增 `environment_detail` JSON 结构（location/architecture/lighting/atmosphere/color_palette）
  - 新增 `key_frames` 三段式时间轴（0-5s / 5-12s / 12-20s）
  - 视频提示词公式：日系动漫风 + 角色外观 + 动作 + 场景氛围 + 光线色调 + 流畅动画 + 高画质

### 11.3 TTS 语音引擎 — 性别匹配修复 + 智能音色选择

**文件**: `src/backend/app/services/video_audio_service.py`（重大重写）

- **性别识别修复**: 新增 `_normalize_gender()` 函数，同时支持中文（男/女/男性/女性）和英文（male/female），修复此前所有男角色被分配女声的 bug
- **音色库扩展**: `VOICE_PROFILES` 从 9 个扩展到 16 个，每个音色包含性别、年龄范围、性格关键词、音色描述
  - 女声 8 个: Cherry(芊悦), Jennifer(詹妮弗), Katerina(卡捷琳娜), Nofish(不吃鱼), Chelsie, Serena, Jada, Sunny
  - 男声 8 个: Ethan(晨煦), Ryan(甜茶), Elias(墨讲师), Dylan, Marcus, Roy, Peter, Rocky
- **智能匹配**: 新增 `_match_voice_by_personality()` — 根据角色性格关键词与音色 profile 打分匹配
- `get_voice_for_character()` 重写匹配逻辑：性格优先 → 年龄回退 → 性别默认
- 音频质量: 采样率 22050→48000，格式 wav→mp3
- 新增 `generate_dialogue_audio_data()` — 返回 DashScope OSS URL（可直接作为 wan2.7-i2v 的 driving_audio）

### 11.4 Storyboard 状态模型扩展

**文件**: `src/backend/app/core/database.py`

- Storyboard 模型新增三个独立状态字段，支持 i2v 管线的三阶段独立追踪：
  - `image_status`: 封面图生成状态（pending/processing/completed/failed）
  - `audio_status`: 配音生成状态
  - `video_status`: 视频生成状态
- 保留原有 `status` 字段向后兼容
- 已执行 SQLite ALTER TABLE 迁移

### 11.5 视频生成修复 — first_frame URL 问题

**文件**: `src/backend/app/api/v1/endpoints/storyboard.py`

- **问题**: `first_frame` 传入本地文件路径 `/mnt/ddata2/.../cover.png`，DashScope 无法访问 → `DataInspection` 错误
- **修复**: `generate_storyboard_image` 现在存储 DashScope OSS URL（而非本地路径）到 `image_url`
- 新增 `_to_http_url()` 辅助函数 — 将本地路径转换为完整 HTTP URL（兼容历史数据）
- `generate_storyboard_video` 接受 `audio_url` 参数（预生成的 TTS 音频）
- 三个生成端点（image/audio/video）各自使用独立的状态字段

### 11.6 图像服务 None model 修复

**文件**: `src/backend/app/services/image_service.py`

- **问题**: `kwargs.pop("model", "wanx2.1-turbo")` 在 key 存在但值为 None 时返回 None → `AttributeError: 'NoneType' object has no attribute 'lower'`
- **修复**: `kwargs.pop("model", None) or "wanx2.1-turbo"`

### 11.7 前端 — 模型配置页修复

**文件**: `src/frontend/src/views/settings/ModelConfig.vue`

- 视频 Provider 下拉补全"万相 (阿里云百炼)"选项
- 视频模型下拉新增: wan2.7-i2v / wan2.7-t2v / wanx2.1-t2v-turbo
- 图像模型下拉新增: wanx2.1-t2i-turbo / wanx2.1-t2i-plus
- 所有默认值改为阿里云百炼: wanx / qwen / cosyvoice + 对应模型

### 11.8 前端 — 剧集编辑页重构

**文件**: `src/frontend/src/views/drama/StoryboardEdit.vue`

- 按钮顺序修正为 i2v 正确流程: ① 生成封面 → ② 配音 → ③ 生成视频
- 解除音频按钮对视频 URL 的依赖（音频独立生成）
- 三阶段状态徽章: image_status / audio_status / video_status
- 新增 HTML5 `<audio>` 元素预览配音
- "一键生成全部"按封面→音频→视频顺序串行执行
- `generateVideo()` 传递 `audio_url` 参数

### 11.9 前端 — 集数档位选择器

**文件**: `src/frontend/src/views/drama/ProjectCreate.vue`
- 新增"集数规模"下拉框: 短篇(8-20集) / 中篇(20-50集) / 长篇(80-120集)
- form reactive 新增 `episode_tier: 'short'`

**文件**: `src/frontend/src/views/drama/ScriptWorkspace.vue`
- 控制栏新增集数档位选择器（短篇≤20 / 中篇20-50 / 长篇~100）
- `generateScript()` SSE 请求传递 `episode_tier` 参数

### 11.10 前端 — 对话侧边栏

**文件**: `src/frontend/src/views/drama/ScriptWorkspace.vue`

- 页面布局从 2 列改为 3 列: 角色(2) | 剧本(7) | 对话面板(3)
- 对话面板按剧集分组展示所有台词，包含角色名、情绪标签、台词内容
- 新增 `totalDialogueCount` computed 统计台词总数
- 空状态提示"生成剧本后将在此显示所有剧集对话"
