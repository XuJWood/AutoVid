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

---

## 十二、2026-04-29 更新日志 — 架构升级：Episode→Segment→Video + Seedance视频模型

### 12.1 数据库模型重构 — 新增 Segment 表

**文件**: `src/backend/app/core/database.py`

- 新增 **Segment** 模型（`segments` 表），实现 Episode→Segment→Video 三级结构：
  - `storyboard_id` / `project_id` — 关联剧集和项目
  - `segment_number` — 剧集内片段序号（1-4）
  - `visual_description` — 视觉描述（AI 视频生成的核心文本输入）
  - `camera_movement` — 镜头运动（推/拉/摇/移/跟/固定/急摇）
  - `dialogue` — 台词（内联格式，不再单独列出）
  - `character_ids` / `character_image_refs` — 出场角色 ID 和参考图 URL
  - `image_url` / `video_url` — 片段封面和视频（视频包含音频）
  - `model_provider` / `generation_params` — 记录使用的模型和参数
  - 独立状态追踪：`status` / `image_status` / `video_status`
- Storyboard 模型更新：`duration` 默认值 20→60s，`video_url`/`audio_url` 标记为 deprecated（由 segments 管理）

### 12.2 新增 Seedance 2.0 视频服务（火山引擎）

**文件**: `src/backend/app/services/seedance_video.py`（新建）

- 实现 `SeedanceVideoService` 类，封装火山引擎 Ark API：
  - 端点: `POST https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks`
  - 模型: `doubao-seedance-2-0-260128`
  - 核心特性：文本 + 参考图 → 视频（含嵌入式音频），无需单独 TTS
  - 参数: `text` (prompt), `image_url` (角色参考图), `ratio`, `duration`, `generate_audio: true`
  - 异步任务模式：创建任务 → 轮询状态 → 下载视频到 `episodes/ep{XX}/seg{YY}/video.mp4`
  - 最长等待 600s，每 5s 轮询一次

**文件**: `src/backend/app/services/video_service.py`

- 工厂函数 `get_video_service()` 新增 provider 路由：
  - `seedance` / `volcano` / `volcengine` / `ark` → `SeedanceVideoService`

### 12.3 剧本提示词重写 — 60秒剧集 + 4段式结构

**文件**: `src/backend/app/services/prompts.py`

- **SCRIPT_SYSTEM_PROMPT** v5.1:
  - 核心法则从"20秒完整叙事"升级为"60秒完整叙事"
  - 新增"段式结构"法则：每集 4 个 Segment，每段 15 秒 = 1 个独立视频
  - 剧集结构: 开场(10s)→发展(15s)→高潮(20s)→收尾(15s)
- **SCRIPT_USER_PROMPT** 输出格式重构：
  - 移除旧 `shots` 数组（镜头列表）
  - 新增 `segments` 数组：
    ```json
    {
      "segment_number": 1,
      "visual_description": "...(80字以上)",
      "camera_movement": "推/拉/摇/移/跟/固定",
      "dialogue": "角色名：台词内容",
      "emotion": "情绪关键词",
      "duration": 15
    }
    ```
  - 每集严格 4 个 segments，第 4 段结尾必须有钩子/悬念
- **STORYBOARD_SYSTEM_PROMPT** v5.0: 新增分段视频生成要点
- **STORYBOARD_USER_PROMPT**: 输出格式更新为 segments 数组，新增角色参考图使用说明
- 新增 `SEGMENT_VIDEO_PROMPT_TEMPLATE` — 片段视频提示词模板

### 12.4 角色三视图重构 — 单张组合设计图 + 表情特写

**文件**: `src/backend/app/services/character_consistency.py`

