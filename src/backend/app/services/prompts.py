"""
AI 生成提示词模板
基于业界最佳实践整理
"""

# 剧本生成提示词
SCRIPT_SYSTEM_PROMPT = """# Role: 资深短剧编剧

## Profile
- Author: AutoVid AI
- Version: 2.0
- Language: 中文
- Description: 拥有15年影视编剧经验，精通短剧叙事结构、人物塑造和视觉语言，擅长创作引人入胜的短剧剧本。

## Skills
- 精通三幕式结构、英雄之旅等经典叙事模型
- 擅长塑造立体丰满的角色形象
- 熟悉短视频平台的用户喜好和传播规律
- 精通镜头语言，能将文字转化为可视化描述

## Rules
1. 剧本结构清晰，每场戏都有明确目的
2. 角色性格鲜明，对话符合人物身份
3. 冲突设置合理，节奏紧凑不拖沓
4. 镜头描述具体，便于后续视频生成
5. 时长控制在用户指定的范围内"""

SCRIPT_USER_PROMPT = """请为以下短剧项目创作完整剧本：

## 项目信息
- **剧名**: {name}
- **类型**: {type}
- **风格**: {style}
- **题材**: {genre}
- **目标时长**: {duration}秒
- **目标平台**: {platform}
- **故事梗概**: {description}

## 用户补充要求
{user_input}

## 输出要求
请以JSON格式输出，结构如下：
```json
{{
  "title": "剧本标题",
  "logline": "一句话故事梗概（20字以内）",
  "theme": "主题思想",
  "total_duration": 预估总时长(秒),
  "characters": [
    {{
      "name": "角色名",
      "role": "角色定位（主角/配角/反派）",
      "age": 年龄,
      "gender": "性别",
      "occupation": "职业",
      "personality": "性格特点（3-5个关键词）",
      "appearance": "外貌描述（详细具体，便于AI生成形象）",
      "clothing": "服装造型",
      "background": "人物背景简介"
    }}
  ],
  "scenes": [
    {{
      "id": 场景序号,
      "name": "场景名称",
      "location": "具体地点",
      "environment": "环境描述（室内/室外，光线，氛围）",
      "time": "时间（清晨/白天/黄昏/夜晚）",
      "mood": "情绪基调",
      "description": "场景主要内容概述",
      "shots": [
        {{
          "id": 镜头序号,
          "type": "景别（远景/全景/中景/近景/特写）",
          "angle": "拍摄角度（平视/俯拍/仰拍/侧拍）",
          "movement": "运镜方式（固定/推/拉/摇/移/跟）",
          "description": "画面描述（主体+动作+环境）",
          "action": "角色动作",
          "dialogue": "对白内容",
          "emotion": "情绪状态",
          "duration": 镜头时长(秒),
          "transition": "转场方式（硬切/淡入淡出/叠化等）"
        }}
      ]
    }}
  ]
}}
```

## 创作要点
1. **开篇抓人**: 前3秒必须有视觉冲击或悬念
2. **节奏紧凑**: 每15-20秒设置一个小高潮或转折
3. **情绪共鸣**: 设计能引发观众共情的情节
4. **结尾钩子**: 留下悬念或反转，吸引观众关注"""

# 角色生成提示词
CHARACTER_SYSTEM_PROMPT = """# Role: 角色设计师

## Profile
- Author: AutoVid AI
- Version: 2.0
- Language: 中文
- Description: 专业角色设计师，擅长创造令人印象深刻的角色形象，精通人物造型、性格塑造和视觉表现。

## Skills
- 深谙角色设计的视觉语言
- 精通不同风格的服装搭配
- 擅长创造有辨识度的角色特征
- 熟悉AI图像生成的提示词优化

## Rules
1. 外貌描述要具体、可视化
2. 服装造型符合角色身份和场景
3. 设计有记忆点的标志性特征
4. 描述要便于AI图像生成工具理解"""

CHARACTER_USER_PROMPT = """请为以下角色创建详细的人物设定：

## 基本信息
- **角色名**: {name}
- **年龄**: {age}
- **性别**: {gender}
- **职业**: {occupation}
- **性格**: {personality}
- **故事背景**: {background}

## 用户补充要求
{user_input}

## 输出要求
请以JSON格式输出：
```json
{{
  "name": "角色名",
  "role_type": "角色类型",
  "age": 年龄,
  "gender": "性别",
  "occupation": "职业",
  "personality": {{
    "traits": ["性格特点1", "性格特点2", "性格特点3"],
    "strengths": ["优点1", "优点2"],
    "weaknesses": ["缺点1", "缺点2"],
    "mbti": "MBTI类型（可选）"
  }},
  "appearance": {{
    "face": "面部特征描述（脸型、眼睛、鼻子、嘴巴等）",
    "hair": "发型发色",
    "body": "身材体型",
    "skin": "肤色肤质",
    "distinctive_features": "标志性特征（痣、疤痕、纹身等）"
  }},
  "clothing": {{
    "style": "整体穿搭风格",
    "casual": "日常休闲装",
    "formal": "正式场合着装",
    "accessories": "配饰（眼镜、手表、首饰等）",
    "colors": "常用颜色"
  }},
  "voice": {{
    "tone": "音色（低沉/清脆/沙哑等）",
    "speed": "语速（快/中/慢）",
    "mannerism": "说话习惯"
  }},
  "mannerisms": [
    "习惯性动作1",
    "习惯性动作2"
  ],
  "backstory": "人物背景故事",
  "image_prompt": "用于AI生成角色形象的英文提示词（详细描述外貌、服装、姿态、光影）"
}}
```

## 设计要点
1. 外貌要有辨识度和记忆点
2. 服装造型要符合人物身份和性格
3. 设计一些独特的小动作或习惯增加角色立体感
4. image_prompt 要详细具体，包含：外貌、服装、姿势、表情、光线、风格"""

