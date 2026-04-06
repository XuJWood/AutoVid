# AutoVid

AI自动生成视频并发布的系统

## 项目简介

AutoVid 是一个基于AI的视频自动生成与发布平台，能够：
- AI生成视频内容
- 自动生成文案
- 语音合成
- 一键发布到多平台

## 技术栈

- **AI引擎**: Python, LangChain, OpenAI API / Claude API
- **后端**: FastAPI
- **前端**: React / Vue
- **数据库**: PostgreSQL, Redis
- **任务队列**: Celery

## 项目结构

```
AutoVid/
├── src/
│   ├── ai/          # AI模块
│   ├── backend/     # 后端服务
│   └── frontend/    # 前端界面
├── tests/           # 测试代码
├── docs/            # 文档
└── media/           # 媒体文件
```

## 快速开始

```bash
# 克隆项目
git clone https://github.com/XuJWood/AutoVid.git
cd AutoVid

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 许可证

MIT License
