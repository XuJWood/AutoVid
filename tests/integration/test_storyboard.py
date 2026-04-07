"""
Storyboard API 集成测试
"""
import pytest
from httpx import AsyncClient

from app.core.database import Project, Storyboard

pytestmark = pytest.mark.integration


@pytest.fixture
async def project_with_script(client: AsyncClient, sample_project_data: dict):
    """创建带有剧本内容的项目"""
    # 先创建项目
    create_response = await client.post(
        "/api/v1/projects",
        json=sample_project_data
    )
    project_id = create_response.json()["id"]

    # 更新项目添加剧本内容
    script_content = {
        "title": "测试剧本",
        "scenes": [
            {
                "id": 1,
                "name": "开场",
                "environment": "城市街道",
                "time": "清晨",
                "shots": [
                    {
                        "id": 1,
                        "type": "远景",
                        "description": "城市全景，晨光初现",
                        "duration": 5
                    },
                    {
                        "id": 2,
                        "type": "全景",
                        "description": "主角走在街上",
                        "duration": 4
                    }
                ]
            },
            {
                "id": 2,
                "name": "相遇",
                "environment": "咖啡厅",
                "time": "上午",
                "shots": [
                    {
                        "id": 1,
                        "type": "中景",
                        "description": "两人相对而坐",
                        "duration": 6
                    }
                ]
            }
        ]
    }

    await client.put(
        f"/api/v1/projects/{project_id}",
        json={"script_content": script_content}
    )

    # 返回完整的项目数据
    get_response = await client.get(f"/api/v1/projects/{project_id}")
    return get_response.json()


class TestStoryboardAPI:
    """分镜API测试"""

    async def test_get_empty_storyboard(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试获取空分镜列表"""
        # 创建项目
        create_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = create_response.json()["id"]

        # 获取分镜
        response = await client.get(f"/api/v1/storyboard/project/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_generate_storyboard(
        self,
        client: AsyncClient,
        project_with_script: dict
    ):
        """测试生成分镜"""
        project_id = project_with_script["id"]

        response = await client.post(f"/api/v1/storyboard/project/{project_id}/generate")
        assert response.status_code == 200
        data = response.json()

        # 应该生成3个分镜（2个场景，共3个镜头）
        assert len(data) == 3

        # 检查分镜数据
        assert data[0]["scene_index"] == 0
        assert data[0]["shot_index"] == 0
        assert data[0]["shot_type"] == "远景"
        assert "image_prompt" in data[0]
        assert "video_prompt" in data[0]
        assert data[0]["duration"] == 5
        assert data[0]["status"] == "pending"

    async def test_generate_storyboard_no_script(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试无剧本时生成分镜"""
        # 创建没有剧本的项目
        create_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = create_response.json()["id"]

        response = await client.post(f"/api/v1/storyboard/project/{project_id}/generate")
        assert response.status_code == 400

    async def test_get_project_storyboard(
        self,
        client: AsyncClient,
        project_with_script: dict
    ):
        """测试获取项目分镜列表"""
        project_id = project_with_script["id"]

        # 先生成分镜
        await client.post(f"/api/v1/storyboard/project/{project_id}/generate")

        # 获取分镜
        response = await client.get(f"/api/v1/storyboard/project/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    async def test_generate_storyboard_image(
        self,
        client: AsyncClient,
        project_with_script: dict,
        sample_model_config_data: dict,
        mock_storyboard_image_service
    ):
        """测试生成分镜图片"""
        project_id = project_with_script["id"]

        # 创建图像模型配置
        config_data = sample_model_config_data.copy()
        config_data["name"] = "image"
        config_data["provider"] = "openai"
        config_data["model"] = "dall-e-3"
        await client.post("/api/v1/model-config", json=config_data)

        # 生成分镜
        generate_response = await client.post(f"/api/v1/storyboard/project/{project_id}/generate")
        storyboard_id = generate_response.json()[0]["id"]

        # 生成图片
        response = await client.post(f"/api/v1/storyboard/{storyboard_id}/generate-image")
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
        """测试生成分镜视频"""
        project_id = project_with_script["id"]

        # 创建视频模型配置
        config_data = sample_model_config_data.copy()
        config_data["name"] = "video"
        config_data["provider"] = "runway"
        config_data["model"] = "gen-2"
        await client.post("/api/v1/model-config", json=config_data)

        # 生成分镜
        generate_response = await client.post(f"/api/v1/storyboard/project/{project_id}/generate")
        storyboard_id = generate_response.json()[0]["id"]

        # 生成视频
        response = await client.post(f"/api/v1/storyboard/{storyboard_id}/generate-video")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["video_url"] is not None

    async def test_delete_storyboard(
        self,
        client: AsyncClient,
        project_with_script: dict
    ):
        """测试删除分镜"""
        project_id = project_with_script["id"]

        # 先生成分镜
        generate_response = await client.post(f"/api/v1/storyboard/project/{project_id}/generate")
        storyboard_id = generate_response.json()[0]["id"]

        # 删除分镜
        response = await client.delete(f"/api/v1/storyboard/{storyboard_id}")
        assert response.status_code == 200

        # 确认已删除
        list_response = await client.get(f"/api/v1/storyboard/project/{project_id}")
        data = list_response.json()
        assert len(data) == 2  # 原来有3个，删了1个

    async def test_storyboard_not_found(
        self,
        client: AsyncClient
    ):
        """测试获取不存在的分镜"""
        response = await client.delete("/api/v1/storyboard/99999")
        assert response.status_code == 404
