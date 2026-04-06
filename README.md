# AutoVid

**AI短剧创作平台** - 一站式AI视频生产工具

## 项目简介

AutoVid 是面向 **AI视频创作者和内容供应商** 的一站式AI视频生产平台，提供两大核心功能：

| 入口 | 功能 | 适用场景 |
|-----|------|---------|
| **短剧创作** | 文字→剧本→角色→分镜→完整短剧 | 连续剧、系列内容 |
| **视频生成** | 人物形象→一致性视频 | 单条视频、角色IP打造 |

### 核心特性

- 🎬 **双入口设计** - 短剧创作与单视频生成两种模式
- 🤖 **多模型支持** - 阿里云百炼、OpenAI、Anthropic、DeepSeek 等
- 🎭 **角色一致性** - Character ID 锁定，确保角色在不同场景中一致
- ✏️ **提示词可控** - 可查看和修改各环节的提示词模板
- 📤 **多平台发布** - 支持抖音、快手、B站、小红书等
- 🔄 **流式生成** - 实时显示剧本生成进度

## 技术栈

| 类别 | 技术 |
|-----|------|
| **后端** | FastAPI, SQLAlchemy, AsyncPG |
| **前端** | Vue3, Vite, TailwindCSS |
| **数据库** | SQLite(开发) / PostgreSQL(生产) |
| **缓存** | Redis |
| **任务队列** | Celery |
| **AI集成** | 阿里云百炼(通义千问/万相/CosyVoice)、OpenAI、Anthropic、DeepSeek |
| **视频处理** | FFmpeg |

## 项目结构

```
AutoVid/
├── src/
│   ├── backend/
│   │   └── app/
│   │       ├── api/v1/endpoints/   # API端点
│   │       │   ├── projects.py     # 项目管理
│   │       │   ├── characters.py   # 角色管理
│   │       │   ├── videos.py       # 视频生成
│   │       │   ├── model_config.py # 模型配置
│   │       │   └── prompt_template.py # 提示词模板
│   │       ├── core/               # 配置、数据库
│   │       ├── services/           # AI服务层
│   │       │   ├── llm_service.py  # 大语言模型
│   │       │   ├── image_service.py # 图像生成
│   │       │   ├── voice_service.py # 语音合成
│   │       │   ├── video_service.py # 视频生成
│   │       │   └── alibaba_cloud.py # 阿里云百炼
│   │       └── main.py             # 应用入口
│   └── frontend/
│       └── src/
│           ├── api/                # API服务
│           ├── components/         # 组件
│           ├── views/              # 页面
│           │   ├── drama/          # 短剧创作
│           │   ├── video/          # 视频生成
│           │   └── settings/       # 系统设置
│           └── router/             # 路由
├── docs/
│   ├── product_spec.md             # 产品需求文档
│   ├── research_report.md          # 市场调研报告
│   ├── ui_design.md                # UI设计说明
│   └── ui-screens/                 # UI原型HTML
├── tests/                          # 测试代码
└── media/                          # 媒体文件
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Redis (可选，用于异步任务)

### 本地开发

```bash
# 克隆项目
git clone https://github.com/XuJWood/AutoVid.git
cd AutoVid

# 后端设置
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API 密钥

# 启动后端
cd src/backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 前端设置 (新终端)
cd src/frontend
npm install
npm run dev
```

### Docker 部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## API 文档

启动后端后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 已实现功能

### 后端 API
- [x] 项目管理 CRUD
- [x] 角色管理 CRUD
- [x] 模型配置管理
- [x] 提示词模板管理
- [x] 视频生成管理
- [x] 剧本生成（流式响应）

### AI 服务集成
- [x] 阿里云通义千问（文本生成）
- [x] 阿里云万相（图像生成）
- [x] 阿里云 CosyVoice（语音合成）
- [x] OpenAI GPT（文本生成）
- [x] Anthropic Claude（文本生成）
- [x] DeepSeek（文本生成）

### 前端页面
- [x] 首页（双入口选择）
- [x] 短剧项目创建
- [x] 剧本编辑工作台
- [x] 角色选择页
- [x] 场景配置页
- [x] 视频结果页
- [x] 模型配置设置
- [x] 提示词模板管理
- [x] 角色库

### 部署配置
- [x] Docker Compose 编排
- [x] 后端/前端 Dockerfile
- [x] Makefile 开发命令

## 待开发功能

- [ ] 分镜生成功能
- [ ] 视频生成功能
- [ ] 多平台发布
- [ ] 测试用例
- [ ] 生产环境部署

## 许可证

MIT License
