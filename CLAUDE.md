# AI视频自动生成与发布项目

## 会话记录

> 最新会话记录: `/Users/a1/.claude/projects/-Users-a1/96c77149-dd21-4566-8b0c-b2e2ebd0dd47.jsonl`
>
> 下次对话时说"读取日志继续开发"即可。

---

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

### 2026-04-07 - 测试体系建设

#### 测试架构
- **测试框架**: pytest + pytest-asyncio
- **分层设计**: unit / integration / e2e
- **数据库**: in-memory SQLite 测试隔离
- **Mock策略**: 外部API使用 AsyncMock

#### 测试文件
- `tests/conftest.py` - 公共fixtures配置
- `tests/integration/test_projects.py` - 项目API测试
- `tests/integration/test_characters.py` - 角色API测试
- `tests/integration/test_model_config.py` - 模型配置API测试
- `tests/integration/test_prompt_template.py` - 提示词模板API测试
- `tests/integration/test_videos.py` - 视频API测试
- `tests/integration/test_pipeline.py` - 流水线API测试
- `tests/unit/services/test_llm_service.py` - LLM服务单元测试
- `tests/unit/services/test_image_service.py` - 图像服务单元测试
- `tests/unit/services/test_voice_service.py` - 语音服务单元测试

#### 测试结果
- 54 passed, 1 failed (预存在问题), 12 warnings

---

### 2026-04-07 - 核心功能优化

#### 新增服务

| 服务 | 文件 | 功能 |
|------|------|------|
| **CharacterConsistencyService** | `services/character_consistency.py` | 角色一致性生成，支持参考图引导 |
| **CacheService** | `services/cache_service.py` | 多层缓存（内存+Redis），带装饰器 |
| **ResilienceService** | `services/resilience.py` | 重试/熔断/限流机制 |
| **VideoPipeline** | `services/pipeline.py` | 一键生成流水线 |

#### 新增API端点
- `POST /api/v1/pipeline/start` - 启动一键生成流水线
- `POST /api/v1/pipeline/start/stream` - SSE流式生成
- `GET /api/v1/pipeline/status/{project_id}` - 查询进度
- `DELETE /api/v1/pipeline/status/{project_id}` - 清除状态

#### 设计文档
- `docs/superpowers/plans/2026-04-07-core-optimization.md` - 核心功能优化计划

### 2026-04-26 - 阿里云百炼多模态配置
- 配置 API key: sk-21ba1b4765eb4e64b8e5b2261ae82c22
- 图像 (wanx2.1-t2i-turbo): ✅ 已测试
- 视频 (wanx2.1-t2v-turbo): ✅ 已测试
- 新增 media_storage.py: 生成内容自动下载到 `media/projects/{id}/images/` 和 `videos/`
- main.py: 挂载 `/media` 静态文件服务

---

### 2026-04-26 - 全链路修复与多模态服务集成

#### 问题诊断
通过代码审查发现以下链路断裂：
1. 角色形象生成是 MOCK：`characters.py` 返回占位URL，不调用任何AI服务
2. 无三视图生成：只能生成单张形象图，缺少正面/侧面/背面
3. Pipeline 分镜不持久化：`pipeline.py` 生成分镜JSON后不写入Storyboard表
4. 视频生成阶段为空：`pipeline.py` generate_short_drama 中直接 `pass`
5. 缺少统一多模态接口：图片/视频服务分散，无预留API key的通用入口

#### 修复内容

##### 1. 统一多模态服务接口
- **新增文件**：`src/backend/app/services/multimodal_service.py`
  - `GenericMultimodalService`: 使用 OpenAI 兼容 API 格式
  - `MultimodalImageAdapter` / `MultimodalVideoAdapter`: 适配器
  - 支持文生图、图生图、图生视频
  - API key 为空时返回明确错误提示，不崩溃

##### 2. 修复角色形象生成
- `characters.py:generate_character_image` 端点在获取图像模型配置后调用真实 AI 服务
- 未配置模型时返回 HTTP 400 错误提示
- `image_service.py` 和 `video_service.py` 工厂函数增加 `multimodal` provider 支持

