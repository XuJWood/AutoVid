# AI视频自动生成与发布项目

## 项目日志

### 2026-04-06 - 项目初始化
- 创建项目文件夹结构
- 定义团队角色：产品经理、AI算法工程师、架构师、测试工程师
- 配置项目hooks（日志更新、git同步）
- 项目目标：AI自动生成视频并发布视频

### 2026-04-06 - Git仓库配置
- 连接远程仓库：https://github.com/XuJWood/AutoVid.git
- 初始化项目基础文件：.gitignore, README.md, requirements.txt
- 创建项目目录结构：src/ai, src/backend, src/frontend, tests, docs, media
- 首次推送到GitHub main分支

### 2026-04-06 - 产品调研完成
- 完成AI视频生成领域市场调研
- 分析GitHub主流开源项目：MoneyPrinterTurbo(43k stars)、Open-Sora(20k stars)、MoneyPrinterPlus(15k stars)
- 输出《产品调研报告》：docs/research_report.md
- 输出《产品需求文档(PRD)》：docs/product_spec.md
- 确定产品定位：一站式AI短视频生成与多平台发布工具

### 2026-04-06 - 产品定位调整
- **重新定位**：从"短视频生成工具"调整为"AI短剧创作平台"
- **目标用户**：AI视频创作者/供应商
- **二次调研**：深入分析AI短剧创作领域
- **竞品分析**：Huobao Drama(7.3k stars)、SkyReels、BigBanana AI Director
- **核心痛点**：角色一致性、分镜连贯性、风格统一
- **更新文档**：
  - docs/research_report.md - AI短剧创作专项调研
  - docs/product_spec.md - AI短剧创作平台PRD v2.0
- **核心流程**：文字→剧本→角色形象生成→分镜→视频→发布

### 2026-04-06 - PRD v2.1更新
- **双入口设计**：
  - 入口1：短剧创作（文字→剧本→角色→分镜→完整短剧）
  - 入口2：视频生成（人物→场景→一致性视频）
- **模型配置系统**：支持配置剧本模型、图像模型、视频模型、语音模型
- **提示词修改系统**：各生成环节支持查看默认模板+补充提示词
- **新增文档**：docs/ui_design.md - 前端UI设计说明
- **页面清单**：首页、短剧工作台、视频生成、系统设置等14个页面

### 2026-04-06 - 项目完整实现

#### 后端实现 (FastAPI)
- **入口文件**：src/backend/app/main.py
- **数据库配置**：src/backend/app/core/
  - SQLite (开发环境) + SQLAlchemy 异步支持
  - AsyncSession 会话管理
- **数据模型** (5个核心模型)：
  - Project: 项目管理（类型、状态、配置、剧本内容）
  - Character: 角色管理（外貌、服装、形象图、语音配置）
  - ModelConfig: 模型配置（提供商、API密钥、参数）
  - PromptTemplate: 提示词模板（类型、模板内容、变量）
  - GeneratedVideo: 生成视频（文件路径、状态、生成参数）

- **API端点**：
  - `/api/v1/model-config` - 模型配置管理
  - `/api/v1/prompt-templates` - 提示词模板管理
  - `/api/v1/projects` - 项目CRUD
  - `/api/v1/characters` - 角色CRUD
  - `/api/v1/videos` - 视频生成管理
  - `/health` - 健康检查

- **AI服务层** (src/backend/app/services/)：
  - base.py: 基础服务接口和GenerationResult模型
  - llm_service.py: 大语言模型服务
    - OpenAI GPT 支持
    - Anthropic Claude 支持
    - DeepSeek 支持
    - **阿里云通义千问支持** ✨
  - alibaba_cloud.py: 阿里云百炼服务 ✨
    - QwenService: 通义千问文本生成
    - WanxImageService: 万相图像生成
    - CosyVoiceService: CosyVoice语音合成
  - image_service.py: 图像生成服务
    - DALL-E 支持
    - Stability AI 支持
    - Midjourney 代理支持
    - **阿里云万相支持** ✨
  - voice_service.py: 语音合成服务
    - ElevenLabs 支持
    - Azure Speech 支持
    - OpenAI TTS 支持
    - **阿里云CosyVoice支持** ✨
  - video_service.py: 视频生成服务
  - prompts.py: 专业提示词模板 ✨
    - 剧本生成提示词（基于业界最佳实践）
    - 角色设计提示词
    - 分镜脚本提示词

