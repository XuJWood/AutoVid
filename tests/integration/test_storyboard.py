"""
Storyboard / Episode API 集成测试
"""
import pytest
from httpx import AsyncClient

from app.core.database import Project, Storyboard

pytestmark = pytest.mark.integration


@pytest.fixture
async def project_with_script(client: AsyncClient, sample_project_data: dict):
    """创建带有剧本内容的项目（新 episodes 格式）"""
    create_response = await client.post(
        "/api/v1/projects",
        json=sample_project_data
    )
    project_id = create_response.json()["id"]

    script_content = {
        "title": "测试漫剧",
        "art_style": "日系动漫风",
        "episodes": [
            {
                "episode_number": 1,
                "title": "开场",
                "environment": "城市街道",
                "time": "清晨",
                "mood": "希望",
                "description": "第一集概述",
                "script": "主角走在街道上。",
                "dialogues": [
                    {"speaker": "主角", "text": "新的一天开始了", "emotion": "期待"}
                ],
                "shots": [
                    {"id": 1, "type": "远景", "description": "城市全景", "duration": 5},
                    {"id": 2, "type": "全景", "description": "主角走在街上", "duration": 4}
                ]
            },
            {
                "episode_number": 2,
                "title": "相遇",
                "environment": "咖啡厅",
                "time": "上午",
                "mood": "温馨",
                "description": "第二集概述",
                "script": "两人在咖啡厅相遇。",
                "dialogues": [
                    {"speaker": "女主", "text": "你好，我们又见面了", "emotion": "开心"}
                ],
                "shots": [
                    {"id": 1, "type": "中景", "description": "两人相对而坐", "duration": 6}
                ]
            }
        ]
    }

    await client.put(
        f"/api/v1/projects/{project_id}",
        json={"script_content": script_content}
    )

    get_response = await client.get(f"/api/v1/projects/{project_id}")
    return get_response.json()


@pytest.fixture
async def project_with_old_scenes(client: AsyncClient, sample_project_data: dict):
    """创建带有旧 scenes 格式剧本的项目（向后兼容测试）"""
    create_response = await client.post(
        "/api/v1/projects",
        json=sample_project_data
    )
    project_id = create_response.json()["id"]

    script_content = {
        "title": "旧格式测试",
        "scenes": [
            {
                "id": 1,
                "name": "开场",
                "environment": "城市街道",
                "time": "清晨",
                "shots": [
                    {"id": 1, "type": "远景", "description": "城市全景", "duration": 5},
                    {"id": 2, "type": "全景", "description": "主角走在街上", "duration": 4}
                ]
            },
            {
                "id": 2,
                "name": "相遇",
                "environment": "咖啡厅",
                "time": "上午",
                "shots": [
                    {"id": 1, "type": "中景", "description": "两人相对而坐", "duration": 6}
                ]
            }
        ]
    }

    await client.put(
        f"/api/v1/projects/{project_id}",
        json={"script_content": script_content}
    )

    get_response = await client.get(f"/api/v1/projects/{project_id}")
    return get_response.json()


