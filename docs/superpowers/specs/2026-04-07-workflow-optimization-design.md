# AI视频生成器流程优化设计文档

| 文档版本 | 日期 | 作者 |
|---------|------|--------|
| v1.0 | 2026-04-07 | AI系统 |

## 1. 项目背景

### 1.1 当前问题

AI视频生成器项目已完成基础架构搭建，但前端到后端的流程存在多处断裂，导致用户无法完成完整的创作流程。

### 1.2 核心痛点
1. **剧本→角色断裂**: 剧本生成后，角色数据存储在 `script_content.characters` 中，未同步到 `characters` 表
2. **分镜功能缺失**: 分镜编辑页面仅为占位符
无实际功能
3. **视频生成未实现**: 视频预览和视频结果页面未调用后端API
4. **导航不完整**: 首页缺少项目列表入口，各页面缺少返回导航

### 1.3 优化目标
打通完整的创作流程：创建项目 → 生成剧本 → 角色形象 → 分镜编辑 → 视频预览 → 最终输出

---
## 2. 架构设计
### 2.1 数据流设计
```
┌──────────────────────────────────────────────────────────────────┐
│                    创建项目 (POST /projects)                          │
└──────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────┐
│                生成剧本 (POST /projects/:id/script/generate)                  │
│                返回: script_content (含 characters, scenes)                         │
└──────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────┐
│        同步创建角色 (自动创建 characters 记录)                               │
│        或: 用户手动添加角色                                          │
└──────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────┐
│              生成角色形象 (POST /characters/:id/generate-image)                 │
└──────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────┐
│               生成分镜图 (POST /projects/:id/storyboard/generate)                │
│               返回: storyboard_data (含 shots, prompts)                      │
└──────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────┐
│              生成视频 (POST /videos/generate)                                │
│              返回: video_url, status                                    │
└──────────────────────────────────────────────────────────────────┘
```
### 2.2 新增数据模型
#### Storyboard 模型
```python
class Storyboard(Base):
    __tablename__ = "storyboards"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    scene_index = Column(Integer, default=0)
    shot_index = Column(Integer, default=0)

    # 分镜数据
    shot_type = Column(String(50))  # 远景/全景/中景/近景/特写
    description = Column(Text)
    image_prompt = Column(Text)  # AI生图提示词
    video_prompt = Column(Text)  # AI生视频提示词
    duration = Column(Integer, default=5)

    # 生成的资源
    image_url = Column(String(500))
    video_url = Column(String(500))
    audio_url = Column(String(500))

    status = Column(String(50), default="pending")

    created_at = Column(DateTime, default=datetime.utcnow)
```

### 2.3 新增API端点
#### 分镜相关
- `GET /projects/:id/storyboard` - 获取项目分镜数据
- `POST /projects/:id/storyboard/generate` - 生成分镜脚本
- `POST /storyboard/:id/generate-image` - 生成分镜图
- `POST /storyboard/:id/generate-video` - 生成分镜视频

#### 视频相关
- `GET /videos/:id/status` - 查询视频生成状态
- `GET /projects/:id/videos` - 获取项目所有视频

### 2.4 娡块划分
```
frontend/
├── views/
│   ├── drama/
│   │   ├── ProjectCreate.vue     # 创建项目
│   │   ├── ScriptWorkspace.vue   # 剧本编辑 + 角色管理
│   │   ├── StoryboardEdit.vue     # 分镜编辑 (重写)
│   │   └── VideoPreview.vue       # 视频预览 (重写)
│   └── components/
│       ├── Navigation.vue          # 全局导航
│       ├── ScriptPanel.vue        # 剧本面板
│       ├── CharactersPanel.vue    # 角色面板
│       ├── StoryboardPanel.vue    # 分镜面板
│       └── VideoPlayer.vue         # 视频播放器
```
---
## 3. 功能模块详细设计
### 3.1 项目创建 (ProjectCreate.vue)
**状态**: 已实现 ✅
**无需修改**
### 3.2 剧本工作台 (ScriptWorkspace.vue)
**当前问题**:
- 岧本生成后，角色数据未同步到 characters 表
- 缺少"进入分镜"按钮
- 缺少项目状态进度指示

