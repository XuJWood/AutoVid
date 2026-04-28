"""
Projects API 集成测试
"""
import pytest
from httpx import AsyncClient

from app.core.database import Project


pytestmark = pytest.mark.integration


class TestProjectsAPI:
    """项目API测试"""

    async def test_create_project(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试创建项目"""
        response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_project_data["name"]
        assert data["type"] == sample_project_data["type"]
        assert data["status"] == "draft"
        assert "id" in data

    async def test_get_project(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试获取单个项目"""
        # 先创建
        create_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = create_response.json()["id"]

        # 再获取
        response = await client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == sample_project_data["name"]

    async def test_get_projects_list(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试获取项目列表"""
        # 创建多个项目
        for i in range(3):
            await client.post(
                "/api/v1/projects",
                json={**sample_project_data, "name": f"项目{i}"}
            )

        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    async def test_get_projects_filter_by_type(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试按类型筛选项目"""
        # 创建不同类型项目
        await client.post(
            "/api/v1/projects",
            json={**sample_project_data, "type": "drama", "name": "短剧项目"}
        )
        await client.post(
            "/api/v1/projects",
            json={**sample_project_data, "type": "video", "name": "视频项目"}
        )

        response = await client.get("/api/v1/projects?type=drama")
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["type"] == "drama"

    async def test_update_project(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试更新项目"""
        # 先创建
        create_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = create_response.json()["id"]

        # 更新
        update_data = {
            "name": "更新后的名称",
            "status": "in_progress"
        }
        response = await client.put(
            f"/api/v1/projects/{project_id}",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的名称"
        assert data["status"] == "in_progress"

    async def test_delete_project(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试删除项目"""
        # 先创建
        create_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = create_response.json()["id"]

        # 删除
        response = await client.delete(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200

        # 确认已删除
        get_response = await client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 404

    async def test_get_project_not_found(
        self,
        client: AsyncClient
    ):
        """测试获取不存在的项目"""
        response = await client.get("/api/v1/projects/99999")
        assert response.status_code == 404


class TestScriptGeneration:
    """剧本生成测试"""

    async def test_generate_script_with_mock(
        self,
        client: AsyncClient,
        sample_project_data: dict,
        mock_llm_service
    ):
        """测试剧本生成（mock LLM）"""
        # 创建项目
        create_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = create_response.json()["id"]

        # 生成剧本
        response = await client.post(
            f"/api/v1/projects/{project_id}/script/generate",
            json={"input": "测试输入", "prompt_suffix": ""}
        )
        assert response.status_code == 200
        # SSE响应检查
        assert "text/event-stream" in response.headers.get("content-type", "")
