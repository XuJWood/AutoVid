# AutoVid - AI短剧创作平台

一站式AI短视频生成与发布工具，让创意一键成片。

## 功能特性

- 🎬 **双入口设计** - 短剧创作与单视频生成两种模式
- 🤖 **多模型支持** - 阿里云百炼、OpenAI、Anthropic、DeepSeek 等
- 🎭 **角色一致性** - Character ID 锁定，确保角色在不同场景中一致
- ✏️ **提示词可控** - 可查看和修改各环节的提示词模板
- 📤 **多平台发布** - 支持抖音、快手、B站、小红书等

## 技术栈

| 类别 | 技术 |
|-----|------|
| 后端 | FastAPI, SQLAlchemy |
| 前端 | Vue 3, Vite, TailwindCSS |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |
| AI集成 | 阿里云百炼、OpenAI、Anthropic、DeepSeek |

## 快速开始

```bash
# 克隆项目
git clone https://github.com/XuJWood/AutoVid.git
cd AutoVid

# 后端设置
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
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

## 服务地址

- 前端: http://localhost:5173/
- 后端: http://localhost:8000/
- API文档: http://localhost:8000/docs

## 项目结构

```
ai-video-generator/
├── src/
│   ├── backend/app/        # 后端服务
│   └── frontend/src/       # 前端界面
├── docs/                   # 文档
├── logs/                   # 日志
└── media/                  # 媒体文件
```

## 许可证

MIT License