**修改方案**:
1. 剧本生成成功后，自动创建角色记录:
2. 添加"进入分镜"按钮（导航到 /drama/:id/storyboard）
3. 添加项目状态进度条（显示: 剧本 → 角色 → 分镜 → 视频）
4. 添加顶部导航（返回项目列表）
### 3.3 分镜编辑 (StoryboardEdit.vue)
**当前问题**: 占位页面，功能未实现
**完整重写**:
```vue
<template>
  <div class="min-h-screen pt-20 pb-8">
    <!-- 顶部导航 -->
    <nav class="fixed top-0 left-0 right-0 bg-surface z-10 px-8 h-16">
      <!-- 返回按钮 -->
      <router-link :to="`/drama/${projectId}`" class="flex items-center gap-2">
        <span class="material-symbols-outlined">arrow_back</span>
        <span class="font-bold">返回剧本</span>
      </router-link>
      <!-- 进度指示 -->
      <div class="flex items-center gap-4">
        <span class="text-xs px-3 py-1 rounded-full" :class="step >= currentStep ? 'bg-primary text-white' : 'bg-surface-container-high'">
          {{ step + 1 }}
        </span>
      </div>
      <!-- 生成视频按钮 -->
      <button @click="generateAllVideos" class="ml-auto px-4 py-2 bg-primary text-white rounded-full text-sm font-bold">
        生成全部视频
      </button>
    </nav>

    <!-- 主内容区 -->
    <div class="max-w-7xl mx-auto px-8 mt-20">
      <h1 class="text-2xl font-bold mb-6">分镜编辑</h1>

      <!-- 场景列表 -->
      <div class="space-y-6">
        <div v-for="(scene, sIndex) in scenes" :key="sIndex" class="bg-surface-container-lowest rounded-lg p-6">
          <h3 class="font-bold mb-4">{{ scene.name }}</h3>
          <p class="text-sm text-on-surface-variant mb-4">{{ scene.environment }}</p>

          <!-- 镜头列表 -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div v-for="(shot, shotIndex) in scene.shots" :key="shot.id" class="bg-surface-container-low rounded-lg overflow-hidden">
              <!-- 镜头图片/视频 -->
              <div class="aspect-video bg-surface-container">
                <img v-if="shot.image_url" :src="shot.image_url" class="w-full h-full object-cover" />
                <video v-else-if="shot.video_url" :src="shot.video_url" class="w-full h-full object-cover" loop muted />
                <div v-else class="w-full h-full flex items-center justify-center">
                  <button @click="generateShotMedia(shot)" class="px-4 py-2 bg-primary/20 text-primary rounded text-sm">
                    生成媒体
                  </button>
                </div>
              </div>
              <!-- 镜头信息 -->
              <div class="p-4">
                <div class="flex items-center gap-2 mb-2">
                  <span class="text-xs px-2 py-0.5 rounded bg-primary/20 text-primary">{{ shot.type }}</span>
                  <span class="text-xs text-on-surface-variant">{{ shot.duration }}s</span>
                </p class="text-sm">{{ shot.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
```
**核心功能**:
1. 加载项目剧本数据
2. 解析场景和镜头
3. 为每个镜头生成图片/视频
4. 支持单镜头生成和批量生成
5. 显示生成进度
### 3.4 视频预览 (VideoPreview.vue)
**当前问题**: 未实现
**完整重写**:
- 显示所有生成的视频
- 支持视频预览
- 支持视频下载
- 支持一键合成
### 3.5 导航优化
**添加顶部导航组件**:
- Logo
- 项目列表入口
- 角色库入口
- 设置入口
**添加面包屑导航**:
- 在每个页面显示当前位置
- 支持点击返回上级页面
### 3.6 数据同步机制
**剧本生成后自动创建角色**:
```python
# 在 projects.py 的 generate_script 端点中
async def generate_script(project_id: int, request: ScriptGenerateRequest, db: AsyncSession = Depends(get_db)):
    # ... 生成剧本 ...

    # 自动创建角色记录
    if script_data.get("characters"):
        for char_data in script_data["characters"]:
            character = Character(
                project_id=project_id,
                name=char_data.get("name"),
                age=char_data.get("age"),
                gender=char_data.get("gender"),
                occupation=char_data.get("occupation"),
                appearance=char_data.get("appearance", {}).get("face") if isinstance(char_data.get("appearance"), dict) else char_data.get("appearance"),
                clothing=char_data.get("clothing", {}).get("style") if isinstance(char_data.get("clothing"), dict) else char_data.get("clothing")
            )
            db.add(character)
    await db.commit()
```
---
## 4. 实现计划
### Phase 1: 数据层优化
1. 添加 Storyboard 数据模型
2. 添加分镜相关API端点
3. 修改剧本生成接口，自动创建角色
### Phase 2: 前端导航优化
1. 创建 Navigation.vue 组件
2. 在各页面集成导航
3. 添加面包屑导航
### Phase 3: 分镜编辑功能
1. 重写 StoryboardEdit.vue
2. 实现镜头列表展示
3. 实现单镜头图片/视频生成
### Phase 4: 视频预览功能
1. 重写 VideoPreview.vue
2. 实现视频列表展示
3. 实现视频合成功能
### Phase 5: 集成测试
1. 测试完整流程
2. 修复发现的问题
3. 性能优化
