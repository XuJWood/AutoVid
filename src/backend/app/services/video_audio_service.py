"""
Video Audio Service
为生成的视频提供配音：
  - Qwen TTS 生成角色语音（返回 DashScope OSS URL + 本地文件）
  - wan2.7-i2v driving_audio 实现口型同步（AI 自动处理）
  - FFmpeg 合并保留用于兼容 / 离线合成
"""
import os
import uuid
import asyncio
import tempfile
from typing import Optional, Dict, Any, List, Tuple

from .alibaba_cloud import CosyVoiceService
from .media_storage import get_project_video_dir, get_audio_dir, _generate_filename, download_and_save_video


# Qwen TTS 可用音色 — 含性别/性格/年龄匹配信息
VOICE_PROFILES = {
    # 女声
    "Cherry":    {"name": "芊悦",   "gender": "female", "age_range": (16, 28),  "personality": "阳光,活泼,甜妹,元气",        "tone": "清脆甜美的元气少女音"},
    "Jennifer":  {"name": "詹妮弗", "gender": "female", "age_range": (20, 35),  "personality": "干练,知性,成熟,优雅",        "tone": "流畅知性的国际化女声"},
    "Katerina":  {"name": "卡捷琳娜","gender": "female","age_range": (25, 45),  "personality": "高冷,强势,御姐,腹黑,反派",   "tone": "低沉性感的御姐音"},
    "Nofish":    {"name": "不吃鱼", "gender": "female", "age_range": (18, 30),  "personality": "文艺,温柔,安静,清新",        "tone": "轻柔文艺的设计师音色"},
    "Chelsie":   {"name": "Chelsie","gender": "female", "age_range": (20, 40),  "personality": "自信,大方,国际化,精英",      "tone": "自信大气的国际化女声"},
    "Serena":    {"name": "Serena", "gender": "female", "age_range": (25, 40),  "personality": "温柔,优雅,成熟,知性",        "tone": "温柔优雅的成熟女声"},
    "Jada":      {"name": "Jada",   "gender": "female", "age_range": (18, 30),  "personality": "活泼,俏皮,可爱,甜美",        "tone": "俏皮可爱的少女音"},
    "Sunny":     {"name": "Sunny",  "gender": "female", "age_range": (16, 25),  "personality": "元气,开朗,青春,阳光",        "tone": "阳光开朗的青春女声"},
    # 男声
    "Ethan":     {"name": "晨煦",   "gender": "male",   "age_range": (16, 28),  "personality": "开朗,温暖,阳光,邻家",        "tone": "阳光温暖的少年音"},
    "Ryan":      {"name": "甜茶",   "gender": "male",   "age_range": (20, 35),  "personality": "深情,温柔,帅气,男主",        "tone": "温柔深情的男主音"},
    "Elias":     {"name": "墨讲师", "gender": "male",   "age_range": (30, 55),  "personality": "沉稳,专业,权威,导师",        "tone": "沉稳专业的成熟男声"},
    "Dylan":     {"name": "Dylan",  "gender": "male",   "age_range": (20, 35),  "personality": "潇洒,不羁,痞帅,玩世不恭",    "tone": "潇洒不羁的低沉男声"},
    "Marcus":    {"name": "Marcus", "gender": "male",   "age_range": (25, 45),  "personality": "霸道,冷酷,强势,总裁",        "tone": "霸道总裁式的低沉男声"},
    "Roy":       {"name": "Roy",    "gender": "male",   "age_range": (18, 30),  "personality": "热血,冲动,正义,少年",        "tone": "热血激昂的少年音"},
    "Peter":     {"name": "Peter",  "gender": "male",   "age_range": (20, 35),  "personality": "幽默,风趣,暖男,搞笑",        "tone": "幽默风趣的暖男音"},
    "Rocky":     {"name": "Rocky",  "gender": "male",   "age_range": (20, 40),  "personality": "坚韧,硬汉,力量,刚毅",        "tone": "坚韧有力的硬汉音"},
}


