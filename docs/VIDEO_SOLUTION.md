# AutoVid 视频生成优化方案报告

> 日期: 2026-04-28
> 环境: lg_1.0 (Python 3.11), DashScope API Key: `sk-21ba...c22`

---

## 一、现状诊断

### 1.1 当前配置问题

| 项目 | 当前值 | 问题 |
|------|--------|------|
| 视频 provider | `kling` (可灵AI) | ❌ 用了别人的 API 服务，DashScope Key 根本调不通 |
| 视频 model | `null` | ❌ 没指定模型 |
| 代码默认模型 | `wan2.7-i2v` → `wan2.7-t2v` | ❌ 刚被我切成了 t2v，但你需要的是图生视频 |
| 旧版支持 | `wanx2.1-t2v-turbo` | ❌ 只支持 5 秒，无音频，无口型 |

### 1.2 核心需求

> **封面图 + 角色形象 + TTS 对话音频 → 15秒带口型的日系动漫视频**

这是典型的 **Image-to-Video + Audio-driven Lip Sync** 场景。

---

## 二、API Key 验证结果

| 检测项 | 状态 | 说明 |
|--------|------|------|
| Key 有效性 | ✅ 正常 | sk-21ba1b4765eb4e64b8e5b2261ae82c22 |
| wanx2.1-t2v-turbo | ✅ 可用 | 5s 文生视频，生成的猫视频质量不错 |
| wan2.7-t2v | ✅ 可用 | 15s 文生视频，1080P，音频驱动 |
| wan2.7-i2v | ✅ 可用 | 图生视频，需 first_frame + driving_audio |
| HappyHorse-1.0 | ❌ 暂无权限 | 4.27 刚上架，企业白名单阶段，预计 4.30 全面开放 |

---

## 三、推荐方案：wan2.7-i2v

### 3.1 为什么选它

| 能力 | wanx2.1-t2v (旧) | wan2.7-t2v | **wan2.7-i2v** | HappyHorse |
|------|:--:|:--:|:--:|:--:|
| 视频时长 | 5s | 2-15s | **2-15s** ✅ | 2-15s |
| 分辨率 | 720P | 1080P | **1080P** ✅ | 1080P |
| 图生视频 | ❌ | ❌ | **✅ first_frame** | ✅ |
| 音频驱动 | ❌ | 自动配乐 | **✅ 口型同步** | ✅ |
| 多镜头叙事 | ❌ | ✅ | ✅ | ✅ |
| 当前可用 | ✅ | ✅ | **✅** | ❌ 白名单 |
| 价格 | 低 | 中 | 中 | 高 (1.6元/s) |

**wan2.7-i2v 的 i2v + driving_audio 模式正好匹配你的流程：**
- `media[first_frame]` = 剧集封面图（日系动漫风格）
- `media[driving_audio]` = TTS 对白音频（Qwen TTS 生成的 OSS URL）
- 模型会自动做口型同步，输出带配音的 15 秒视频

### 3.2 HappyHorse 待后续接入

HappyHorse 是阿里 ATH 最新模型，效果应该更好（人像真实感强、运镜流畅），但目前白名单限制。建议 4.30 全面开放后立即测试接入，预计只需要改 model name 和 adapt media format（`first_frame` → `image_url`）。

---

## 四、已完成的代码修改

### 4.1 `alibaba_cloud.py` — WanxVideoService 重写

**文件**: `src/backend/app/services/alibaba_cloud.py:248-398`

改动要点：
- 新增 `_is_new_gen` 属性识别 wan2.5/2.6/2.7 系列
- wan2.7+ t2v: 使用 `resolution` + `ratio` + `duration` 参数格式
- wan2.7+ i2v: 使用 `resolution` + `duration` + `media` 格式
- wanx2.1 旧版: 保持 `size` 参数兼容
- 新增 `negative_prompt` 支持
- `max_wait` 动态计算: `max(900, duration * 60)` 秒
- 返回 `actual_prompt` 字段（AI 改写后的 prompt）

### 4.2 `video_service.py` — 工厂默认模型

**文件**: `src/backend/app/services/video_service.py:314`

```python
model = kwargs.pop("model", None) or "wan2.7-t2v"
```

### 4.3 `config.py` — 新增 DashScope 配置

**文件**: `src/backend/app/core/config.py:36-37`

```python
DASHSCOPE_API_KEY: str = ""
DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
```

### 4.4 数据库 model_configs

| name | provider | model | api_key | status |
|------|----------|-------|---------|--------|
| image | qwen-image | wanx2.1-t2i-turbo | ✅ 正确 | active |
| voice | cosyvoice | null | ✅ 正确 | active |
| **video** | **wanx** | **wan2.7-i2v** | ✅ 正确 | active |
| text | qwen | null | ✅ 正确 | active |

---

## 五、完整调用链路

```
用户输入 → 剧本生成 (qwen-plus)
           ↓
       角色生成 (qwen-plus) → 角色形象图 (wanx2.1-t2i-turbo)
           ↓
       剧集拆分 → 每集一个 Storyboard 行
           ↓
       剧集封面生成 (wanx2.1-t2i-turbo, 融入角色外观 prompt)
           ↓
       对白 TTS (Qwen TTS) → 返回 DashScope OSS URL
           ↓
  ┌─ wan2.7-i2v ──────────────────────────────────────┐
  │  input.prompt:    日系动漫风 prompt                 │
  │  input.media[0]:  first_frame = 剧集封面图          │
  │  input.media[1]:  driving_audio = TTS OSS URL      │
  │  parameters:      resolution=720P, duration=15     │
  └────────────────────────────────────────────────────┘
           ↓
       口型同步的 15 秒动漫视频 (mp4)
```

### i2v API 请求格式

```json
{
    "model": "wan2.7-i2v",
    "input": {
        "prompt": "日系动漫风，二次元...",
        "media": [
            {"type": "first_frame", "url": "https://...封面图.jpg"},
            {"type": "driving_audio", "url": "https://...TTS音频.wav"}
        ]
    },
    "parameters": {
        "resolution": "720P",
        "duration": 15,
        "prompt_extend": true
    }
}
```

---

## 六、注意事项

1. **音频 URL 必须是公网可访问的 HTTP URL** — Qwen TTS 返回的 DashScope OSS URL 满足此条件，有效期内可用
2. **首帧图片宽高比** — 建议 16:9，分辨率 ≥ 300px，≤ 10MB
3. **轮询超时** — 15秒视频预计耗时 3-8 分钟，代码已按 `duration * 60` 动态计算轮询时间
4. **video_url 有效期 24 小时** — 必须在此时间内下载到本地 media/ 目录
5. **价格** — wan2.7-i2v 按 duration 和 resolution 计费，建议开发阶段用 720P

---

## 七、后续优化方向

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | HappyHorse 接入 | 4.30 开放后立即测试，预期质量提升显著 |
| P1 | 多角色多音色对白 | 当前是合并对白单一音色，可改为逐句分角色 TTS |
| P2 | 视频后处理 | 加字幕、转场效果、片头片尾 |
| P3 | 本地音频缓存 | TTS 结果缓存避免重复生成 |
| P4 | 流式预览 | 生成中提供中间帧预览 |