##### 3. 角色三视图生成
- **角色一致性服务**：`character_consistency.py` 新增 `generate_three_views()` 方法
- **API端点**：`POST /characters/{id}/generate-three-views`
- 生成正面/侧面(45°)/背面三张角色形象图

##### 4. Pipeline 分镜持久化与视频生成
- `pipeline.py:generate_storyboard()` 改为生成后创建 Storyboard 表记录
- 新增 `_create_storyboard_from_scene()` 方法：无需LLM直接从剧本shots创建
- `generate_short_drama()` 新增阶段3-5：分镜生成→图片生成→视频生成

##### 5. 前端三视图展示
- `CharacterModal.vue`: 增加"生成三视图"按钮和三视图标签切换(正面/侧面/背面)
- `characters.js` API: 增加 `generateThreeViews()` 方法

#### 完整链路
```
创建项目 → 生成剧本(LLM) → 自动创建角色(DB)
                ↓
    分镜脚本(LLM→Storyboard表) + 角色三视图(多模态→Character表)
                ↓
        分镜图片生成(多模态，可选)
                ↓
        分镜视频生成(多模态，可选)
                ↓
            视频预览+导出
```

#### 待完成
- [x] 提供多模态模型 API key 并测试图片生成
- [x] 提供多模态模型 API key 并测试视频生成
- [x] 测试完整 Pipeline 流程
- [ ] 实现视频导出功能（后端合并视频）

---

### 2026-04-26 - 视频配音与全链路联调

#### 视频配音系统
- **新增文件**：`src/backend/app/services/video_audio_service.py`
  - `VOICE_PROFILES`: Qwen TTS 音色映射（Cherry/Ethan/Jennifer/Ryan 等）
  - `get_voice_for_character()`: 根据角色性别/年龄自动匹配音色
  - `generate_dialogue_audio()`: TTS 生成台词语音 → 下载到本地
  - `merge_video_audio()`: FFmpeg 合并视频 + 音频（h264 copy + aac）
  - `add_audio_to_video()`: 一站式：下载视频 → 生成配音 → 合并 → 返回本地路径
- **Pipeline 阶段6（配音）**：`generate_short_drama()` 新增 AUDIO 阶段
  - 遍历已完成视频的 Storyboard，提取台词 → TTS → FFmpeg 合并
  - 自动根据角色匹配音色，支持 `generate_audio` 选项控制
- **Storyboard 配音端点**：`POST /{id}/generate-audio`
  - 接收台词和音色参数，一键配音并更新 storyboard 记录

#### TTS 模型切换（CosyVoice → Qwen TTS）
- **原因**：CosyVoice 未开通权限；Qwen TTS 可用模型：`qwen3-tts-flash`
- **API 端点**：`/api/v1/services/aigc/multimodal-generation/generation`
- **音色**：Cherry/Ethan/Jennifer/Ryan/Katerina/Elias 等
- `alibaba_cloud.py:CosyVoiceService` 重写为使用 DashScope 原生接口
- `video_audio_service.py`: 音色映射和默认值全部更新为 Qwen TTS 音色

#### 视频生成修复
- **问题**：`wan2.7-i2v`（图生视频）要求 OSS 图片 URL，但 DashScope 生成的图片 URL 有鉴权限制（403）
- **解决**：切换到 `wanx2.1-t2v-turbo`（文生视频），不依赖图片 URL
- **API 格式修复**：DashScope 视频 API 接收 `input.media[].url/type` → 改为 `first_frame`
- `alibaba_cloud.py:WanxVideoService` input 格式修正

#### 本地文件存储与媒体访问
- **media_storage.py**: 图片/视频自动下载到 `media/projects/{id}/images/` 和 `videos/`
- **路径修复**：`main.py` media 挂载从 4 级 `..` 修正为 3 级
- **Storyboard/Pipeline**：`video_url`/`image_url` 优先存本地路径
- 前端 `toPlayableUrl()`: 兼容本地路径（转为 `/media/...`）和远程 URL

#### 前端配音集成
- **StoryboardEdit.vue**: 增加配音按钮、配音统计、`toPlayableUrl()` 路径转换
- **VideoPreview.vue**: 增加 `toPlayableUrl()` 支持本地视频播放
- **storyboard.js API**: 增加 `generateAudio()` 方法

