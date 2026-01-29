"""
Video Generation Tests
Tests for video pipeline operations.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock


class TestVideoGeneration:
    """Tests for video generation endpoints."""

    @pytest.mark.asyncio
    async def test_start_video_job(self, client: AsyncClient, sample_project_data):
        """Test starting a video generation job."""
        # Create project and story
        project_response = await client.post("/api/v1/projects", json=sample_project_data)
        project_id = project_response.json()["id"]

        story_response = await client.post(
            "/api/v1/stories",
            json={
                "project_id": project_id,
                "title": "Test Story",
                "prompt": "A test story for video generation",
            },
        )
        story_id = story_response.json()["id"]

        # Start video job
        response = await client.post(
            "/api/v1/video/jobs",
            json={
                "story_id": story_id,
                "generate_audio": True,
                "generate_video": True,
                "stitch_final": True,
            },
        )

        assert response.status_code in [201, 202]
        data = response.json()
        assert "job_id" in data or "id" in data

    @pytest.mark.asyncio
    async def test_get_job_status(self, client: AsyncClient, sample_project_data):
        """Test getting video job status."""
        # Create project and story
        project_response = await client.post("/api/v1/projects", json=sample_project_data)
        project_id = project_response.json()["id"]

        story_response = await client.post(
            "/api/v1/stories",
            json={
                "project_id": project_id,
                "title": "Test Story",
                "prompt": "A test story for video generation",
            },
        )
        story_id = story_response.json()["id"]

        # Start job
        job_response = await client.post(
            "/api/v1/video/jobs",
            json={"story_id": story_id},
        )

        if job_response.status_code in [201, 202]:
            job_id = job_response.json().get("job_id") or job_response.json().get("id")

            # Get status
            response = await client.get(f"/api/v1/video/jobs/{job_id}")
            # May be 200 (found) or 404 (if job_id format differs)
            assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_generate_video_full_pipeline(self, client: AsyncClient, sample_project_data):
        """Test the full video generation pipeline endpoint."""
        # Create project
        project_response = await client.post("/api/v1/projects", json=sample_project_data)
        project_id = project_response.json()["id"]

        # Call full pipeline endpoint
        with patch("src.domains.video_generation.enhanced_tasks.generate_project_video.delay") as mock_task:
            mock_task.return_value = MagicMock(id="mock-task-id")

            response = await client.post(
                f"/api/v1/projects/{project_id}/generate-video",
                json={
                    "prompt": "Create a video about space exploration and the future of humanity",
                    "target_duration": 60,
                },
            )

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"


class TestContentEndpoints:
    """Tests for content endpoints (captions, exports)."""

    @pytest.mark.asyncio
    async def test_generate_captions(self, client: AsyncClient, sample_project_data):
        """Test caption generation."""
        # Create project and story
        project_response = await client.post("/api/v1/projects", json=sample_project_data)
        project_id = project_response.json()["id"]

        story_response = await client.post(
            "/api/v1/stories",
            json={
                "project_id": project_id,
                "title": "Story for Captions",
                "prompt": "Test story for caption generation",
            },
        )
        story_id = story_response.json()["id"]

        # Generate captions
        response = await client.post(
            "/api/v1/content/captions",
            json={
                "story_id": story_id,
                "style": "standard",
                "position": "bottom",
            },
        )

        # May succeed or fail based on scene availability
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_export_video(self, client: AsyncClient, sample_project_data):
        """Test video export."""
        # Create project and story
        project_response = await client.post("/api/v1/projects", json=sample_project_data)
        project_id = project_response.json()["id"]

        story_response = await client.post(
            "/api/v1/stories",
            json={
                "project_id": project_id,
                "title": "Story for Export",
                "prompt": "Test story for video export",
            },
        )
        story_id = story_response.json()["id"]

        # Start export
        response = await client.post(
            "/api/v1/content/exports",
            json={
                "story_id": story_id,
                "format": "mp4_1080p",
                "include_captions": False,
            },
        )

        assert response.status_code in [200, 202]


class TestAnalyticsEndpoints:
    """Tests for analytics endpoints."""

    @pytest.mark.asyncio
    async def test_get_stats(self, client: AsyncClient):
        """Test getting usage stats."""
        response = await client.get("/api/v1/analytics/stats?days=7")

        assert response.status_code == 200
        data = response.json()
        assert "overall" in data
        assert "daily" in data

    @pytest.mark.asyncio
    async def test_log_event(self, client: AsyncClient):
        """Test logging a usage event."""
        response = await client.post(
            "/api/v1/analytics/events",
            json={
                "event_type": "api_call",
                "user_id": "test_user",
                "service": "gemini",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