#### 前端实现 (Vue3 + Vite + TailwindCSS)
- **入口文件**：src/frontend/src/main.js
- **路由配置** (14个页面)：
  - `/` - 首页（双入口选择）
  - `/drama/create` - 短剧项目创建
  - `/drama/:id` - 剧本工作台
  - `/drama/:id/storyboard` - 分镜编辑
  - `/drama/:id/preview` - 视频预览
  - `/video/select` - 视频生成-选择人物
  - `/video/scene` - 视频生成-场景配置
  - `/video/result` - 视频生成-结果展示
  - `/settings/models` - 模型配置
  - `/settings/prompts` - 提示词模板
  - `/settings/defaults` - 默认设置
  - `/characters` - 角色库
  - `/projects` - 项目列表

- **核心组件**：
  - TopNavBar.vue: 顶部导航栏
  - BottomNavBar.vue: 底部导航栏
  - CharacterModal.vue: 角色生成弹窗

- **API服务封装** (src/frontend/src/api/)：
  - modelConfig.js, promptTemplate.js, projects.js, characters.js, videos.js

- **已实现页面**：
  - HomeView.vue: 双入口卡片设计
  - ProjectCreate.vue: 项目创建表单（类型、风格、平台选择）
  - ScriptWorkspace.vue: 剧本编辑工作台
  - CharacterSelect.vue: 角色选择页
  - SceneConfig.vue: 场景配置页
  - VideoResult.vue: 视频结果页
  - ModelConfig.vue: 模型配置设置
  - PromptTemplates.vue: 提示词模板管理
  - DefaultSettings.vue: 默认设置

#### 部署配置
- **docker-compose.yml**：
  - PostgreSQL 15 (端口 5432)
  - Redis 7 (端口 6379)
  - Backend API (端口 8000)
  - Frontend (端口 5173)
  - Celery Worker (异步任务)
- **Dockerfile**: backend/frontend 分别构建
- **Makefile**: 开发环境命令

#### 文档
- docs/research_report.md: 产品调研报告
- docs/product_spec.md: 产品需求文档(PRD)
- docs/ui_design.md: 前端UI设计说明
- docs/ui-screens/: UI原型图资源

---

### 2026-04-06 - 阿里云百炼集成与本地环境配置

#### 阿里云百炼服务适配
- **新增服务**：`src/backend/app/services/alibaba_cloud.py`
  - QwenService: 通义千问文本生成（OpenAI兼容接口）
  - WanxImageService: 万相图像生成
  - CosyVoiceService: CosyVoice语音合成
- **API地址**：`https://dashscope.aliyuncs.com/compatible-mode/v1`

#### 专业提示词模板
- **新增文件**：`src/backend/app/services/prompts.py`
- 基于业界最佳实践整理的专业提示词
- 支持剧本生成、角色设计、分镜脚本三大场景
- 用户可添加额外提示词，系统自动拼接

#### 流式响应支持
- 剧本生成接口支持 Server-Sent Events (SSE)
- 前端实时显示生成进度和状态
- 解决了模型配置中 base_url 为 None 时覆盖默认值的问题

#### 本地开发环境
- **Python环境**：brew 安装的 Python 3.11 + venv 虚拟环境
- **数据库**：SQLite（开发环境）
- **Redis**：brew services 启动
- **前端**：npm run dev