#### Pipeline 修复
- **DB 会话问题**：后台任务使用已关闭的会话 → `start_pipeline` 改为创建独立 `async_session_maker()` 会话
- **Storyboard 生成**：增加 `model`/`base_url` 参数传递，修复 LLM 调用
- **视频生成**：传递 `image_url` 到视频服务

#### API 修复汇总
| 文件 | 修复内容 |
|------|----------|
| `alibaba_cloud.py` | CosyVoice → Qwen TTS；视频 input 格式；添加 `os`/`tempfile` 导入 |
| `video_audio_service.py` | 音色映射更新；添加 `uuid` 导入；本地文件判断 |
| `pipeline.py` | 阶段6配音；local_path 优先；模型参数传递 |
| `storyboard.py` | 配音端点；model/base_url 参数；image_url 传递 |
| `main.py` | media 路径 3 级修正 |
| `pipeline.py`(endpoint) | 独立 DB 会话创建 |

#### 测试结果
| 功能 | 状态 |
|------|------|
| 剧本生成 (qwen-plus) | ✅ |
| 角色自动创建 | ✅ |
| 分镜生成 (LLM + 持久化) | ✅ |
| 图片生成 (wanx2.1-t2i-turbo) | ✅ 本地存储 866KB PNG |
| 视频生成 (wanx2.1-t2v-turbo) | ✅ 本地存储 3.7MB MP4 |
| TTS 语音 (qwen3-tts-flash) | ✅ |
| FFmpeg 视频配音合并 | ✅ 695KB 带音频 MP4 |
| 前端 /media/ 播放 | ✅ HTTP 200, video/mp4 |
| Pipeline 全链路 | ✅ |

#### 已配置模型（更新）
| 类型 | 提供商 | 模型 | 状态 |
|------|--------|------|------|
| 文本 | 阿里云通义千问 | qwen-plus | ✅ |
| 图像 | 阿里云万相 | wanx2.1-t2i-turbo | ✅ |
| 视频 | 阿里云万相 | wanx2.1-t2v-turbo | ✅ |
| 语音 | 阿里云 Qwen TTS | qwen3-tts-flash | ✅ |

#### 完整链路
```
创建项目 → 生成剧本(LLM) → 自动创建角色(DB)
                ↓
    分镜脚本(LLM→Storyboard表) + 角色三视图(多模态→Character表)
                ↓
        分镜图片生成(t2i, 本地存储)
                ↓
        分镜视频生成(t2v, 本地存储)
                ↓
        TTS 配音生成 + FFmpeg 合并
                ↓
            视频预览(/media/ 本地播放)
```

### 2026-04-26 - 剧本提示词优化与全链路修复

#### 剧本提示词 v3.0 重写
- **文件**：`src/backend/app/services/prompts.py`
- 系统提示词升级为"爆款短剧编剧大师"，融入黄金3秒法则、反转即正义、爽点密集、情绪过山车
- 爆款公式：强冲突开局→信息差→误会→反转→打脸→悬念钩子
- 硬性要求：≥3个反转、≥2次打脸、每镜头必含台词/旁白
- 新增输出字段：twist_points、hook_description、archetype
- `get_script_prompt()` 新增 `prompt_suffix` 参数

#### 视频提示词融入角色外观
- 新增 `_build_character_visual_prompt()` 和 `_enrich_video_prompt()` 函数
- `pipeline.py` 阶段5和 `storyboard.py` generate-video：视频生成前从DB加载角色外观融入提示词

#### 角色声音匹配智能化
- 新增 `_extract_dialogue_from_script()`：按索引直接查找台词（替代脆弱list.index()）
- 新增 `_match_voice_for_speaker()`：4级匹配（speaker字段→台词前缀解析→全文匹配→回退）

#### 前端加载状态优化
- ScriptWorkspace: 阶段标签（准备→AI创作→解析→保存）
- StoryboardEdit: 单镜头遮罩动画+批量X/N计数
- VideoPreview: 加载骨架状态