- `generate_three_views()` 完全重写：
  - **旧**: 生成 3 张独立图片（front/side/back.png）
  - **新**: 生成 1 张组合角色设计表（character design sheet），包含：
    - 三视图：正面全身 / 45度侧面 / 背面
    - 4 种表情特写：开心的笑 / 愤怒的吼 / 惊讶 / 悲伤的哭
    - 全部排列在一张干净的白色背景角色参考图上
  - 新增 `custom_prompt` 参数：传入自定义提示词时跳过自动生成
  - 存储为 `design_sheet.png`，同时保留 `reference.png` 副本向后兼容
  - 返回 `expressions` 和 `views` 元信息

**文件**: `src/backend/app/api/v1/endpoints/characters.py`

- 新增 `GET /{character_id}/preview-three-views-prompt` — 预览提示词（不生成图片），供用户编辑
- `GenerateThreeViewsRequest` 新增 `custom_prompt` 字段 — 支持完全自定义提示词
- `GenerateThreeViewsRequest.style` 默认值改为 `anime`

### 12.5 剧集 API 重构 — Segment 级别端点

**文件**: `src/backend/app/api/v1/endpoints/storyboard.py`（重大重写）

- **`GET /project/{id}`**: 返回结构新增 `segments` 数组，每个 episode 下挂载其 segments
- **`POST /project/{id}/generate`**: 从剧本的 `segments` 数据创建 Segment 记录，自动映射角色名称到 ID，构建角色参考图映射
- **新增 `POST /segment/{id}/generate-video`**: 为单个片段生成视频（使用 Seedance，视频+音频一体化）
- **新增 `POST /{id}/generate-all-segments`**: 批量生成该集所有片段视频
- **新增 `DELETE /segment/{id}`**: 删除单个片段
- `DELETE /{id}` 更新为同时删除剧集和所有关联片段
- 旧 `generate-video` 端点保留，检测到有 segments 时自动重定向到 `generate-all-segments`
- 移除独立音频生成流程（Seedance 已包含音频）
- 向后兼容：旧格式 `scenes` 自动转换为 episodes + segments

### 12.6 前端 — API 客户端更新

**文件**: `src/frontend/src/api/storyboard.js`

- 新增 `generateSegmentVideo(segmentId, options)` — 单个片段视频生成
- 新增 `generateAllSegments(storyboardId, options)` — 批量片段视频生成
- 新增 `deleteSegment(segmentId)` — 删除片段
- `generateAudio` / `generateVideo` 标记为 DEPRECATED

**文件**: `src/frontend/src/api/characters.js`

- 新增 `previewThreeViewsPrompt(characterId, params)` — 预览三视图提示词

### 12.7 前端 — 剧集编辑页重构（Segment 级别管理）

**文件**: `src/frontend/src/views/drama/StoryboardEdit.vue`（完全重写）

- 移除三阶段流水线（封面→配音→视频），替换为两阶段：封面 + 片段视频
- 每个剧集卡片内展开显示其 segments：
  - 片段编号、镜头运动、时长、视频状态徽章
  - 视觉描述和台词预览
  - 内嵌视频播放器（completed 时）
  - 独立"生成视频 (Seedance)"按钮
- "一键生成全部片段视频"：所有片段串行生成
- 统计栏更新："封面 X/Y" + "片段视频 X/Y"
- 移除 `audio_status` 追踪

### 12.8 前端 — 视频预览页重构（Segment 级别播放）

**文件**: `src/frontend/src/views/drama/VideoPreview.vue`（完全重写）

- 剧集→片段两级导航：右侧面板按剧集分组显示所有片段
- 播放器区域：
  - 封面优先设计：显示剧集封面图 + 集号/段号标签
  - 点击封面开始播放当前片段视频
  - 上一个/下一个切换跨片段连续播放
  - "连续播放"模式：片段播放完毕后自动跳到下一段
- 统计信息：集数、已生成片段/总片段数、总时长

### 12.9 前端 — 剧本工作区更新

**文件**: `src/frontend/src/views/drama/ScriptWorkspace.vue`

- 剧集展示从"镜头列表"（shots）切换为"片段列表"（segments）
- 每个片段显示：段号、镜头运动图标、visual_description、dialogue
- 旧格式 `shots` 保留兼容显示（标注"旧格式"）
- 剧集时长显示从 20s 更新为 60s

