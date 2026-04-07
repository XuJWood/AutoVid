"""
Characters API 集成测试
"""
import pytest
from httpx import AsyncClient

from app.core.database import Character, Project


pytestmark = pytest.mark.integration


class TestCharactersAPI:
    """角色API测试"""

    async def test_create_character(
        self,
        client: AsyncClient,
        sample_character_data: dict,
        sample_project_data: dict
    ):
        """测试创建角色"""
        # 先创建项目
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        # 创建角色
        response = await client.post(
            "/api/v1/characters",
            json={**sample_character_data, "project_id": project_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_character_data["name"]
        assert data["project_id"] == project_id
        assert "id" in data

    async def test_get_character(
        self,
        client: AsyncClient,
        sample_character_data: dict,
        sample_project_data: dict
    ):
        """测试获取单个角色"""
        # 创建项目和角色
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        create_response = await client.post(
            "/api/v1/characters",
            json={**sample_character_data, "project_id": project_id}
        )
        character_id = create_response.json()["id"]

        # 获取角色
        response = await client.get(f"/api/v1/characters/{character_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == character_id
        assert data["name"] == sample_character_data["name"]

    async def test_get_characters_by_project(
        self,
        client: AsyncClient,
        sample_character_data: dict,
        sample_project_data: dict
    ):
        """测试按项目获取角色列表"""
        # 创建项目
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        # 创建多个角色
        for i in range(3):
            await client.post(
                "/api/v1/characters",
                json={**sample_character_data, "name": f"角色{i}", "project_id": project_id}
            )

        response = await client.get(f"/api/v1/projects/{project_id}/characters")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    async def test_update_character(
        self,
        client: AsyncClient,
        sample_character_data: dict,
        sample_project_data: dict
    ):
        """测试更新角色"""
        # 创建项目和角色
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        create_response = await client.post(
            "/api/v1/characters",
            json={**sample_character_data, "project_id": project_id}
        )
        character_id = create_response.json()["id"]

        # 更新角色
        update_data = {"name": "更新后的角色名", "age": 30}
        response = await client.put(
            f"/api/v1/characters/{character_id}",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的角色名"
        assert data["age"] == 30

    async def test_delete_character(
        self,
        client: AsyncClient,
        sample_character_data: dict,
        sample_project_data: dict
    ):
        """测试删除角色"""
        # 创建项目和角色
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = project_response.json()["id"]

        create_response = await client.post(
            "/api/v1/characters",
            json={**sample_character_data, "project_id": project_id}
        )
        character_id = create_response.json()["id"]

        # 删除角色
        response = await client.delete(f"/api/v1/characters/{character_id}")
        assert response.status_code == 200

        # 确认已删除
        get_response = await client.get(f"/api/v1/characters/{character_id}")
        assert get_response.status_code == 404

    async def test_create_character_without_project(
        self,
        client: AsyncClient,
        sample_character_data: dict
    ):
        """测试创建无项目关联的角色"""
        response = await client.post(
            "/api/v1/characters",
            json=sample_character_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_character_data["name"]
        assert data.get("project_id") is None