#### 测试结果
| 测试项 | 状态 |
|--------|------|
| 新提示词剧本生成 | ✅ 5场景、3反转、角色+台词 |
| 角色自动创建 | ✅ |
| 分镜/图片/视频/配音 | ✅ 全链路通过 |
| 前端HMR | ✅ |

---

### 2026-04-26 - 体验官评审与产品优化（v3.1）

#### 评审方式
创建两个虚拟角色迭代优化产品：
- **体验官**：全链路体验测试，输出33个问题清单
- **产品经理**：按优先级排期修复，目标"完整好用的一站式短剧平台"

#### 关键修复
| 修复 | 说明 |
|------|------|
| defineProps/defineEmits 错误导入 | CharacterModal 移除无效 vue 导入 |
| BottomNavBar 功能缺失 | 重写为上下文感知导航（返回/下一步），随页面切换 |
| ScriptWorkspace 模板错误 | 移除多余 `</div>` 导致编译失败 |
| SSE 流解析无缓冲 | 增加 buffer 累积跨帧数据，不再丢事件 |
| 前端加载状态缺失 | ScriptWorkspace/StoryboardEdit/VideoPreview 增加 loading 骨架 |
| HomeView 卡片不可点击 | 改为 `<router-link>` + 加载/错误状态 |
| API 超时太短 | axios timeout 30s → 180s |
| 视频导出假进度条 | 改为真实 API 调用 + 诚实降级提示 |
| 角色生成无错误反馈 | CharacterModal 增加错误显示 + 加载动画 |
| 无 404 页面 | 新增 NotFound.vue + 通配路由 |
| 添加角色按钮无功能 | 替换为提示文字"角色由剧本自动创建" |
| 分镜生成状态处理 | 增加 processing 中态，不再直接标记 failed |

#### 当前状态
- 后端 API 全链路通：剧本→角色→分镜→图片→视频→配音
- 前端 14 个页面全部可访问，含 404 页面
- 所有按钮和导航有实际功能
- 加载状态覆盖主要生成操作

---

### 2026-04-26 - 架构重构：漫剧平台 + 剧集化

#### 重构原因
用户纠正了对产品架构的根本理解：
- **一个分镜 = 短剧的一集**（~20s），不是单个镜头（3-8s）
- 这是**漫剧（anime short drama）**平台，不是真人短剧
- 角色必须是动漫风格，女性角色性感可爱
- 每集独立视频，各自下载，不需要最终合并导出
- 剧本可手动编辑修改

#### 变更内容

##### 1. 数据库模型扩展（database.py）
- Storyboard 表新增字段：`episode_number`、`title`、`episode_script`、`dialogue_lines`
- `duration` 默认值 5 → 20
- 保留 scene_index/shot_index 向后兼容

##### 2. 提示词全面改写（prompts.py）
- 剧本提示词：漫剧创作大师，输出 `episodes` 格式，日系动漫风
- 角色提示词：日系动漫角色设计师，女性角色性感可爱
- 生图/视频模板：anime style, 二次元, 日系动漫风, vibrant colors
- 分镜提示词：改名漫剧分集导演

##### 3. Pipeline 重构（pipeline.py）
- `generate_storyboard()` → `generate_episodes()`：每集一行 Storyboard
- 新增 `_convert_scenes_to_episodes()`：旧 scenes 格式向后兼容
- `_enrich_video_prompt()`：动漫风格质量关键词
- 配音阶段：每集一次 TTS，合并所有 dialogue_lines
- 阶段名更新：EPISODES/IMAGES 替代 STORYBOARD/SCENES

##### 4. API 端点更新（storyboard.py）
- StoryboardResponse 新增 episode_number/title/episode_script/dialogue_lines
- generate 端点：从 episodes[] 读取，回退 scenes（向后兼容）
- 查询排序：按 episode_number
- 移除导出端点（每集独立下载）

##### 5. 前端重写
- **ScriptWorkspace.vue**：编辑模式（可修改标题/对话/剧集），显示 episodes，保存剧本
- **StoryboardEdit.vue**：重写为剧集列表（垂直卡片），每集有封面预览/对话/下载按钮
- **VideoPreview.vue**：重写为剧集播放器，移除导出，每集独立下载
- **BottomNavBar.vue**："进入分镜"→"编辑剧集"，"预览视频"→"预览剧集"

