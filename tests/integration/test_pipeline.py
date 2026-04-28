"""
Pipeline integration tests
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock

pytestmark = pytest.mark.integration


class TestPipelineAPI:
    """流水线API测试"""

    async def test_start_pipeline(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试启动流水线"""
        # 创建项目
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        # 启动流水线
        response = await client.post(
            "/api/v1/pipeline/start",
            json={
                "project_id": project_id,
                "user_input": "一个关于程序员的故事",
                "options": {}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert data["project_id"] == project_id

    async def test_get_pipeline_status_not_found(
        self,
        client: AsyncClient
    ):
        """测试获取不存在的流水线状态"""
        response = await client.get("/api/v1/pipeline/status/99999")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_found"

    async def test_clear_pipeline_status(
        self,
        client: AsyncClient
    ):
        """测试清除流水线状态"""
        response = await client.delete("/api/v1/pipeline/status/1")
        assert response.status_code == 200

    async def test_start_pipeline_stream(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试启动流水线流式响应"""
        # 创建项目
        project_response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        # Mock LLM服务
        with patch("app.services.pipeline.get_llm_service") as mock_llm:
            mock_service = MagicMock()
            mock_service.generate = AsyncMock(return_value=MagicMock(
                success=True,
                data={
                    "title": "测试剧本",
                    "characters": [],
                    "scenes": []
                },
                content=None,
                error=None
            ))
            mock_llm.return_value = mock_service

            # 启动流式流水线
            response = await client.post(
                "/api/v1/pipeline/start/stream",
                json={
                    "project_id": project_id,
                    "user_input": "一个测试故事",
                    "options": {}
                }
            )
            assert response.status_code == 200
            # 流式响应检查
            assert "text/event-stream" in response.headers.get("content-type", "")


class TestPipelineService:
    """流水线服务测试"""

    @pytest.mark.asyncio
    async def test_generate_script(
        self,
        test_db,
        sample_project_data: dict,
        sample_model_config_data: dict
    ):
        """测试漫剧剧本生成"""
        from app.services.pipeline import VideoPipeline
        from app.core.database import Project, ModelConfig

        project = Project(**sample_project_data)
        test_db.add(project)
        await test_db.flush()

        config = ModelConfig(**sample_model_config_data)
        test_db.add(config)
        await test_db.commit()

        with patch("app.services.pipeline.get_llm_service") as mock_llm:
            mock_service = MagicMock()
            mock_service.generate = AsyncMock(return_value=MagicMock(
                success=True,
                data={
                    "title": "测试漫剧",
                    "art_style": "日系动漫风",
                    "characters": [{"name": "主角", "gender": "女"}],
                    "episodes": [
                        {
                            "episode_number": 1,
                            "title": "第一集",
                            "description": "测试",
                            "dialogues": [{"speaker": "主角", "text": "你好", "emotion": "开心"}],
                            "duration": 20
                        }
                    ]
                },
                content=None,
                error=None
            ))
            mock_llm.return_value = mock_service

            pipeline = VideoPipeline(test_db)
            result = await pipeline.generate_script(
                project_id=project.id,
                user_input="测试故事"
            )

            assert "title" in result
            assert result["title"] == "测试漫剧"
            assert result["art_style"] == "日系动漫风"
            assert "episodes" in result

    @pytest.mark.asyncio
    async def test_generate_episodes(
        self,
        test_db,
        sample_project_data: dict,
        sample_model_config_data: dict
    ):
        """测试剧集生成（episodes → Storyboard 行）"""
        from app.services.pipeline import VideoPipeline
        from app.core.database import Project

        project = Project(**sample_project_data)
        project.script_content = {
            "title": "测试",
            "episodes": [
                {
                    "episode_number": 1,
                    "title": "第一集",
                    "description": "测试描述",
                    "environment": "城市",
                    "time": "清晨",
                    "mood": "紧张",
                    "script": "完整的剧本文字",
                    "dialogues": [
                        {"speaker": "角色A", "text": "你好", "emotion": "开心"}
                    ],
                    "duration": 20
                },
                {
                    "episode_number": 2,
                    "title": "第二集",
                    "description": "测试描述2",
                    "environment": "公园",
                    "time": "黄昏",
                    "mood": "温馨",
                    "script": "更多剧本",
                    "dialogues": [],
                    "duration": 20
                }
            ]
        }
        test_db.add(project)
        await test_db.commit()

        pipeline = VideoPipeline(test_db)
        episodes = await pipeline.generate_episodes(project_id=project.id)

        assert len(episodes) == 2
        assert episodes[0].episode_number == 1
        assert episodes[0].title == "第一集"
        assert episodes[0].duration == 20
        assert episodes[0].episode_script == "完整的剧本文字"
        assert len(episodes[0].dialogue_lines) == 1
        assert "日系动漫" in episodes[0].image_prompt
        assert "日系动漫" in episodes[0].video_prompt

    @pytest.mark.asyncio
    async def test_generate_episodes_backward_compat(
        self,
        test_db,
        sample_project_data: dict
    ):
        """测试旧 scenes 格式向后兼容"""
        from app.services.pipeline import VideoPipeline
        from app.core.database import Project

        project = Project(**sample_project_data)
        project.script_content = {
            "title": "旧格式",
            "scenes": [
                {
                    "id": 1,
                    "name": "第一场",
                    "environment": "城市",
                    "time": "清晨",
                    "mood": "平静",
                    "description": "旧格式描述",
                    "shots": [
                        {"id": 1, "type": "全景", "description": "画面", "duration": 5}
                    ]
                }
            ]
        }
        test_db.add(project)
        await test_db.commit()

        pipeline = VideoPipeline(test_db)
        episodes = await pipeline.generate_episodes(project_id=project.id)

        assert len(episodes) == 1
        assert episodes[0].title == "第一场"
        assert episodes[0].duration == 20

    @pytest.mark.asyncio
    async def test_pipeline_progress(
        self,
        test_db,
        sample_project_data: dict,
        sample_model_config_data: dict
    ):
        """测试流水线进度回调"""
        from app.services.pipeline import VideoPipeline, PipelineProgress
        from app.core.database import Project, ModelConfig

        project = Project(**sample_project_data)
        test_db.add(project)
        await test_db.flush()

        config = ModelConfig(**sample_model_config_data)
        test_db.add(config)
        await test_db.commit()

        progress_list = []

        async def capture_progress(progress: PipelineProgress):
            progress_list.append(progress)

        with patch("app.services.pipeline.get_llm_service") as mock_llm:
            mock_service = MagicMock()
            mock_service.generate = AsyncMock(return_value=MagicMock(
                success=True,
                data={
                    "title": "测试漫剧",
                    "characters": [],
                    "episodes": [
                        {
                            "episode_number": 1,
                            "title": "第一集",
                            "description": "测试",
                            "duration": 20,
                            "dialogues": [],
                            "script": "测试剧本"
                        }
                    ]
                },
                content=None,
                error=None
            ))
            mock_llm.return_value = mock_service

            pipeline = VideoPipeline(test_db)
            pipeline.on_progress(capture_progress)

            await pipeline.generate_short_drama(
                project_id=project.id,
                user_input="测试故事"
            )

            assert len(progress_list) > 0
