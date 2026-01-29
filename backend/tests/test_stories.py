"""
Story API Tests
Tests for story generation and CRUD operations.
"""
import json
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch


class TestStoryGeneration:
    """Tests for AI story generation."""

    @pytest.mark.asyncio
    async def test_generate_story_success(
        self,
        client: AsyncClient,
        sample_project_data,
        sample_story_data,
        mock_gemini_response,
    ):
        """Test successful story generation."""
        # Create project first
        project_response = await client.post("/api/v1/projects", json=sample_project_data)
        project_id = project_response.json()["id"]

        # Mock Gemini response
        with patch("src.domains.stories.services.StoryService._generate_script") as mock_gen:
            from src.domains.stories.entities import GeneratedScript, GeneratedScene

            mock_gen.return_value = GeneratedScript(
                title="Test Story",
                scenes=[
                    GeneratedScene(
                        order=1,
                        narration="First scene narration",
                        visual_prompt="Visual for scene 1",
                        duration_seconds=10,
                    ),
                    GeneratedScene(
                        order=2,
                        narration="Second scene narration",
                        visual_prompt="Visual for scene 2",
                        duration_seconds=10,
                    ),
                ],
                total_duration_seconds=20,
            )

            response = await client.post(
                "/api/v1/stories/generate",
                json={**sample_story_data, "project_id": project_id},
            )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == "Test Story"
        assert data["scene_count"] == 2

    @pytest.mark.asyncio
    async def test_generate_story_invalid_project(
        self,
        client: AsyncClient,
        sample_story_data,
    ):
        """Test story generation with invalid project ID."""
        fake_project_id = "00000000-0000-0000-0000-000000000000"

        response = await client.post(
            "/api/v1/stories/generate",
            json={**sample_story_data, "project_id": fake_project_id},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_generate_story_short_prompt(self, client: AsyncClient, sample_project_data):
        """Test story generation with too short prompt."""
        project_response = await client.post("/api/v1/projects", json=sample_project_data)
        project_id = project_response.json()["id"]

        response = await client.post(
            "/api/v1/stories/generate",
            json={
                "project_id": project_id,
                "prompt": "short",  # Too short
            },
        )

        assert response.status_code == 422


class TestStoryCRUD:
    """Tests for story CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_story_manual(self, client: AsyncClient, sample_project_data):
        """Test manual story creation."""
        # Create project first
        project_response = await client.post("/api/v1/projects", json=sample_project_data)
        project_id = project_response.json()["id"]

        response = await client.post(
            "/api/v1/stories",
            json={
                "project_id": project_id,
                "title": "Manual Story",
                "prompt": "A story created manually",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Manual Story"

    @pytest.mark.asyncio
    async def test_list_stories(self, client: AsyncClient, sample_project_data):
        """Test listing stories for a project."""
        # Create project
        project_response = await client.post("/api/v1/projects", json=sample_project_data)
        project_id = project_response.json()["id"]

        # Create story
        await client.post(
            "/api/v1/stories",
            json={
                "project_id": project_id,
                "title": "Test Story",
                "prompt": "Test prompt for story",
            },
        )

        # List stories
        response = await client.get(f"/api/v1/stories?project_id={project_id}")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_get_story_with_scenes(self, client: AsyncClient, sample_project_data):
        """Test getting a story with its scenes."""
        # Create project and story
        project_response = await client.post("/api/v1/projects", json=sample_project_data)
        project_id = project_response.json()["id"]

        story_response = await client.post(
            "/api/v1/stories",
            json={
                "project_id": project_id,
                "title": "Story with Scenes",
                "prompt": "Test prompt for story",
            },
        )
        story_id = story_response.json()["id"]

        # Get story
        response = await client.get(f"/api/v1/stories/{story_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == story_id

    @pytest.mark.asyncio
    async def test_delete_story(self, client: AsyncClient, sample_project_data):
        """Test deleting a story."""
        # Create project and story
        project_response = await client.post("/api/v1/projects", json=sample_project_data)
        project_id = project_response.json()["id"]

        story_response = await client.post(
            "/api/v1/stories",
            json={
                "project_id": project_id,
                "title": "Story to Delete",
                "prompt": "Test prompt for story",
            },
        )
        story_id = story_response.json()["id"]

        # Delete story
        response = await client.delete(f"/api/v1/stories/{story_id}")
        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(f"/api/v1/stories/{story_id}")
        assert get_response.status_code == 404
