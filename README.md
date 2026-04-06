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
- 🤖 **多模型支持** - 可自由切换 GPT-4、Claude、DeepSeek 等
- 🎭 **角色一致性** - Character ID 锁定，确保角色在不同场景中一致
- ✏️ **提示词可控** - 可查看和修改各环节的提示词模板
- 📤 **多平台发布** - 支持抖音、快手、B站、小红书等

## 技术栈

| 类别 | 技术 |
|-----|------|
| **后端** | FastAPI, SQLAlchemy, AsyncPG |
| **前端** | Vue3, Vite, TailwindCSS |
| **数据库** | PostgreSQL, Redis |
| **任务队列** | Celery |
| **AI集成** | OpenAI, Anthropic, DeepSeek, 可灵AI, ElevenLabs |
| **视频处理** | FFmpeg |

## 项目结构

```
AutoVid/
├── src/
│   ├── backend/
│   │   └── app/
│   │       ├── api/v1/endpoints/   # API端点
│   │       ├── core/               # 配置、数据库
│   │       └── main.py             # 应用入口
│   └── frontend/
│       └── src/
│           ├── api/                # API服务
│           ├── components/         # 组件
│           ├── views/              # 页面
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
- PostgreSQL 15+
- Redis 7+

### 本地开发

```bash
# 克隆项目
git clone https://github.com/XuJWood/AutoVid.git
cd AutoVid

# 后端设置
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入数据库连接信息

# 启动后端
make run-backend

# 前端设置 (新终端)
cd src/frontend
npm install
npm run dev
```

### Docker 部署

```bash
# 启动所有服务
make docker-up

# 查看日志
docker-compose logs -f

# 停止服务
make docker-down
```

## API 文档

启动后端后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发进度

- [x] 项目架构设计
- [x] 后端 API 实现
- [x] 前端页面实现
- [ ] AI 服务集成
- [ ] 测试用例
- [ ] 部署上线

## 许可证

MIT License