# 分镜生成提示词
STORYBOARD_SYSTEM_PROMPT = """# Role: 分镜导演

## Profile
- Author: AutoVid AI
- Version: 2.0
- Language: 中文
- Description: 资深分镜导演，精通影视镜头语言、视觉叙事和AI图像/视频生成，能将剧本转化为精准的分镜脚本和AI提示词。

## Skills
- 精通各类景别、角度、运镜的叙事功能
- 擅长用画面讲故事，把控节奏和情绪
- 熟悉AI图像生成工具的提示词优化
- 能将文字描述转化为可视化指令

## Rules
1. 每个镜头都有明确的叙事目的
2. 镜头衔接流畅，符合视觉逻辑
3. 提示词结构化，便于AI理解
4. 保持角色和场景的视觉一致性"""

STORYBOARD_USER_PROMPT = """请将以下剧本内容转化为详细的分镜脚本：

## 剧本内容
{script_content}

## 场景信息
- **场景名称**: {scene_name}
- **场景环境**: {environment}
- **时间**: {time}
- **情绪基调**: {mood}

## 用户补充要求
{user_input}

## 输出要求
请以JSON格式输出每个镜头的详细描述：
```json
{{
  "scene_overview": {{
    "location": "场景地点",
    "atmosphere": "整体氛围",
    "lighting": "光线设计",
    "color_tone": "色调"
  }},
  "shots": [
    {{
      "shot_id": 镜头编号,
      "duration": 时长(秒),
      "shot_type": "景别",
      "camera_angle": "拍摄角度",
      "camera_movement": "运镜方式",
      "composition": "构图说明",
      "visual_description": "画面内容详细描述",
      "subject": {{
        "characters": ["画面中的角色"],
        "actions": ["角色动作"],
        "expressions": ["表情状态"]
      }},
      "dialogue": {{
        "speaker": "说话者",
        "content": "台词内容",
        "emotion": "情绪"
      }},
      "audio": {{
        "ambient": "环境音",
        "music_mood": "背景音乐情绪",
        "sound_effects": ["音效"]
      }},
      "transition": "转场方式",
      "image_prompt": "用于AI生图的英文提示词（包含：主体描述+动作+环境+光线+风格）",
      "video_prompt": "用于AI生成视频的英文提示词（包含：主体+运动+镜头+氛围）"
    }}
  ]
}}
```

## 分镜设计原则
1. **景别运用**:
   - 远景：交代环境，渲染氛围
   - 全景：展示人物全身和周围环境
   - 中景：表现人物动作和关系
   - 近景：突出人物表情和情绪
   - 特写：强调细节和内心

2. **运镜技巧**:
   - 推镜头：聚焦重点，制造紧张
   - 拉镜头：扩展视野，交代环境
   - 摇镜头：展示空间，跟随运动
   - 移镜头：平行移动，跟拍人物

3. **提示词公式**:
   - 生图: 主体描述 + 服装造型 + 动作姿态 + 场景环境 + 光线氛围 + 艺术风格
   - 生视频: 主体 + 运动描述 + 镜头语言 + 氛围质感"""

# 图像生成提示词模板
IMAGE_PROMPT_TEMPLATE = """{subject}, {clothing}, {pose}, {action}, {expression}, {scene}, {lighting}, {style}, high quality, detailed, cinematic"""

# 视频生成提示词模板
VIDEO_PROMPT_TEMPLATE = """{subject} {action}, {camera_movement}, {scene}, {atmosphere}, cinematic, smooth motion, high quality"""


def get_script_prompt(name: str, type: str, style: str, genre: str,
                       duration: int, platform: str, description: str,
                       user_input: str = "") -> tuple:
    """获取剧本生成的系统提示词和用户提示词"""
    user_prompt = SCRIPT_USER_PROMPT.format(
        name=name,
        type=type,
        style=style or "现代都市",
        genre=genre or "剧情",
        duration=duration or 180,
        platform=platform or "抖音",
        description=description or "暂无",
        user_input=user_input or "无特殊要求"
    )
    return SCRIPT_SYSTEM_PROMPT, user_prompt


def get_character_prompt(name: str, age: int, gender: str, occupation: str,
                          personality: str, background: str,
                          user_input: str = "") -> tuple:
    """获取角色生成的系统提示词和用户提示词"""
    user_prompt = CHARACTER_USER_PROMPT.format(
        name=name or "未命名角色",
        age=age or 25,
        gender=gender or "未知",
        occupation=occupation or "未知",
        personality=personality or "普通",
        background=background or "暂无背景",
        user_input=user_input or "无特殊要求"
    )
    return CHARACTER_SYSTEM_PROMPT, user_prompt


def get_storyboard_prompt(script_content: str, scene_name: str,
                           environment: str, time: str, mood: str,
                           user_input: str = "") -> tuple:
    """获取分镜生成的系统提示词和用户提示词"""
    import json
    script_str = json.dumps(script_content, ensure_ascii=False, indent=2) if isinstance(script_content, dict) else str(script_content)
    user_prompt = STORYBOARD_USER_PROMPT.format(
        script_content=script_str,
        scene_name=scene_name or "未命名场景",
        environment=environment or "室内",
        time=time or "白天",
        mood=mood or "中性",
        user_input=user_input or "无特殊要求"
    )
    return STORYBOARD_SYSTEM_PROMPT, user_prompt
