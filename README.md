# AutoVid - AI 漫剧创作平台

一站式日系动漫短剧（漫剧）AI 创作平台。从剧本到成品视频，全链路自动化。

## 什么是漫剧？

漫剧（Anime Short Drama）是一种快节奏的日系动漫短视频，每集约 20 秒，具有完整的叙事单元。适合抖音、快手、B站等短视频平台。

## 核心流程

```
创建项目 → AI 生成剧本 → 自动创建动漫角色 → 生成角色三视图
                ↓
        生成剧集封面（动漫风格） → 生成视频（文生视频） → TTS 配音 → 最终成品
```

## 功能特性

- **AI 剧本生成** — 漫剧创作大师，自动生成 5+ 集剧本，含反转设计、爽点安排、角色设定
- **动漫角色设计** — 日系动漫风格角色，自动生成三视图（正面/侧面/背面），女性角色性感可爱
- **剧集化管理** — 每集独立封面、视频、配音，支持单独下载
- **多模型支持** — 阿里云百炼（通义千问、万相、Qwen TTS），可扩展 OpenAI/Claude 等
- **角色一致性** — 台词角色自动匹配角色库，外观描述融入视频提示词
- **可编辑剧本** — 前端直接编辑剧本内容、标题、对话
- **独立下载** — 每集视频独立下载，无需最终合并导出

## 技术栈

| 类别 | 技术 |
|-----|------|
| 后端框架 | FastAPI (Python 3.11) |
| 前端框架 | Vue 3 + Vite + TailwindCSS |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |
| 文本模型 | 通义千问 qwen-plus |
| 图像模型 | 万相 wanx2.1-t2i-turbo |
| 视频模型 | 万相 wanx2.1-t2v-turbo |
| 语音模型 | Qwen TTS qwen3-tts-flash |
| 音频处理 | FFmpeg |

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- FFmpeg
- 阿里云百炼 API Key

### 安装

```bash
git clone https://github.com/XuJWood/AutoVid.git
cd AutoVid

# 后端
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY=sk-xxx

# 前端
cd src/frontend
npm install
```

### 启动

```bash
# 后端（终端 1）
PYTHONPATH=src/backend python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 前端（终端 2）
cd src/frontend
npm run dev
```

### 服务地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173/ |
| 后端 API | http://localhost:8000/ |
| API 文档 | http://localhost:8000/docs |

### 首次使用

1. 打开 http://localhost:5173/，点击"短剧创作"
2. 在设置页面配置模型 API Key
3. 创建新项目 → 生成剧本 → 生成剧集 → 生成视频 → 预览下载

## 项目结构

```
ai-video-generator/
├── src/
│   ├── backend/app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── core/database.py     # 数据库模型（Project, Character, Storyboard, ModelConfig）
│   │   ├── api/v1/endpoints/    # API 端点
│   │   │   ├── projects.py      # 项目管理
│   │   │   ├── characters.py    # 角色管理 + 三视图生成
│   │   │   ├── storyboard.py    # 剧集管理 + 视频/音频生成
│   │   │   ├── pipeline.py      # 一键生成流水线
│   │   │   └── model_config.py  # 模型配置
│   │   └── services/
│   │       ├── alibaba_cloud.py           # 阿里云百炼服务
│   │       ├── prompts.py                 # 提示词模板
│   │       ├── pipeline.py                # 生成流水线
│   │       ├── character_consistency.py   # 角色一致性服务
│   │       ├── video_audio_service.py     # TTS + FFmpeg 配音
│   │       ├── media_storage.py           # 文件存储管理
│   │       └── image_service.py           # 图像生成工厂
│   └── frontend/src/
│       ├── views/drama/
│       │   ├── ScriptWorkspace.vue    # 剧本工作台
│       │   ├── StoryboardEdit.vue     # 剧集编辑
│       │   └── VideoPreview.vue       # 视频预览
│       ├── components/
│       └── api/
├── tests/                   # 测试（66 个用例）
├── media/projects/{id}/     # 生成内容（不入 git）
│   ├── characters/{name}/   # 角色三视图
│   └── episodes/ep{XX}/     # 剧集封面 + 成品视频
├── docs/                    # 文档
└── logs/                    # 日志
```

## API 概览

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/v1/projects/{id}/generate-script` | 生成剧本（SSE 流式） |
| POST | `/api/v1/characters/{id}/generate-three-views` | 生成角色三视图 |
| POST | `/api/v1/storyboard/project/{id}/generate` | 生成剧集 |
| POST | `/api/v1/storyboard/{id}/generate-image` | 生成剧集封面 |
| POST | `/api/v1/storyboard/{id}/generate-video` | 生成剧集视频 + 配音 |
| POST | `/api/v1/pipeline/start` | 一键全链路生成 |
| GET | `/api/v1/pipeline/status/{project_id}` | 查询流水线进度 |

## 媒体文件组织

```
media/projects/{project_id}/
├── characters/
│   ├── 角色名/front.png       # 正面
│   ├── 角色名/side.png        # 侧面(45°)
│   ├── 角色名/back.png        # 背面
│   └── 角色名/reference.png   # 参考图（正面副本）
├── episodes/
│   └── ep01/
│       ├── cover.png              # 剧集封面
│       └── final_with_audio.mp4   # 带配音成品视频
└── audio/
    └── ep01_dialogue.wav   # 对话音频
```

## 许可证

MIT License
