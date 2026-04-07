"""
ModelConfig API 集成测试
"""
import pytest
from httpx import AsyncClient

from app.core.database import ModelConfig


pytestmark = pytest.mark.integration


class TestModelConfigAPI:
    """模型配置API测试"""

    async def test_create_model_config(
        self,
        client: AsyncClient,
        sample_model_config_data: dict
    ):
        """测试创建模型配置"""
        response = await client.post(
            "/api/v1/model-config",
            json=sample_model_config_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_model_config_data["name"]
        assert data["provider"] == sample_model_config_data["provider"]
        assert data["is_active"] is True
        assert "id" in data

    async def test_get_model_config(
        self,
        client: AsyncClient,
        sample_model_config_data: dict
    ):
        """测试获取模型配置"""
        # 先创建
        create_response = await client.post(
            "/api/v1/model-config",
            json=sample_model_config_data
        )
        config_id = create_response.json()["id"]

        # 再获取
        response = await client.get(f"/api/v1/model-config/{config_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == config_id
        assert data["name"] == sample_model_config_data["name"]

    async def test_get_all_model_configs(
        self,
        client: AsyncClient,
        sample_model_config_data: dict
    ):
        """测试获取所有模型配置"""
        # 创建多个配置
        for name in ["text", "image", "video"]:
            await client.post(
                "/api/v1/model-config",
                json={**sample_model_config_data, "name": name}
            )

        response = await client.get("/api/v1/model-config")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    async def test_update_model_config(
        self,
        client: AsyncClient,
        sample_model_config_data: dict
    ):
        """测试更新模型配置"""
        # 先创建
        create_response = await client.post(
            "/api/v1/model-config",
            json=sample_model_config_data
        )
        config_id = create_response.json()["id"]

        # 更新
        update_data = {"model": "gpt-4-turbo", "is_active": False}
        response = await client.put(
            f"/api/v1/model-config/{config_id}",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "gpt-4-turbo"
        assert data["is_active"] is False

    async def test_delete_model_config(
        self,
        client: AsyncClient,
        sample_model_config_data: dict
    ):
        """测试删除模型配置"""
        # 先创建
        create_response = await client.post(
            "/api/v1/model-config",
            json=sample_model_config_data
        )
        config_id = create_response.json()["id"]

        # 删除
        response = await client.delete(f"/api/v1/model-config/{config_id}")
        assert response.status_code == 200

        # 确认已删除
        get_response = await client.get(f"/api/v1/model-config/{config_id}")
        assert get_response.status_code == 404

    async def test_get_active_config_by_name(
        self,
        client: AsyncClient,
        sample_model_config_data: dict
    ):
        """测试按名称获取激活配置"""
        # 创建配置
        await client.post(
            "/api/v1/model-config",
            json=sample_model_config_data
        )

        response = await client.get("/api/v1/model-config/text/active")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "text"
        assert data["is_active"] is True