def _normalize_gender(gender: str) -> str:
    """标准化性别字符串 → male / female / unknown"""
    if not gender:
        return "unknown"
    g = str(gender).strip().lower()
    if g in ("男", "male", "男性", "boy", "man", "m"):
        return "male"
    if g in ("女", "female", "女性", "girl", "woman", "f"):
        return "female"
    return "unknown"


def _match_voice_by_personality(personality: str, gender: str) -> Optional[str]:
    """根据性格关键词匹配音色，返回最佳匹配音色名"""
    if not personality:
        return None
    p = str(personality).lower()
    best = None
    best_score = 0
    for voice_name, profile in VOICE_PROFILES.items():
        if profile["gender"] != gender:
            continue
        score = 0
        for kw in profile["personality"].split(","):
            if kw.strip() in p:
                score += 1
        if score > best_score:
            best_score = score
            best = voice_name
    return best if best_score >= 1 else None


def get_voice_for_character(character: Any) -> str:
    """根据角色性别+年龄+性格智能匹配音色"""
    gender = _normalize_gender(getattr(character, "gender", None))
    age = getattr(character, "age", None)
    personality = getattr(character, "personality", None)

    if gender == "male":
        # 先尝试性格匹配
        if personality:
            matched = _match_voice_by_personality(personality, "male")
            if matched:
                return matched
        # 回退到年龄匹配
        if age and age >= 40:
            return "Elias"
        elif age and age >= 28:
            return "Ryan"
        elif age and age >= 20:
            return "Dylan"
        else:
            return "Ethan"
    elif gender == "female":
        if personality:
            matched = _match_voice_by_personality(personality, "female")
            if matched:
                return matched
        if age and age >= 40:
            return "Katerina"
        elif age and age >= 28:
            return "Serena"
        elif age and age >= 20:
            return "Jennifer"
        else:
            return "Cherry"
    else:
        # 未知性别：用文本特征推测
        if personality:
            for g in ("female", "male"):
                matched = _match_voice_by_personality(personality, g)
                if matched:
                    return matched
        return "Cherry"  # 最终默认


async def generate_dialogue_audio(
    text: str,
    voice: str = "Cherry",
    api_key: str = None,
    speed: float = 1.0,
    volume: int = 50
) -> Optional[str]:
    """使用 Qwen TTS 为台词生成语音，下载到本地，返回文件路径"""
    if not text or not api_key:
        return None

    try:
        service = CosyVoiceService(api_key=api_key, model="qwen3-tts-flash", voice=voice)
        result = await service.generate(
            text=text,
            voice=voice,
            format="mp3",
            sample_rate=48000
        )

        if result.success:
            audio_url = result.data.get("audio_url")
            if audio_url:
                import httpx
                tmpdir = tempfile.gettempdir()
                filename = f"dialogue_{uuid.uuid4().hex[:8]}.mp3"
                filepath = os.path.join(tmpdir, filename)
                async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
                    resp = await client.get(audio_url)
                    if resp.status_code == 200:
                        with open(filepath, "wb") as f:
                            f.write(resp.content)
                        return filepath
        else:
            print(f"TTS failed: {result.error}")
    except Exception as e:
        print(f"TTS error: {e}")

    return None


async def generate_dialogue_audio_data(
    text: str,
    voice: str = "Cherry",
    api_key: str = None,
) -> Optional[Dict[str, Any]]:
    """使用 Qwen TTS 生成语音，返回 {audio_url, local_path, voice} 字典

    audio_url 是 DashScope OSS URL，可直接作为 wan2.7-i2v 的 driving_audio。
    """
    if not text or not api_key:
        return None

    try:
        service = CosyVoiceService(api_key=api_key, model="qwen3-tts-flash", voice=voice)
        result = await service.generate(
            text=text,
            voice=voice,
            format="mp3",
            sample_rate=48000
        )

        if result.success:
            oss_url = result.data.get("audio_url")
            if oss_url:
                return {
                    "audio_url": oss_url,
                    "voice": voice,
                    "text": text
                }
        else:
            print(f"TTS failed: {result.error}")
    except Exception as e:
        print(f"TTS error: {e}")

    return None


