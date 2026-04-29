"""
Seedance 2.0 Video Service — Volcano Engine Ark API
Doubao Seedance 2.0: text+image → video with embedded audio

API Schema reference:
  POST https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks
  Body:
    {
      "model": "doubao-seedance-2-0-260128",
      "content": [
        {"type": "text", "text": "<prompt> --resolution 1080p --duration 15 --ratio 16:9"},
        {"type": "image_url", "image_url": {"url": "<reference_image>"}}  # optional, for i2v
      ]
    }
  Response (create): {"id": "cgt-xxxx"}
  GET /tasks/{id} → {"id":"...", "status":"queued|running|succeeded|failed", "content":{"video_url":"..."}}
"""
import asyncio
import base64
import json
import os
import re
from urllib.parse import urlparse
import httpx
from typing import Optional, Dict, Any

from .base import BaseAIService, GenerationResult
from .media_storage import get_episode_dir, save_video_to_path, local_path_to_url


# ──────────────────────────────────────────────
# Image URL normalization for Ark API
# ──────────────────────────────────────────────

_LOCAL_HOST_PATTERN = re.compile(r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)", re.I)


def _guess_mime(path: str) -> str:
    p = path.lower().split("?")[0]
    if p.endswith(".jpg") or p.endswith(".jpeg"):
        return "image/jpeg"
    if p.endswith(".webp"):
        return "image/webp"
    if p.endswith(".gif"):
        return "image/gif"
    return "image/png"