##### 6. 测试更新
- test_storyboard.py：episodes 格式测试 + 旧 scenes 向后兼容测试
- test_pipeline.py：剧集生成测试 + 向后兼容测试
- 测试结果：65 passed, 1 failed（预存在问题）

#### 新架构
```
创建项目 → 生成剧本(LLM→episodes) → 自动创建动漫角色
                ↓
        生成剧集(每集1个Storyboard行)
                ↓
        每集生成封面图(anime style) + 视频(~20s)
                ↓
        每集配音(TTS + FFmpeg) → 独立下载
```

---

### 2026-04-08 - 分镜功能完善与工作流优化

#### 问题诊断
通过代码分析发现4个主要问题：
1. 剧本生成后角色未同步到数据库
2. 分镜编辑页面是占位符，无实际功能
3. 视频预览页面未实现
4. 页面间导航不完整

#### 后端优化

##### 1. Storyboard 数据模型
- **新增文件**：`src/backend/app/api/v1/endpoints/storyboard.py`
- **数据模型**：Storyboard（分镜表）
  - project_id: 关联项目
  - scene_index / shot_index: 场景和镜头索引
  - shot_type: 镜头类型（远景/全景/中景等）
  - description: 镜头描述
  - image_prompt / video_prompt: 生图/视频提示词
  - image_url / video_url: 生成的资源URL
  - duration: 时长
  - status: 状态（pending/processing/completed/failed）

##### 2. 分镜 API 端点
- `GET /storyboard/project/{project_id}` - 获取项目分镜列表
- `POST /storyboard/project/{project_id}/generate` - 从剧本生成分镜
- `POST /storyboard/{storyboard_id}/generate-image` - 生成分镜图片
- `POST /storyboard/{storyboard_id}/generate-video` - 生成分镜视频
- `DELETE /storyboard/{storyboard_id}` - 删除分镜

##### 3. 角色自动同步
- 剧本生成后自动解析 characters 字段
- 自动创建 Character 数据库记录
- 支持复杂结构（appearance/clothing 对象）

##### 4. API 路由注册
- 将 storyboard 路由注册到 `/api/v1/storyboard`

#### 前端优化

##### 1. StoryboardEdit.vue 完整实现
- 按场景分组展示分镜
- 单个镜头图片/视频生成
- 批量生成按钮
- 生成状态实时显示
- 进度统计（图片数/视频数）
- 导航：返回剧本 / 进入预览

##### 2. VideoPreview.vue 完整实现
- 视频播放器（支持单个/连续播放）
- 时间线侧边栏（按场景分组）
- 生成进度追踪
- 导出选项（分辨率/帧率/格式）
- 导出进度弹窗

##### 3. ScriptWorkspace.vue 导航优化
- 剧本生成后显示"进入分镜"按钮
- 完整流程导航：剧本 → 分镜 → 预览

##### 4. TopNavigation.vue 全局导航
- Logo + 项目列表 + 角色库链接
- 设置入口（模型配置）
- 当前路由高亮显示

##### 5. Storyboard API 封装
- **新增文件**：`src/frontend/src/api/storyboard.js`
- 封装所有分镜相关 API 调用

#### 测试完善

##### 分镜集成测试
- **新增文件**：`tests/integration/test_storyboard.py`
- 8个测试用例，全部通过
  - 空分镜列表获取
  - 从剧本生成分镜
  - 无剧本时错误处理
  - 分镜列表获取
  - 图片生成（Mock）
  - 视频生成（Mock）
  - 分镜删除
  - 404 错误处理

##### Mock 服务优化
- 新增 `mock_storyboard_image_service`
- 新增 `mock_storyboard_video_service`
- 修复 patch 路径问题

#### 完整工作流
```
创建项目 → 生成剧本 → 自动创建角色 → 进入分镜 → 生成分镜 → 生成图片/视频 → 视频预览 → 导出
```

#### 测试结果
| 测试文件 | 通过 | 总数 |
|----------|------|------|
| test_storyboard.py | 8 | 8 |

---

### 2026-04-27 - 全链路修复：视频生成、角色三视图、测试修复