### 12.10 前端 — 角色弹窗升级

**文件**: `src/frontend/src/components/CharacterModal.vue`

- 新增"提示词预览 & 编辑"区域：
  - 自动加载 AI 生成的提示词（调用 `preview-three-views-prompt` API）
  - 可编辑的 textarea，支持完全自定义
  - "刷新提示词"按钮重新获取
- 三视图展示更新：
  - 优先显示组合设计图（`design_sheet`）
  - 旧格式（front/side/back 分离）作为回退显示
  - 表情信息展示（expressions 列表）
- "生成设计图（三视图+表情）"按钮传递 `custom_prompt` 参数
- 角色切换时自动刷新提示词

### 12.11 媒体存储目录结构更新

**文件**: `src/backend/app/services/media_storage.py`

- 新增 segment 级别目录: `media/projects/{id}/episodes/ep{XX}/seg{YY}/video.mp4`
- `SeedanceVideoService.generate()` 自动创建 `seg{YY}` 子目录

### 12.12 API 路由新增

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/characters/{id}/preview-three-views-prompt` | 预览三视图提示词 |
| POST | `/api/v1/storyboard/segment/{id}/generate-video` | 生成片段视频 (Seedance) |
| POST | `/api/v1/storyboard/{id}/generate-all-segments` | 批量生成全部片段视频 |
| DELETE | `/api/v1/storyboard/segment/{id}` | 删除片段 |

### 12.13 Seedance API Schema 修复（关键 Bug）

**问题**: 所有 segment video 生成失败，错误 `Field required: input.media`。每次约 5 秒后被服务端拒绝。

**根因**: 第一版 `seedance_video.py` 把 Ark API schema 写错了：
- 错误格式：`{"input": {"text": "...", "image_url": "...", "ratio": "...", "duration": ...}}` （照搬 DashScope 格式）
- 正确格式：`{"content": [{"type": "text", "text": "..."}, {"type": "image_url", "image_url": {"url": "..."}}]}` （Ark v3 用 typed-content array）

**调研结果**（火山引擎 Ark v3 API 真实协议）:
- 端点 `POST /api/v3/contents/generations/tasks` 使用 `content` 数组，每项有 `type` 字段
- 视频参数（resolution/duration/ratio/watermark）以 **inline flag** 形式追加在 text 内容尾部：`<prompt> --resolution 1080p --duration 15 --ratio 16:9 --watermark false`
- 任务 id 字段是 `id`（不是 `task_id`），状态值 `queued/running/succeeded/failed/expired/cancelled`
- 支持 duration 4-15 秒，resolution 480p/720p/1080p（Pro 支持 2K），ratio 1:1/3:4/4:3/16:9/9:16/21:9
- `generate_audio` 是 Seedance 2.0 顶层字段（默认开启），不是 input 子字段

**修复**:

**文件**: `src/backend/app/services/seedance_video.py`（重写）

- 改用 `content` 数组 schema，参数以 inline flags 追加
- 默认 resolution = 1080p（之前漏传），duration = 15s
- 新增参数验证 `_validate_params()` — 自动夹紧到 supported 范围
- 新增 `build_seedance_anime_prompt(visual_description, camera_movement, dialogue, emotion)` — 构建动漫风高质量提示词：
  - 视觉主体 → 镜头运动（中文"推/拉/摇/移/跟"自动翻译为英文 cinematography 术语）→ 情绪基调 → 动漫品质标签 → 台词（带 lip-sync 提示）
  - `ANIME_QUALITY_TAGS` 包含: Japanese anime style / 二次元 / smooth fluid animation / vibrant saturated colors / dynamic lighting / detailed background art / sharp clean linework / high quality 4K anime / masterpiece
  - `CAMERA_MOVEMENT_HINTS` 字典: 推→slow dolly-in, 拉→slow dolly-out, 跟→tracking shot, 摇→horizontal pan, 急摇→quick whip pan with motion blur 等
- 任务结果解析：兼容 `content.video_url`、`content[].video_url`、顶层 `video_url`、`data.video_url` 多种返回格式
- 轮询参数调整：max_wait 600s→900s（15s/1080p 通常需 2-4 分钟），poll_interval 5s→6s

**文件**: `src/backend/app/api/v1/endpoints/storyboard.py`

- `GenerateSegmentVideoRequest` 新增 `resolution: str = "1080p"` 字段
- `generate_segment_video` 端点改用 `build_seedance_anime_prompt()` 构建提示词
- Reference image 回退逻辑：角色参考图缺失时使用剧集封面作为 i2v first_frame
- 修复 `episode_number` 取值（之前传 None 导致存储路径错误）
- 移除冗余的二次下载逻辑（service 内部已下载到正确路径）

**文件**: `src/frontend/src/api/storyboard.js` & `src/frontend/src/views/drama/StoryboardEdit.vue`

- API 客户端 `generateSegmentVideo` / `generateAllSegments` 新增 `resolution` 参数
- StoryboardEdit 默认传 `resolution: '1080p'`

**模型配置切换**: 通过 PUT `/api/v1/model-config/3` 把 video model 从 `wanx`/`wan2.7-i2v` 切换到 `seedance`/`doubao-seedance-2-0-260128`。

**端到端验证**（2026-04-29 15:08）:
```
SUCCESS: True
TASK_ID: cgt-20260429150157-kwrrx
VIDEO_URL: https://ark-acg-cn-beijing.tos-cn-beijing.volces.com/doubao-seedance-2-0/...
LOCAL_PATH: media/projects/999/episodes/ep99/seg01/video.mp4 (17MB mp4)
```
真实 15s/1080p 视频生成成功，文件已落盘。

### 12.14 Reference image 公网可达性 — base64 data URL 方案

**问题**: 第一次端到端用真实数据生成时，Ark 报 `HTTP 400 InvalidParameter: content[1].image_url ... resource download failed`。

**根因（多层）**:
1. 后端在 `localhost:8010`，外网（火山引擎服务端）下不到 `http://localhost/media/...`
2. 公网 IP `183.129.232.94` 没有 NAT 映射到 8010 端口（只有前端 18362 映射）
3. 角色图片实际存为本地绝对路径 `/mnt/ddata2/.../front.png`，更不可能下载
4. 旧 storyboards 的 `image_url` 是 DashScope 预签名 OSS URL，已过期（`Expires=1777440116`）
5. `segment.character_image_refs` 在生成时角色还没图，所以全是 `{}`

