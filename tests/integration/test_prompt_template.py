"""
PromptTemplate API 集成测试
"""
import pytest
from httpx import AsyncClient

from app.core.database import PromptTemplate


pytestmark = pytest.mark.integration


class TestPromptTemplateAPI:
    """提示词模板API测试"""

    async def test_create_prompt_template(
        self,
        client: AsyncClient,
        sample_prompt_template_data: dict
    ):
        """测试创建提示词模板"""
        response = await client.post(
            "/api/v1/prompt-templates",
            json=sample_prompt_template_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_prompt_template_data["name"]
        assert data["type"] == sample_prompt_template_data["type"]
        assert data["is_default"] is True
        assert "id" in data

    async def test_get_prompt_template(
        self,
        client: AsyncClient,
        sample_prompt_template_data: dict
    ):
        """测试获取提示词模板"""
        # 先创建
        create_response = await client.post(
            "/api/v1/prompt-templates",
            json=sample_prompt_template_data
        )
        template_id = create_response.json()["id"]

        # 再获取
        response = await client.get(f"/api/v1/prompt-templates/{template_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        assert data["name"] == sample_prompt_template_data["name"]

    async def test_get_templates_by_type(
        self,
        client: AsyncClient,
        sample_prompt_template_data: dict
    ):
        """测试按类型获取模板"""
        # 创建多个模板
        for template_type in ["script", "character", "storyboard"]:
            await client.post(
                "/api/v1/prompt-templates",
                json={**sample_prompt_template_data, "type": template_type, "name": f"{template_type}_template"}
            )

        response = await client.get("/api/v1/prompt-templates?type=script")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        for item in data:
            assert item["type"] == "script"

    async def test_update_prompt_template(
        self,
        client: AsyncClient,
        sample_prompt_template_data: dict
    ):
        """测试更新提示词模板"""
        # 先创建
        create_response = await client.post(
            "/api/v1/prompt-templates",
            json=sample_prompt_template_data
        )
        template_id = create_response.json()["id"]

        # 更新
        update_data = {"template": "新的模板内容: {topic}"}
        response = await client.put(
            f"/api/v1/prompt-templates/{template_id}",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["template"] == "新的模板内容: {topic}"

    async def test_delete_prompt_template(
        self,
        client: AsyncClient,
        sample_prompt_template_data: dict
    ):
        """测试删除提示词模板"""
        # 先创建
        create_response = await client.post(
            "/api/v1/prompt-templates",
            json=sample_prompt_template_data
        )
        template_id = create_response.json()["id"]

        # 删除
        response = await client.delete(f"/api/v1/prompt-templates/{template_id}")
        assert response.status_code == 200

        # 确认已删除
        get_response = await client.get(f"/api/v1/prompt-templates/{template_id}")
        assert get_response.status_code == 404

    async def test_get_all_templates(
        self,
        client: AsyncClient,
        sample_prompt_template_data: dict
    ):
        """测试获取所有模板"""
        # 创建多个模板
        for i in range(3):
            await client.post(
                "/api/v1/prompt-templates",
                json={**sample_prompt_template_data, "name": f"template_{i}"}
            )

        response = await client.get("/api/v1/prompt-templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