class TestStoryboardAPI:
    """剧集API测试"""

    async def test_get_empty_storyboard(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试获取空剧集列表"""
        create_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = create_response.json()["id"]

        response = await client.get(f"/api/v1/storyboard/project/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_generate_episodes(
        self,
        client: AsyncClient,
        project_with_script: dict
    ):
        """测试从 episodes 格式生成剧集"""
        project_id = project_with_script["id"]

        response = await client.post(f"/api/v1/storyboard/project/{project_id}/generate")
        assert response.status_code == 200
        data = response.json()

        # 2 episodes → 2 storyboard rows
        assert len(data) == 2

        # 检查第一集数据
        assert data[0]["episode_number"] == 1
        assert data[0]["title"] == "开场"
        assert data[0]["scene_index"] == 0
        assert data[0]["shot_index"] == 0
        assert data[0]["duration"] == 15
        assert data[0]["status"] == "pending"
        assert data[0]["episode_script"] is not None
        assert data[0]["dialogue_lines"] is not None
        assert len(data[0]["dialogue_lines"]) == 1
        assert "image_prompt" in data[0]
        assert "video_prompt" in data[0]

        # 检查第二集
        assert data[1]["episode_number"] == 2
        assert data[1]["title"] == "相遇"

    async def test_generate_from_old_scenes_format(
        self,
        client: AsyncClient,
        project_with_old_scenes: dict
    ):
        """测试从旧 scenes 格式生成剧集（向后兼容）"""
        project_id = project_with_old_scenes["id"]

        response = await client.post(f"/api/v1/storyboard/project/{project_id}/generate")
        assert response.status_code == 200
        data = response.json()

        # 2 scenes → 2 episodes
        assert len(data) == 2

        assert data[0]["title"] == "开场"
        assert data[1]["title"] == "相遇"
        assert data[0]["duration"] == 15

    async def test_generate_storyboard_no_script(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试无剧本时生成剧集"""
        create_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = create_response.json()["id"]

        response = await client.post(f"/api/v1/storyboard/project/{project_id}/generate")
        assert response.status_code == 400

    async def test_get_project_episodes(
        self,
        client: AsyncClient,
        project_with_script: dict
    ):
        """测试获取项目剧集列表"""
        project_id = project_with_script["id"]

        await client.post(f"/api/v1/storyboard/project/{project_id}/generate")

        response = await client.get(f"/api/v1/storyboard/project/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # 应按 episode_number 排序
        assert data[0]["episode_number"] == 1
        assert data[1]["episode_number"] == 2

    async def test_generate_storyboard_image(
        self,
        client: AsyncClient,
        project_with_script: dict,
        sample_model_config_data: dict,
        mock_storyboard_image_service
    ):
        """测试生成剧集封面图"""
        project_id = project_with_script["id"]

        config_data = sample_model_config_data.copy()
        config_data["name"] = "image"
        config_data["provider"] = "openai"
        config_data["model"] = "dall-e-3"
        await client.post("/api/v1/model-config", json=config_data)

        generate_response = await client.post(f"/api/v1/storyboard/project/{project_id}/generate")
        episode_id = generate_response.json()[0]["id"]

        response = await client.post(f"/api/v1/storyboard/{episode_id}/generate-image")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["image_url"] is not None

    async def test_generate_storyboard_video(
        self,
        client: AsyncClient,
        project_with_script: dict,
        sample_model_config_data: dict,
        mock_storyboard_video_service
    ):
        """测试生成剧集视频"""
        project_id = project_with_script["id"]

        config_data = sample_model_config_data.copy()
        config_data["name"] = "video"
        config_data["provider"] = "runway"
        config_data["model"] = "gen-2"
        await client.post("/api/v1/model-config", json=config_data)

        generate_response = await client.post(f"/api/v1/storyboard/project/{project_id}/generate")
        episode_id = generate_response.json()[0]["id"]

        response = await client.post(f"/api/v1/storyboard/{episode_id}/generate-video")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["video_url"] is not None

    async def test_delete_storyboard(
        self,
        client: AsyncClient,
        project_with_script: dict
    ):
        """测试删除剧集"""
        project_id = project_with_script["id"]

        generate_response = await client.post(f"/api/v1/storyboard/project/{project_id}/generate")
        episode_id = generate_response.json()[0]["id"]

        response = await client.delete(f"/api/v1/storyboard/{episode_id}")
        assert response.status_code == 200

        list_response = await client.get(f"/api/v1/storyboard/project/{project_id}")
        data = list_response.json()
        assert len(data) == 1  # 原来2集，删了1集

    async def test_storyboard_not_found(
        self,
        client: AsyncClient
    ):
        """测试获取不存在的剧集"""
        response = await client.delete("/api/v1/storyboard/99999")
        assert response.status_code == 404