**修复**: `src/backend/app/services/seedance_video.py` 新增 `normalize_image_url_for_ark(image_url)` 函数：
- 本地文件路径 → 读文件 → base64 data URL（实测 Ark 接受 1.1MB+ data URL）
- `/media/...` 相对 URL → 解析到本地文件 → base64
- `http://localhost/...` 或私有 IP URL → 提取 `/media/...` 路径 → 本地文件 → base64
- 公网 HTTP URL → 直接传（Ark 自己下载）
- 无法解析 → 返回 None，跳过 reference image（fallback 到 t2v 模式）

**修复**: `src/backend/app/api/v1/endpoints/storyboard.py` `generate_segment_video` 重写 ref_image 选择逻辑：
1. 优先取 segment 出场角色的**当前** `character.selected_image`（不依赖 segment 创建时的快照）
2. 回退到 `segment.character_image_refs` 缓存
3. 回退到剧集封面图，但**跳过过期的 OSS URL**（含 `Expires=` 参数）
4. 全部走 `normalize_image_url_for_ark()`，本地路径自动转 base64

**前端 ModelConfig UI 更新**: `src/frontend/src/views/settings/ModelConfig.vue`
- 视频 Provider 下拉新增 `Seedance 2.0 (火山引擎/推荐)`
- 视频模型下拉新增三个 Seedance 模型: `doubao-seedance-2-0-260128` / `doubao-seedance-2-0-fast-260128` / `doubao-seedance-1-5-pro-251215`
- 默认值改为 Seedance

