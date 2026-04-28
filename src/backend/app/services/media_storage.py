"""
Media Storage Service
Organized directory structure:
  media/projects/{project_id}/
    characters/{name}/front.png, side.png, back.png
    episodes/ep{XX}/cover.png, video.mp4, final.mp4
    audio/
"""
import os
import uuid
import aiofiles
import httpx
from typing import Optional
from datetime import datetime


PROJECTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "media", "projects")
PROJECTS_DIR = os.path.abspath(PROJECTS_DIR)


def get_project_image_dir(project_id: int) -> str:
    """（旧版兼容）获取项目图片目录"""
    path = os.path.join(PROJECTS_DIR, str(project_id), "images")
    os.makedirs(path, exist_ok=True)
    return path


def get_project_video_dir(project_id: int) -> str:
    """（旧版兼容）获取项目视频目录"""
    path = os.path.join(PROJECTS_DIR, str(project_id), "videos")
    os.makedirs(path, exist_ok=True)
    return path


def get_character_dir(project_id: int, character_name: str) -> str:
    """获取角色专属文件夹"""
    safe_name = "".join(c for c in character_name if c.isalnum() or c in "._- ").strip()
    if not safe_name:
        safe_name = "unknown"
    path = os.path.join(PROJECTS_DIR, str(project_id), "characters", safe_name)
    os.makedirs(path, exist_ok=True)
    return path


def get_episode_dir(project_id: int, episode_number: int) -> str:
    """获取剧集专属文件夹"""
    path = os.path.join(PROJECTS_DIR, str(project_id), "episodes", f"ep{episode_number:02d}")
    os.makedirs(path, exist_ok=True)
    return path


def get_audio_dir(project_id: int) -> str:
    """获取音频临时文件夹"""
    path = os.path.join(PROJECTS_DIR, str(project_id), "audio")
    os.makedirs(path, exist_ok=True)
    return path


def _generate_filename(prefix: str, ext: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:8]
    return f"{prefix}_{ts}_{uid}.{ext}"


def _guess_ext(url: str, default: str = "png") -> str:
    url_lower = url.split("?")[0]
    for ext in ["png", "jpg", "jpeg", "gif", "webp", "mp4", "mov", "webm"]:
        if url_lower.endswith(f".{ext}"):
            return ext
    return default


def local_path_to_url(filepath: str) -> str:
    """将本地绝对路径转为 /media/... 可访问 URL"""
    if not filepath:
        return ""
    rel = os.path.relpath(filepath, os.path.join(PROJECTS_DIR, ".."))
    return f"/media/{rel}"


async def download_and_save_image(
    url: str,
    project_id: int,
    prefix: str = "img"
) -> Optional[str]:
    """下载图片到项目 images/ 目录（旧版兼容）"""
    if not url:
        return None
    ext = _guess_ext(url, "png")
    filename = _generate_filename(prefix, ext)
    filepath = os.path.join(get_project_image_dir(project_id), filename)
    try:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                async with aiofiles.open(filepath, "wb") as f:
                    await f.write(response.content)
                return filepath
    except Exception as e:
        print(f"Failed to download image from {url}: {e}")
    return None


async def save_image_to_path(url: str, filepath: str) -> Optional[str]:
    """下载图片到指定路径"""
    if not url:
        return None
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    try:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                async with aiofiles.open(filepath, "wb") as f:
                    await f.write(response.content)
                return filepath
    except Exception as e:
        print(f"Failed to download image from {url}: {e}")
    return None


async def download_and_save_video(
    url: str,
    project_id: int,
    prefix: str = "vid"
) -> Optional[str]:
    """下载视频到项目 videos/ 目录（旧版兼容）"""
    if not url:
        return None
    ext = _guess_ext(url, "mp4")
    filename = _generate_filename(prefix, ext)
    filepath = os.path.join(get_project_video_dir(project_id), filename)
    try:
        async with httpx.AsyncClient(timeout=600.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                async with aiofiles.open(filepath, "wb") as f:
                    await f.write(response.content)
                return filepath
    except Exception as e:
        print(f"Failed to download video from {url}: {e}")
    return None


async def save_video_to_path(url: str, filepath: str) -> Optional[str]:
    """下载视频到指定路径"""
    if not url:
        return None
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    try:
        async with httpx.AsyncClient(timeout=600.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                async with aiofiles.open(filepath, "wb") as f:
                    await f.write(response.content)
                return filepath
    except Exception as e:
        print(f"Failed to download video from {url}: {e}")
    return None


async def get_local_image_url(filepath: str) -> str:
    """将本地路径转为可访问的URL"""
    return local_path_to_url(filepath)