#### 已配置模型
- 文本模型：通义千问 qwen-plus ✅ 测试通过
- 图像模型：万相 wanx2.1-turbo
- 语音模型：CosyVoice cosyvoice-v1

#### 接口测试结果
| 接口 | 状态 |
|------|------|
| 健康检查 | ✅ |
| 模型配置 CRUD | ✅ |
| 项目 CRUD | ✅ |
| 剧本生成（流式） | ✅ 通义千问调用成功 |
| 角色 CRUD | ✅ |

---

## 项目结构

```
ai-video-generator/
├── TEAM.md              # 团队配置
├── CLAUDE.md            # 项目日志（本文件）
├── docker-compose.yml   # Docker 编排
├── Dockerfile.backend   # 后端 Dockerfile
├── Dockerfile.frontend  # 前端 Dockerfile
├── Makefile             # 开发命令
├── requirements.txt     # Python 依赖
├── .env                 # 环境变量
├── tasks/               # 任务文件
├── src/
│   ├── ai/              # AI模块（预留）
│   ├── backend/         # 后端服务
│   │   └── app/
│   │       ├── main.py          # FastAPI 入口
│   │       ├── core/            # 核心配置
│   │       │   ├── config.py    # 设置
│   │       │   └── database.py  # 数据库+模型
│   │       ├── api/v1/endpoints/ # API端点
│   │       └── services/        # AI服务层
│   └── frontend/        # 前端界面
│       └── src/
│           ├── main.js          # 入口
│           ├── App.vue          # 根组件
│           ├── router/          # 路由配置
│           ├── api/             # API封装
│           ├── components/      # 组件
│           └── views/           # 页面视图
├── tests/               # 测试代码
├── docs/                # 文档
└── media/               # 媒体文件
```

---

## 开发规范

### 代码提交规范
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- refactor: 重构
- test: 测试相关
- chore: 构建/工具变动

### 分支策略
- main: 主分支，稳定版本
- develop: 开发分支
- feature/*: 功能分支
- hotfix/*: 紧急修复

---

## 待完成事项

- [x] 安装 Docker Desktop 并启动服务
- [x] 配置本地开发环境 (Python venv + npm)
- [x] 配置阿里云百炼 API 密钥
- [x] 测试剧本生成接口
- [ ] 测试图像生成接口
- [ ] 测试语音合成接口
- [ ] 完善前端模型配置保存功能
- [ ] 实现角色形象生成功能
- [ ] 实现分镜生成功能
- [ ] 实现视频生成功能

---

## 本地开发环境

### 启动命令

```bash
# 进入项目目录
cd /Users/a1/projects/ai-video-generator

# 启动后端 (使用虚拟环境)
source venv/bin/activate
cd src/backend
nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > ../../logs/backend.log 2>&1 &

# 启动前端
cd ../frontend
nohup npm run dev > ../../logs/frontend.log 2>&1 &
```

### 服务地址
- **前端**: http://localhost:5173/
- **后端**: http://127.0.0.1:8000/
- **API文档**: http://127.0.0.1:8000/docs

### 日志位置
- 后端日志: `/Users/a1/projects/ai-video-generator/logs/backend.log`
- 前端日志: `/Users/a1/projects/ai-video-generator/logs/frontend.log`

---

## 已配置的模型

| 类型 | 提供商 | 模型 | 状态 |
|------|--------|------|------|
| 文本 | 阿里云通义千问 | qwen-plus | ✅ 已测试 |
| 图像 | 阿里云万相 | wanx2.1-turbo | 待测试 |
| 语音 | 阿里云CosyVoice | cosyvoice-v1 | 待测试 |

---

## 待完成事项（旧）

- [ ] 安装 Docker Desktop 并启动服务
- [ ] 配置 .env 文件中的 API 密钥
- [ ] 运行数据库迁移
- [ ] 测试完整流程
- [ ] 编写测试用例

---