**端到端最终验证**（2026-04-29 15:51）:
```
seg01/video.mp4: 7969057 bytes (7.6MB, 15s 1080p)
seg02/video.mp4: 9047728 bytes (8.6MB, 15s 1080p)
后端日志: [seedance] Using base64 data URL (1138KB) for reference image
```
真实剧集 ep01 的两个 segment 视频都生成成功，含角色一致性参考图，含嵌入式音频对白，存储在 `media/projects/{id}/episodes/epXX/segYY/video.mp4`。

### 12.15 视频生成参数面板（ModelConfig 全开放）

**问题**: 用户希望视频时长、分辨率、画面比例等参数都可在模型配置页自定义，每次生成沿用默认值，无需写死代码。

**修复**:

**文件**: `src/frontend/src/views/settings/ModelConfig.vue`

视频区扩展为完整参数面板（横跨整行），分两个区块：

- **模型连接区**: 提供商 / 具体模型 / API Key / Base URL，每个字段都有用途说明
- **生成参数区**:
  - **视频时长**: 4/5/8/10/12/**15** 秒（含价格提示）
  - **分辨率**: 480p / 720p / **1080p**（说明价格关系）
  - **画面比例**: 16:9（B站）/ 9:16（抖音）/ 1:1 / 4:3 / 3:4 / 21:9
  - **嵌入音频**: 复选框（仅 Seedance 2.0 支持）
  - **添加水印**: 复选框
  - **预估单价**: 实时计算 `约 ¥X.XX / 视频`，含 Fast 折扣

**文件**: `src/backend/app/api/v1/endpoints/storyboard.py`

`GenerateSegmentVideoRequest` 重构为**三层参数优先级**：
1. 请求体显式参数（最高，可针对单 segment 覆盖）
2. `ModelConfig.params` 中保存的用户默认值（中）
3. 服务硬编码默认值（最低）

`GenerateSegmentVideoRequest` 全字段改为 `Optional`，配合 `cfg_params.get(key, default)` 的优先级解析逻辑。

### 12.16 删除功能（项目 / 角色）

**问题**: 项目和角色没有删除入口；后端 `delete_project` 仅删主表记录，留下孤儿数据（characters / storyboards / segments）和媒体文件。

**修复**:

**文件**: `src/backend/app/api/v1/endpoints/projects.py` `delete_project`
- **级联删除**: Segments → Storyboards → Characters → GeneratedVideos → Project
- **媒体清理**: 递归删除 `media/projects/{id}/` 整个文件夹
- 所有删除在一个事务中完成，磁盘空间自动回收

**文件**: `src/backend/app/api/v1/endpoints/characters.py` `delete_character`
- 删除角色记录后清理 `media/projects/{pid}/characters/{name}/` 文件夹（三视图、表情图）

**文件**: `src/frontend/src/views/ProjectsView.vue`
- 项目卡片右上角悬停显示红色删除按钮
- 确认对话框列出会被一并删除的内容（角色 / 剧集 / 视频 / 媒体文件夹）
- 处理中显示 spinner，操作不可逆告警

**文件**: `src/frontend/src/views/CharactersView.vue`
- 三个 hover 按钮全部接通：👁️ 预览大图 / ✏️ 编辑 / 🗑️ 删除
- 新增"预览大图" Modal
- 删除确认带"剧本台词不受影响"的提示

**文件**: `src/frontend/src/views/drama/ScriptWorkspace.vue`
- 角色侧栏每个卡片在"生成形象"和"编辑"按钮旁加红色删除按钮
- 同款确认对话框

**端到端验证**:
```
POST /projects → id=8 创建 → POST /characters → id=26 创建
DELETE /characters/26 → "Character deleted successfully"
DELETE /projects/8 → "Project deleted successfully"
GET /projects/8 → 404 ✅
GET /characters/26 → 404 ✅
```

### 12.17 角色图片路径全链路标准化

**问题**: 用户反馈"生成人物图像的接口好像还是没有用" — API 调用成功，但前端 `<img>` 标签渲染不出来。

**根因**: 数据库里 `characters.selected_image / alternative_images / three_views.design_sheet` **存的是绝对文件系统路径**（`/mnt/ddata2/.../front.png`），浏览器无法访问本地文件系统。后端的 normalize 函数只处理 `selected_image` 一个字段，`alternative_images` 和 `three_views` 里的 URL 完全没动。

**修复**:

**文件**: `src/backend/app/services/character_consistency.py`
- `generate_three_views()` 落库时直接调用 `local_path_to_url()`，把绝对路径转成 `/media/...` URL 后再存
- `selected_image` / `alternative_images` / `three_views.design_sheet` 三个字段都用统一的 `/media/...` 格式

**文件**: `src/backend/app/api/v1/endpoints/characters.py`
- 提取 `_normalize_url()` 工具函数：处理绝对路径 / 含 `/media/` 的字符串 / HTTP URL 多种格式
- 提取 `_normalize_character()` 函数：一并标准化 `selected_image` / `alternative_images` / `three_views`
- `GET /characters` / `GET /characters/{id}` 都用新函数

**文件**: `src/backend/app/api/v1/endpoints/projects.py`
- `_normalize_character_fields()` 标准化所有图像字段
- `GET /projects/{id}/characters` 一并使用

**一次性 DB 迁移**: 写脚本扫描 9 个历史角色，把绝对路径全部转为 `/media/...` 格式（之前 alt + tv 没被任何 normalize 函数处理）。

**端到端验证**:
```
POST /characters/25/generate-three-views →
  selected_image: "/media/projects/7/characters/佐藤葵/design_sheet.png"
  three_views.design_sheet: "/media/projects/7/characters/佐藤葵/design_sheet.png"
GET /projects/7/characters → 全部 ✓ /media/...
```

### 12.18 DeepSeek-V4-Pro 通过 Anthropic 兼容接口接入

**需求**: 用户提供 deepseek-v4-pro 模型 + Anthropic 兼容接口 `https://api.deepseek.com/anthropic`，需要在模型配置页可以直接选用。

**实现**:

**文件**: `src/backend/app/services/llm_service.py`
- `ClaudeService.__init__` 新增 `base_url` 参数支持 — 当 base_url 提供时，AsyncAnthropic 客户端用该地址作为 endpoint，使其同时支持 Anthropic 官方 API 和兼容接口（DeepSeek、Bedrock、Vertex 等）
- `get_llm_service` 工厂函数新增路由：
  - `provider="deepseek-anthropic"` / `"deepseek_anthropic"` / `"deepseek-v4"` → `ClaudeService(base_url="https://api.deepseek.com/anthropic", model="deepseek-v4-pro")`

**文件**: `src/backend/app/api/v1/endpoints/projects.py`
- `provider_name` 友好名称映射新增 `deepseek-anthropic → "DeepSeek-V4-Pro (Anthropic-compat)"`

**文件**: `src/frontend/src/views/settings/ModelConfig.vue`
- 文本模型下拉新增 `DeepSeek-V4-Pro (Anthropic接口/推荐)` 选项
- 新增独立的"模型"输入框 + "Base URL"输入框（默认值会根据所选 provider 自动填充）
- `TEXT_PROVIDER_DEFAULTS` 字典定义各 provider 的默认 model + base_url
- `onTextProviderChange()` 切换 provider 时自动填充 model 和 base_url 默认值
- 实时切换说明文字（`v-if="textModel.provider === 'deepseek-anthropic'"`）

**验证**:
```python
get_llm_service('deepseek-anthropic', 'sk-test', model='deepseek-v4-pro')
→ ClaudeService(base_url='https://api.deepseek.com/anthropic/', model='deepseek-v4-pro')
```

### 12.19 服务重启（2026-04-29 16:58）

旧 PID 已 `fuser -k`，重新启动：
- Backend `uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload` (PID 4032137)
- Frontend `npx vite --host --port 8362` (PID 4032398)
- 公网访问 `http://183.129.232.94:18362`

### 12.20 四大问题修复（2026-04-29 17:30）

产品审查 + 代码专家双角色联合审查，修复 4 个已知问题：

#### 问题 1：CharacterModal 信息不完整

**根因**: `generate_script` 保存角色数据时，仅提取 `appearance.face` 字段，丢失 hair/body/skin/distinctive_features。

**修复**:
- `src/backend/app/api/v1/endpoints/projects.py` — 角色创建时将 appearance/clothing 的所有子字段用"，"拼接为完整文本
- `src/frontend/src/components/CharacterModal.vue` — 重构信息展示区：增加角色头像预览、年龄/性别/职业标签、性格/外貌/服装详情、当前设计图预览

#### 问题 2：片段时长固定 15s 不可配置

**根因**: `prompts.py` 模板中 segment duration 硬编码为 `15`，LLM 始终输出 15s。

**修复**:
- `src/backend/app/services/prompts.py` — 将 `"duration": 15` 改为 `"duration": 10` 并增加说明"5-15秒不等，根据内容合理分配"
- 更新 SCRIPT_SYSTEM_PROMPT 和 STORYBOARD_SYSTEM_PROMPT 中的段式结构描述
- 前端 ScriptWorkspace / StoryboardEdit 中移除硬编码的"每段~15s"显示

#### 问题 3：Fast 模型视频生成失败

**三个根因**:

1. **API Key 不匹配** — fast 模型使用不同的 Ark 账号密钥
2. **API Schema 错误** — 我们使用 inline flags 格式（`--duration 15` 内嵌在 text 中），但 Ark v3 正确格式是 top-level 参数
3. **Duration 覆盖** — 前端发送 `duration: 15`（来自 segment.duration）覆盖了 config 的 `duration: 5`，fast 模型不支持 15s

**修复**:

**文件**: `src/backend/app/services/seedance_video.py`
- `generate()` 方法重写：从 inline flags 格式改为 top-level 参数格式
  - 旧：`"text": "<prompt> --resolution 1080p --duration 15 --ratio 16:9"`
  - 新：payload 顶层 `"duration": 5, "ratio": "16:9", "generate_audio": true, "watermark": false`
- reference image 添加 `"role": "reference_image"` 字段
- `test_connection()` 同步更新为新格式

**文件**: `src/backend/app/api/v1/endpoints/storyboard.py`
- `generate_segment_video()` — duration 优先级改为：request body → ModelConfig.params → defaults（不再用 segment.duration 覆盖 config）
- 错误处理改进：失败时返回 `{"status": "failed", "error": "..."}` 而非抛 500 异常

**文件**: `src/frontend/src/views/drama/StoryboardEdit.vue`
- `generateSegmentVideo()` — 不再发送 `duration: seg.duration`，改为空 body `{}`
- 错误显示优化：读取 `res.data.error` 字段

**数据库**: `model_configs` video 行
- `model` → `doubao-seedance-2-0-fast-260128`
- `api_key` → 新的 fast 模型密钥
- `params.duration` = 5, `params.resolution` = "720p"

**验证**: 项目 8 第 1 集 4 个片段全部生成成功（1.6-2.5MB/段，5s 720p）

#### 问题 4：UX 体验优化

**修复列表**:
- StoryboardEdit 顶部统计栏新增视频模型配置信息显示（模型名 · 时长 · 分辨率 · 比例）
- 错误消息改为可关闭的横幅（带 × 按钮）
- 片段状态徽章增加"处理中"旋转动画
- "重新生成"按钮不再对已完成的片段禁用
- 批量生成遇到失败时继续生成剩余片段（不再中断）
- 批量生成完成后显示成功/失败计数
- 待生成片段数量显示优化
