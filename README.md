# AutoVid - AI 漫剧创作平台

一站式日系动漫短剧（漫剧）AI 创作平台。从文字创意到成品视频，全链路自动化。

## 什么是漫剧？

漫剧（Anime Short Drama）是一种快节奏的日系动漫短视频，每集约 60 秒（4 个片段），具有完整的叙事单元——冲突、反转、爽点、钩子。适合抖音、快手、B站等短视频平台。

## 核心流程

```
创建项目 → AI 生成剧本（含角色+剧集+片段） → 自动创建动漫角色
    ↓
生成角色设计图（三视图+表情） → 生成剧集封面
    ↓
逐片段生成视频（Seedance 视频+音频一体化） → 预览 & 下载
```

## 功能特性

- **AI 剧本生成** — 漫剧创作大师提示词，自动生成完整剧本（8-120 集），含反转设计、爽点安排、角色设定、分段脚本
- **分段式结构** — 每集 ~60s = 4 个片段（5-15s/段），每个片段独立生成视频，支持逐段预览和重新生成
- **动漫角色设计** — 单张角色设计图（三视图 + 4 种表情），支持提示词预览和自定义编辑
- **Seedance 视频生成** — 火山引擎 Ark API，文本+参考图→视频，视频内嵌音频（含对话语音），无需单独 TTS
- **多模型支持** — 文本：通义千问 / DeepSeek-V4-Pro；图像：万相 wanx2.1；视频：Seedance 2.0（标准/Fast）
- **角色一致性** — 角色参考图自动注入视频生成 prompt，本地图片自动转 base64 供 Ark API 使用
- **可编辑剧本** — 前端直接编辑标题、对话、情绪、场景描述
- **全链路管理** — 项目/角色/剧集/片段的创建、编辑、删除（含媒体文件级联清理）
- **模型配置面板** — 文本/图像/视频/语音模型独立配置，视频参数面板（时长/分辨率/比例/音频/水印）

## 技术栈

| 类别 | 技术 |
|-----|------|
| 后端框架 | FastAPI + SQLAlchemy Async (Python 3.11) |
| 前端框架 | Vue 3 + Vite + TailwindCSS |
| 数据库 | SQLite (aiosqlite) |
| 文本模型 | 通义千问 qwen-plus / DeepSeek-V4-Pro (Anthropic 兼容接口) |
| 图像模型 | 万相 wanx2.1-t2i-turbo (DashScope) |
| 视频模型 | Seedance 2.0 (火山引擎 Ark API)，支持 standard / fast |
| 语音模型 | CosyVoice / Qwen TTS (预留，视频已内嵌音频) |

## 快速开始

### 环境要求

- Python 3.11+ (推荐 conda)
- Node.js 18+
- 阿里云百炼 API Key (图像)
- 火山引擎 Ark API Key (视频)

### 安装

```bash
git clone https://github.com/XuJWood/AutoVid.git
cd AutoVid

# 后端
conda activate lg_1.0  # 或自建虚拟环境
pip install -r src/backend/requirements.txt

# 前端
cd src/frontend
npm install
```

### 启动

```bash
# 后端（终端 1）
cd src/backend
uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload

# 前端（终端 2）
cd src/frontend
npx vite --host --port 8362
```

### 服务地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:8362/ |
| 后端 API | http://localhost:8010/ |
| API 文档 | http://localhost:8010/docs |

### 首次使用

1. 打开前端，进入 **设置 → 模型配置**
2. 配置文本模型（通义千问或 DeepSeek）、图像模型（万相）、视频模型（Seedance）的 API Key
3. 创建新项目 → 填写故事描述 → 生成剧本
4. 在剧本页面查看角色 → 点击"生成形象"生成角色设计图
5. 进入剧集编辑 → 生成封面 → 逐段生成视频
6. 预览页面查看完整剧集视频

## 数据模型

```
Project (项目)
  ├── Character (角色) — name, appearance, clothing, selected_image, three_views
  ├── Storyboard (剧集/Episode) — episode_number, title, description, image_url
  │     └── Segment (片段) — segment_number, visual_description, camera_movement,
  │                           dialogue, duration, video_url, video_status
  └── ModelConfig (模型配置) — provider, model, api_key, params
```