def _file_to_data_url(file_path: str) -> Optional[str]:
    """Convert a local file to a base64 data URL."""
    try:
        if not os.path.isfile(file_path):
            return None
        with open(file_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        mime = _guess_mime(file_path)
        return f"data:{mime};base64,{b64}"
    except Exception as e:
        print(f"[seedance] _file_to_data_url failed for {file_path}: {e}")
        return None


def _resolve_local_path_from_media_url(media_url: str) -> Optional[str]:
    """Resolve /media/... URL to absolute filesystem path under PROJECTS_DIR/.."""
    from .media_storage import PROJECTS_DIR
    parsed = urlparse(media_url) if media_url.startswith("http") else None
    rel = parsed.path if parsed else media_url
    # Strip leading /media/
    if rel.startswith("/media/"):
        rel = rel[len("/media/"):]
    elif rel.startswith("media/"):
        rel = rel[len("media/"):]
    full = os.path.join(os.path.dirname(PROJECTS_DIR), "media", rel)
    full = os.path.normpath(full)
    return full if os.path.isfile(full) else None


def normalize_image_url_for_ark(image_url: str) -> Optional[str]:
    """Normalize an image reference for Ark API consumption.

    Ark needs a publicly-downloadable URL OR a base64 data URL. This helper:
    - Passes through public HTTP(S) URLs that aren't localhost
    - Converts local file paths → base64 data URL
    - Converts /media/... or http://localhost/media/... → resolve local file → base64
    - Returns None if the image cannot be resolved (caller should skip the ref)
    """
    if not image_url:
        return None
    # Already a base64 data URL
    if image_url.startswith("data:"):
        return image_url
    # Local filesystem absolute path
    if image_url.startswith("/") and not image_url.startswith("/media/"):
        return _file_to_data_url(image_url)
    # /media/... relative URL → resolve to local file
    if image_url.startswith("/media/"):
        local = _resolve_local_path_from_media_url(image_url)
        return _file_to_data_url(local) if local else None
    # HTTP URL pointing at localhost / private IPs → resolve to local file via /media path
    if _LOCAL_HOST_PATTERN.match(image_url):
        # Extract /media/... portion
        idx = image_url.find("/media/")
        if idx != -1:
            local = _resolve_local_path_from_media_url(image_url[idx:])
            return _file_to_data_url(local) if local else None
        return None  # localhost URL without /media/ — skip
    # Public HTTP URL — pass through (Ark will download it)
    if image_url.startswith("http://") or image_url.startswith("https://"):
        return image_url
    # Unknown format
    return None


# ──────────────────────────────────────────────
# Anime video prompt builder
# ──────────────────────────────────────────────

ANIME_QUALITY_TAGS = (
    "Japanese anime style, 日系动漫风, 二次元, anime cinematic style, "
    "smooth fluid animation, vibrant saturated colors, dynamic lighting, "
    "detailed background art, expressive character design, sharp clean linework, "
    "high quality 4K anime, masterpiece"
)

CAMERA_MOVEMENT_HINTS = {
    "推": "slow dolly-in pushing toward subject",
    "拉": "slow dolly-out pulling back to reveal scene",
    "摇": "horizontal pan revealing the environment",
    "移": "lateral tracking shot",
    "跟": "tracking shot following the character's motion",
    "固定": "fixed steady shot, no camera movement",
    "急摇": "quick whip pan with motion blur",
    "升": "crane up, camera rises smoothly",
    "降": "crane down, camera lowers smoothly",
    "推/固定": "subtle dolly-in to fixed shot",
    "fixed": "fixed steady shot, no camera movement",
    "pan": "smooth horizontal pan",
    "tracking": "tracking shot following the action",
    "dolly": "dolly movement creating depth",
    "zoom": "smooth zoom",
}


def build_seedance_anime_prompt(
    visual_description: str,
    camera_movement: str = "fixed",
    dialogue: str = "",
    emotion: str = "",
) -> str:
    """Build a high-quality anime video prompt for Seedance 2.0.

    Structure: visual subject → action → camera → atmosphere → quality tags → audio cue
    The model parses the front of the prompt as primary visual content,
    so the most important visual elements come first.
    """
    parts = []

    if visual_description:
        parts.append(visual_description.strip().rstrip(",."))

    cam_hint = CAMERA_MOVEMENT_HINTS.get(camera_movement, camera_movement) if camera_movement else ""
    if cam_hint:
        parts.append(f"camera: {cam_hint}")

    if emotion:
        parts.append(f"mood: {emotion}")

    parts.append(ANIME_QUALITY_TAGS)

    if dialogue:
        clean_dialogue = dialogue.replace('"', "'").strip()
        parts.append(f"the character speaks the line: \"{clean_dialogue}\" with matching lip-sync and natural anime voice acting")

    return ", ".join(p for p in parts if p)


# ──────────────────────────────────────────────
# Seedance Video Service
# ──────────────────────────────────────────────

class SeedanceVideoService(BaseAIService):
    """Seedance 2.0 video generation via Volcano Engine Ark API."""

    DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
    SUPPORTED_DURATIONS = (4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)
    SUPPORTED_RESOLUTIONS = ("480p", "720p", "1080p")
    SUPPORTED_RATIOS = ("1:1", "3:4", "4:3", "16:9", "9:16", "21:9")

    def __init__(
        self,
        api_key: str,
        model: str = "doubao-seedance-2-0-fast-260128",
        base_url: str = None,
        **kwargs
    ):
        effective_base_url = base_url or self.DEFAULT_BASE_URL
        super().__init__(api_key, effective_base_url, **kwargs)
        self.model = model

    def _validate_params(self, duration: int, resolution: str, ratio: str) -> tuple:
        if duration not in self.SUPPORTED_DURATIONS:
            duration = max(4, min(15, duration))
        if resolution not in self.SUPPORTED_RESOLUTIONS:
            resolution = "1080p"
        if ratio not in self.SUPPORTED_RATIOS:
            ratio = "16:9"
        return duration, resolution, ratio

    async def generate(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        ratio: str = "16:9",
        duration: int = 15,
        resolution: str = "1080p",
        generate_audio: bool = True,
        watermark: bool = False,
        project_id: Optional[int] = None,
        episode_number: Optional[int] = None,
        segment_number: Optional[int] = None,
        **kwargs
    ) -> GenerationResult:
        """Generate video with embedded audio via Seedance.

        Ark v3 API uses top-level parameters (duration, ratio, etc.)
        and a `content` array for prompt text + reference images.
        """
        try:
            duration, resolution, ratio = self._validate_params(duration, resolution, ratio)

            content = [{"type": "text", "text": prompt.strip()}]
            if image_url:
                normalized = normalize_image_url_for_ark(image_url)
                if normalized:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": normalized},
                        "role": "reference_image"
                    })
                    if normalized.startswith("data:"):
                        print(f"[seedance] Using base64 data URL ({len(normalized)//1024}KB) for reference image")
                else:
                    print(f"[seedance] WARNING: image_url could not be normalized for Ark, falling back to text-only: {image_url[:120]}")

            payload: Dict[str, Any] = {
                "model": self.model,
                "content": content,
                "duration": duration,
                "ratio": ratio,
                "generate_audio": generate_audio,
                "watermark": watermark,
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=180.0) as client:
                # Create generation task
                response = await client.post(
                    f"{self.base_url}/contents/generations/tasks",
                    headers=headers,
                    json=payload
                )

                if response.status_code not in (200, 201):
                    return GenerationResult(
                        success=False,
                        error=f"Seedance task creation failed: HTTP {response.status_code}, body={response.text[:600]}"
                    )

                result = response.json()
                task_id = result.get("id") or result.get("task_id")
                if not task_id:
                    return GenerationResult(
                        success=False,
                        error=f"No task id in response: {json.dumps(result, ensure_ascii=False)[:500]}"
                    )

                # Poll task status
                task_url = f"{self.base_url}/contents/generations/tasks/{task_id}"
                # 15s 1080p typically takes 2-4 minutes; allow up to ~10 min
                max_wait = 900
                waited = 0
                poll_interval = 6

                while waited < max_wait:
                    await asyncio.sleep(poll_interval)
                    waited += poll_interval

                    task_response = await client.get(task_url, headers=headers)
                    if task_response.status_code != 200:
                        continue

                    task_result = task_response.json()
                    status = (task_result.get("status") or "").lower()

                    if status in ("succeeded", "completed", "success"):
                        # Ark returns video_url under "content" object (type-tagged), or
                        # directly on the task. Cover both.
                        video_url = None
                        c = task_result.get("content")
                        if isinstance(c, dict):
                            video_url = c.get("video_url") or c.get("url")
                        elif isinstance(c, list):
                            for item in c:
                                if isinstance(item, dict) and item.get("type") in ("video_url", "video"):
                                    vu = item.get("video_url") or item.get("url")
                                    if isinstance(vu, dict):
                                        vu = vu.get("url")
                                    if vu:
                                        video_url = vu
                                        break
                        if not video_url:
                            video_url = task_result.get("video_url") or task_result.get("url")
                        if not video_url:
                            data = task_result.get("data") or {}
                            video_url = data.get("video_url") or data.get("url")

                        if not video_url:
                            return GenerationResult(
                                success=False,
                                error=f"Task succeeded but no video_url in response: {json.dumps(task_result, ensure_ascii=False)[:600]}"
                            )

                        # Download to local storage
                        local_path = None
                        if project_id:
                            if segment_number is not None and episode_number is not None:
                                ep_dir = get_episode_dir(project_id, episode_number)
                                seg_dir = os.path.join(ep_dir, f"seg{segment_number:02d}")
                                os.makedirs(seg_dir, exist_ok=True)
                                final_path = os.path.join(seg_dir, "video.mp4")
                            elif episode_number is not None:
                                ep_dir = get_episode_dir(project_id, episode_number)
                                final_path = os.path.join(ep_dir, "final.mp4")
                            else:
                                from .media_storage import get_project_video_dir
                                import uuid
                                proj_vid_dir = get_project_video_dir(project_id)
                                final_path = os.path.join(proj_vid_dir, f"seedance_{uuid.uuid4().hex[:8]}.mp4")

                            saved = await save_video_to_path(video_url, final_path)
                            local_path = saved if saved else video_url

                        return GenerationResult(
                            success=True,
                            content=video_url,
                            data={
                                "video_url": video_url,
                                "local_path": local_path,
                                "task_id": task_id,
                                "task_result": task_result,
                            }
                        )

                    if status in ("failed", "error", "expired", "cancelled"):
                        err = task_result.get("error") or task_result.get("message")
                        if isinstance(err, dict):
                            err = err.get("message") or json.dumps(err, ensure_ascii=False)
                        return GenerationResult(
                            success=False,
                            error=f"Seedance task {status}: {err or 'no error detail'}; task_id={task_id}"
                        )

                    # else queued / running → keep polling

                return GenerationResult(
                    success=False,
                    error=f"Seedance video generation timed out after {max_wait}s; task_id={task_id}"
                )

        except Exception as e:
            return GenerationResult(success=False, error=f"{type(e).__name__}: {e}")

    async def test_connection(self) -> bool:
        """Test API connectivity with a minimal task creation."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/contents/generations/tasks",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "content": [{"type": "text", "text": "test"}],
                        "duration": 4,
                        "ratio": "16:9",
                    }
                )
                return response.status_code in (200, 201)
        except Exception:
            return False