#### 角色三视图端点修复
- **问题**：`characters.py` 的 `generate-three-views` 端点有重复实现，直接调用 image_service 而不下载到本地文件夹，也不更新 `three_views` 字段
- **修复**：端点改为委托 `CharacterConsistencyService.generate_three_views()`，图片现在保存到 `media/projects/{id}/characters/{name}/front|side|back.png`
- **文件**：`characters.py`

#### 视频生成模型切换
- **问题**：`wan2.7-i2v` 需要 HTTP URL 作为 `first_frame`/`driving_audio`，但本地文件路径无法被 DashScope API 访问
- **修复**：切换到 `wanx2.1-t2v-turbo`（文生视频，5s），更新 `WanxVideoService` 区分 t2v/i2v API 格式（`size` vs `resolution` 参数）
- **TTS 合并**：t2v 不支持 `driving_audio`，改用后置 FFmpeg 合并（TTS → WAV → ffmpeg merge）
- **内容审核处理**：增加 `DataInspectionFailed` 重试逻辑，自动切换清洁提示词
- **文件**：`alibaba_cloud.py`, `storyboard.py`

#### 测试修复
- `test_update_character`: age 字段改为 description 嵌套
- `test_generate_episodes` / `test_generate_from_old_scenes_format`: duration 断言 20→15
- 全部 **66 个测试通过**，0 失败

#### 文件组织
- `media/projects/` 加入 `.gitignore`，不推送生成内容
- 角色三视图目录：`characters/{name}/front.png, side.png, back.png, reference.png`
- 剧集目录：`episodes/ep{XX}/cover.png, final_with_audio.mp4`

### 2026-04-30 - 模型切换与角色形象生成修复

#### 图像/视频模型切换到火山引擎 Ark
- **图像模型**：阿里云万相 wanx2.1-t2i-turbo → 火山引擎 Seedream 4.5 (`doubao-seedream-4-5-251128`)
- **视频模型**：阿里云万相 wanx2.1-t2v-turbo → 火山引擎 Seedance 2.0 Fast (`doubao-seedance-2-0-fast-260128`)
- **API 端点**：`https://ark.cn-beijing.volces.com/api/v3`
- **新增服务**：`SeedreamImageService` → `image_service.py`（POST `/images/generations`，response_format=url）
- **Seedance**：已有 `SeedanceVideoService`，支持 base64 参考图、anime 提示词构建器、最长 15min 轮询

#### 角色形象生成全链路修复
- **问题**：生成的形象图为临时远程 URL，过期后 403；`custom_prompt` 未传递到 API
- **后端修复**：
  - `GenerateImageRequest` 新增 `custom_prompt` 字段
  - 生成的形象图自动下载到 `media/projects/{id}/characters/{name}/portrait_N.ext`
  - 提示词改为日系动漫风格（女性性感可爱，男性帅气）
- **前端修复**：
  - `CharacterModal.vue` `generateImages()` 传递 `customPrompt.value`
  - 提示词 textarea 标签更新为"图像生成提示词（可编辑）"
  - `ScriptWorkspace.vue`：SSE 完成后自动 `loadCharacters()` 刷新侧边栏
  - 角色卡片点击打开预览弹窗，关闭后刷新列表

#### 前端其他修复
- `vite.config.js`：代理端口 8010 → 8000，前端端口 8362
- `ModelConfig.vue`：新增 seedream 图像提供商选项，provider 切换自动匹配模型，base_url 表单字段
- `StoryboardEdit.vue`：移除硬编码 "Seedance" 文本，显示中文提供商名

#### 数据库修复
- `storyboards` 表新增 3 个缺失列：`image_status`、`audio_status`、`video_status`
- 模型配置更新为火山引擎 Ark 密钥和端点

#### 影响文件
| 文件 | 变更 |
|------|------|
| `characters.py` | custom_prompt 支持 + 本地下载 + 日系提示词 |
| `image_service.py` | 新增 SeedreamImageService |
| `CharacterModal.vue` | customPrompt 传递 + 提示词标签更新 + 编辑详情功能 |
| `ScriptWorkspace.vue` | 角色列表自动刷新 + 角色卡片可点击 |
| `StoryboardEdit.vue` | 提供商名中文化 |
| `ModelConfig.vue` | seedream 选项 + base_url 字段 |
| `vite.config.js` | 代理端口修正 |
| `projects.py` | character_id 生成修复 |