## 项目结构

```
AutoVid/
├── src/
│   ├── backend/app/
│   │   ├── main.py                  # FastAPI 入口
│   │   ├── core/database.py         # 数据模型 (Project, Character, Storyboard, Segment, ModelConfig)
│   │   ├── api/v1/endpoints/
│   │   │   ├── projects.py          # 项目管理 + 剧本生成 (SSE)
│   │   │   ├── characters.py        # 角色 CRUD + 三视图/设计图生成
│   │   │   ├── storyboard.py        # 剧集+片段管理 + 封面/视频生成
│   │   │   └── model_config.py      # 模型配置 CRUD
│   │   └── services/
│   │       ├── seedance_video.py     # Seedance 2.0 视频服务 (Ark API)
│   │       ├── prompts.py           # 提示词模板（剧本/角色/分镜）
│   │       ├── character_consistency.py  # 角色设计图生成
│   │       ├── llm_service.py       # LLM 服务工厂 (Qwen/Claude/DeepSeek)
│   │       ├── image_service.py     # 图像生成工厂
│   │       ├── video_service.py     # 视频生成工厂
│   │       └── media_storage.py     # 文件存储 + URL 规范化
│   └── frontend/src/
│       ├── views/drama/
│       │   ├── ScriptWorkspace.vue   # 剧本工作台（编辑+角色管理）
│       │   ├── StoryboardEdit.vue    # 剧集编辑（片段视频生成）
│       │   └── VideoPreview.vue      # 视频预览（逐段播放）
│       ├── components/
│       │   └── CharacterModal.vue    # 角色详情+设计图生成弹窗
│       └── api/                      # Axios API 封装
├── media/projects/{id}/              # 生成内容（不入 git）
│   ├── characters/{name}/
│   │   ├── design_sheet.png          # 角色设计图（三视图+表情）
│   │   └── reference.png            # 参考图副本
│   └── episodes/ep{XX}/
│       ├── cover.png                 # 剧集封面
│       └── seg{YY}/video.mp4         # 片段视频（含音频）
├── docs/                             # 文档
│   ├── DEV_LOG.md                    # 开发日志
│   ├── product_spec.md               # 产品规格
│   ├── VIDEO_SOLUTION.md             # 视频方案
│   ├── research_report.md            # 调研报告
│   └── ui_design.md                  # UI 设计
└── README.md
```

## API 概览

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/v1/projects/{id}/script/generate` | 生成剧本（SSE 流式） |
| GET  | `/api/v1/projects/{id}/characters` | 获取项目角色列表 |
| POST | `/api/v1/characters/{id}/generate-three-views` | 生成角色设计图 |
| GET  | `/api/v1/characters/{id}/preview-three-views-prompt` | 预览设计图提示词 |
| POST | `/api/v1/storyboard/project/{id}/generate` | 从剧本生成剧集+片段 |
| GET  | `/api/v1/storyboard/project/{id}` | 获取剧集列表（含片段） |
| POST | `/api/v1/storyboard/{id}/generate-image` | 生成剧集封面 |
| POST | `/api/v1/storyboard/segment/{id}/generate-video` | 生成片段视频 (Seedance) |
| POST | `/api/v1/storyboard/{id}/generate-all-segments` | 批量生成该集所有片段视频 |

## Seedance 视频生成

使用火山引擎 Ark API v3，支持 text-to-video 和 image-to-video：

```python
# Ark API payload 格式
{
    "model": "doubao-seedance-2-0-fast-260128",
    "content": [
        {"type": "text", "text": "<anime prompt>"},
        {"type": "image_url", "image_url": {"url": "<base64 or public URL>"}, "role": "reference_image"}
    ],
    "duration": 5,
    "ratio": "16:9",
    "generate_audio": true,
    "watermark": false
}
```

- 本地参考图自动转 base64 data URL（Ark 无法访问 localhost）
- 异步轮询任务状态，视频下载到本地存储
- 支持 standard（最长 15s）和 fast（推荐 5s）模型

## 许可证

MIT License
