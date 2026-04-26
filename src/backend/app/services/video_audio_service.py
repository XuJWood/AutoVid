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


# Qwen TTS 可用音色
VOICE_PROFILES = {
    "Cherry": {"name": "芊悦", "gender": "female", "tone": "阳光积极女声"},
    "Ethan": {"name": "晨煦", "gender": "male", "tone": "阳光温暖男声"},
    "Jennifer": {"name": "詹妮弗", "gender": "female", "tone": "品牌级美语女声"},
    "Ryan": {"name": "甜茶", "gender": "male", "tone": "戏感炸裂男声"},
    "Katerina": {"name": "卡捷琳娜", "gender": "female", "tone": "御姐音色"},
    "Elias": {"name": "墨讲师", "gender": "male", "tone": "专业讲师男声"},
    "Nofish": {"name": "不吃鱼", "gender": "female", "tone": "设计师音色"},
    "Chelsie": {"name": "Chelsie", "gender": "female", "tone": "国际化女声"},
    "Serena": {"name": "Serena", "gender": "female", "tone": "优雅女声"},
}


def get_voice_for_character(character: Any) -> str:
    """根据角色属性选择合适的音色"""
    gender = getattr(character, "gender", None)
    age = getattr(character, "age", None)

    if gender == "male":
        if age and age >= 40:
            return "Elias"
        elif age and age >= 30:
            return "Ryan"
        else:
            return "Ethan"
    else:
        if age and age >= 40:
            return "Katerina"
        elif age and age >= 30:
            return "Serena"
        else:
            return "Cherry"


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
            format="wav",
            sample_rate=22050
        )

        if result.success:
            audio_url = result.data.get("audio_url")
            if audio_url:
                import httpx
                tmpdir = tempfile.gettempdir()
                filename = f"dialogue_{uuid.uuid4().hex[:8]}.wav"
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
            format="wav",
            sample_rate=22050
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
        local_path = os.path.join(audio_dir, f"ep{episode_number:02d}_dialogue.wav")
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
