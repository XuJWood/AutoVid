"""
Videos API 集成测试
"""
import pytest
from httpx import AsyncClient

from app.core.database import GeneratedVideo, Project


pytestmark = pytest.mark.integration


class TestVideosAPI:
    """视频API测试"""

    async def test_create_video_task(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试创建视频生成任务"""
        # 创建项目
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        # 创建视频任务（使用正确的端点）
        response = await client.post(
            "/api/v1/videos/generate",
            json={
                "project_id": project_id,
                "scene_description": "测试场景描述",
                "duration": 5,
                "resolution": "1080p",
                "aspect_ratio": "16:9"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "video_id" in data
        assert data["status"] == "pending"

    async def test_get_video(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试获取单个视频信息"""
        # 创建项目和视频
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        create_response = await client.post(
            "/api/v1/videos/generate",
            json={
                "project_id": project_id,
                "scene_description": "测试场景"
            }
        )
        video_id = create_response.json()["video_id"]

        # 获取视频
        response = await client.get(f"/api/v1/videos/{video_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == video_id
        assert data["status"] == "pending"

    async def test_get_videos_by_project(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试按项目获取视频列表"""
        # 创建项目
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        # 创建多个视频任务
        for i in range(3):
            await client.post(
                "/api/v1/videos/generate",
                json={
                    "project_id": project_id,
                    "scene_description": f"场景{i}"
                }
            )

        response = await client.get(f"/api/v1/videos?project_id={project_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    async def test_get_video_status(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试获取视频状态"""
        # 创建项目和视频
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        create_response = await client.post(
            "/api/v1/videos/generate",
            json={
                "project_id": project_id,
                "scene_description": "测试场景"
            }
        )
        video_id = create_response.json()["video_id"]

        # 获取状态
        response = await client.get(f"/api/v1/videos/{video_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "progress" in data

    async def test_delete_video(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试删除视频记录"""
        # 创建项目和视频
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        create_response = await client.post(
            "/api/v1/videos/generate",
            json={
                "project_id": project_id,
                "scene_description": "测试场景"
            }
        )
        video_id = create_response.json()["video_id"]

        # 删除视频
        response = await client.delete(f"/api/v1/videos/{video_id}")
        assert response.status_code == 200

        # 确认已删除
        get_response = await client.get(f"/api/v1/videos/{video_id}")
        assert get_response.status_code == 404

    async def test_get_all_videos(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试获取所有视频"""
        # 创建项目
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        # 创建多个视频
        for i in range(3):
            await client.post(
                "/api/v1/videos/generate",
                json={
                    "project_id": project_id,
                    "scene_description": f"场景{i}"
                }
            )

        response = await client.get("/api/v1/videos")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    async def test_regenerate_video(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试重新生成视频"""
        # 创建项目和视频
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        create_response = await client.post(
            "/api/v1/videos/generate",
            json={
                "project_id": project_id,
                "scene_description": "测试场景"
            }
        )
        video_id = create_response.json()["video_id"]

        # 重新生成
        response = await client.post(f"/api/v1/videos/{video_id}/regenerate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