---

## 项目结构

```
ai-video-generator/
├── README.md            # 项目说明
├── CLAUDE.md            # 项目日志（本文件）
├── autovid.db           # SQLite 数据库（开发环境）
├── requirements.txt     # Python 依赖
├── .env                 # 环境变量（不入 git）
├── src/
│   ├── ai/              # AI模块（预留）
│   ├── backend/         # 后端服务
│   │   └── app/
│   │       ├── main.py                  # FastAPI 入口
│   │       ├── core/
│   │       │   ├── config.py            # 设置
│   │       │   └── database.py          # 数据库+模型
│   │       ├── api/v1/endpoints/        # API端点
│   │       │   ├── projects.py          # 项目管理
│   │       │   ├── characters.py        # 角色管理+三视图
│   │       │   ├── storyboard.py        # 剧集管理+视频配音
│   │       │   ├── pipeline.py          # 一键流水线
│   │       │   └── model_config.py      # 模型配置
│   │       └── services/               # AI服务层
│   │           ├── alibaba_cloud.py           # 阿里云百炼
│   │           ├── prompts.py                 # 提示词模板
│   │           ├── pipeline.py                # 生成流水线
│   │           ├── character_consistency.py   # 角色一致性
│   │           ├── video_audio_service.py     # TTS+FFmpeg
│   │           ├── media_storage.py           # 文件存储
│   │           ├── multimodal_service.py      # 多模态接口
│   │           ├── image_service.py           # 图像工厂
│   │           ├── video_service.py           # 视频工厂
│   │           ├── voice_service.py           # 语音工厂
│   │           └── llm_service.py             # LLM工厂
│   └── frontend/        # 前端界面
│       └── src/
│           ├── main.js          # 入口
│           ├── App.vue          # 根组件
│           ├── router/          # 路由配置
│           ├── api/             # API封装
│           ├── components/      # 组件
│           └── views/           # 页面视图
├── tests/               # 测试代码（66 cases）
├── docs/                # 设计文档
├── media/projects/      # 生成内容（不入 git）
└── logs/                # 运行日志
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

## 当前状态 & 已知限制

### 已实现
- [x] 剧本生成 → 角色创建 → 剧集生成 → 封面图 → 视频 → 配音 全链路通
- [x] 角色三视图（正面/侧面/背面）存到角色专属文件夹
- [x] 前端可编辑剧本、预览视频、独立下载
- [x] 66 个测试全部通过

### 已知限制
- **视频时长**: wanx2.1-t2v-turbo 最大 5 秒，无法到 20 秒目标
- **口型同步**: t2v 不支持 driving_audio，用 FFmpeg 后置合并（无口型同步）
- **内容审核**: 部分含敏感词（如"废物"）的提示词会被阿里云拦截，已加重试降级
- **DashScope API Key 区域**: 必须与 endpoint 同区域，目前用国内站

### 待完成
- [ ] 升级到 wan2.7-t2v（支持 15s + driving_audio 口型同步）— 需确认模型可用性
- [ ] 完善前端模型配置保存功能
- [ ] 实现视频到 OSS 上传，支持 i2v 的 first_frame
- [ ] 实现角色参考图引导生图（提升一致性）

---

## 本地开发环境

### 启动命令

```bash
cd /Users/a1/projects/ai-video-generator

# 启动后端 (使用虚拟环境)
PYTHONPATH=src/backend nohup venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > logs/backend.log 2>&1 &

# 启动前端
cd src/frontend
nohup npm run dev > ../../logs/frontend.log 2>&1 &
```

### 服务地址
- **前端**: http://localhost:5173/
- **后端**: http://127.0.0.1:8000/
- **API文档**: http://127.0.0.1:8000/docs

### 日志位置
- 后端日志: `logs/backend.log`
- 前端日志: `logs/frontend.log`

### 数据库
- 路径: `autovid.db`（项目根目录）
- 引擎: SQLite + aiosqlite 异步

---