async def build_episode_dialogue_audio(
    dialogue_lines: list,
    characters: list,
    api_key: str,
    project_id: int,
    episode_number: int
) -> Optional[Dict[str, Any]]:
    """
    为剧集构建完整配音。
    遍历 dialogue_lines，逐角色匹配音色，合并台词后一次 TTS 生成。

    Returns:
        {"audio_url": "...", "voice": "...", "local_path": "..."}
        或 None
    """
    if not dialogue_lines or not api_key:
        return None

    # Build character name → voice mapping
    char_voices = {}
    for c in characters:
        char_voices[c.name] = get_voice_for_character(c)

    # Determine primary voice (most frequent speaker)
    speaker_count = {}
    for d in dialogue_lines:
        speaker = d.get("speaker", "") if isinstance(d, dict) else ""
        if speaker:
            speaker_count[speaker] = speaker_count.get(speaker, 0) + 1
    primary_speaker = max(speaker_count, key=speaker_count.get) if speaker_count else None
    voice = char_voices.get(primary_speaker, "Cherry") if primary_speaker else "Cherry"

    # Build merged dialogue text
    parts = []
    for d in dialogue_lines:
        if isinstance(d, dict):
            speaker = d.get("speaker", "")
            text = d.get("text", "")
            parts.append(f"{speaker}: {text}" if speaker else text)
        elif isinstance(d, str):
            parts.append(d)

    dialogue_text = "。".join(parts)
    if not dialogue_text:
        return None

    result = await generate_dialogue_audio_data(
        text=dialogue_text,
        voice=voice,
        api_key=api_key
    )

    if result:
        # Also download to project audio dir for safekeeping
        audio_dir = get_audio_dir(project_id)
        local_path = os.path.join(audio_dir, f"ep{episode_number:02d}_dialogue.mp3")
        try:
            import httpx
            async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
                resp = await client.get(result["audio_url"])
                if resp.status_code == 200:
                    with open(local_path, "wb") as f:
                        f.write(resp.content)
                    result["local_path"] = local_path
        except Exception as e:
            print(f"Failed to download dialogue audio: {e}")

    return result


# ────────────────────────────────
# Legacy FFmpeg merge (kept for compatibility)
# ────────────────────────────────

async def merge_video_audio(
    video_path: str,
    audio_path: str,
    output_path: str
) -> Optional[str]:
    """使用 FFmpeg 合并视频和音频到指定输出路径"""
    if not video_path or not audio_path:
        return None

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-map", "0:v:0",
            "-map", "1:a:0",
            output_path
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0 and os.path.exists(output_path):
            return output_path
        else:
            print(f"FFmpeg merge failed: {stderr.decode()[:200]}")
            return None
    except Exception as e:
        print(f"FFmpeg error: {e}")
        return None


async def add_audio_to_video(
    video_url: str,
    dialogue: str,
    voice: str,
    project_id: int,
    api_key: str,
    shot_prefix: str = "shot"
) -> Optional[str]:
    """
    一站式：给视频加配音（FFmpeg 方式，旧版兼容）
    1. 下载视频到本地
    2. 生成 TTS 音频
    3. FFmpeg 合并
    4. 返回最终视频路径

    新流程推荐使用 wan2.7-i2v 的 driving_audio 实现口型同步。
    """
    if not dialogue or not api_key:
        return None

    if video_url.startswith("http://") or video_url.startswith("https://"):
        local_video = await download_and_save_video(video_url, project_id, prefix=shot_prefix)
        if not local_video:
            print(f"Failed to download video for audio merge: {video_url}")
            return None
    else:
        local_video = video_url
        if not os.path.exists(local_video):
            print(f"Local video file not found: {local_video}")
            return None

    audio_path = await generate_dialogue_audio(dialogue, voice=voice, api_key=api_key)
    if not audio_path:
        print(f"Failed to generate audio for dialogue: {dialogue[:50]}")
        return None

    output_dir = get_project_video_dir(project_id)
    output_filename = _generate_filename(f"{shot_prefix}_audio", "mp4")
    output_path = os.path.join(output_dir, output_filename)

    merged_path = await merge_video_audio(local_video, audio_path, output_path)

    try:
        os.remove(audio_path)
    except Exception:
        pass

    return merged_path
