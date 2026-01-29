"""
Project API Tests
Tests for project CRUD operations.
"""
import pytest
from httpx import AsyncClient


class TestProjectCRUD:
    """Tests for project CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_project(self, client: AsyncClient, sample_project_data):
        """Test project creation."""
        response = await client.post("/api/v1/projects", json=sample_project_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_project_data["name"]
        assert data["description"] == sample_project_data["description"]
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_project_minimal(self, client: AsyncClient):
        """Test project creation with minimal data."""
        response = await client.post(
            "/api/v1/projects",
            json={"name": "Minimal Project"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Project"
        assert data["description"] is None

    @pytest.mark.asyncio
    async def test_create_project_invalid(self, client: AsyncClient):
        """Test project creation with invalid data."""
        response = await client.post(
            "/api/v1/projects",
            json={"name": ""},  # Empty name should fail
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_projects(self, client: AsyncClient, sample_project_data):
        """Test listing projects."""
        # Create a project first
        await client.post("/api/v1/projects", json=sample_project_data)

        response = await client.get("/api/v1/projects")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_projects_pagination(self, client: AsyncClient, sample_project_data):
        """Test project listing with pagination."""
        # Create multiple projects
        for i in range(5):
            await client.post(
                "/api/v1/projects",
                json={**sample_project_data, "name": f"Project {i}"},
            )

        response = await client.get("/api/v1/projects?page=1&size=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["size"] == 2

    @pytest.mark.asyncio
    async def test_get_project(self, client: AsyncClient, sample_project_data):
        """Test getting a single project."""
        # Create project
        create_response = await client.post("/api/v1/projects", json=sample_project_data)
        project_id = create_response.json()["id"]

        # Get project
        response = await client.get(f"/api/v1/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == sample_project_data["name"]

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, client: AsyncClient):
        """Test getting a non-existent project."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/v1/projects/{fake_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_project(self, client: AsyncClient, sample_project_data):
        """Test updating a project."""
        # Create project
        create_response = await client.post("/api/v1/projects", json=sample_project_data)
        project_id = create_response.json()["id"]

        # Update project
        response = await client.patch(
            f"/api/v1/projects/{project_id}",
            json={"name": "Updated Name", "description": "Updated description"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_project(self, client: AsyncClient, sample_project_data):
        """Test deleting a project."""
        # Create project
        create_response = await client.post("/api/v1/projects", json=sample_project_data)
        project_id = create_response.json()["id"]

        # Delete project
        response = await client.delete(f"/api/v1/projects/{project_id}")
        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 404


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_basic_health(self, client: AsyncClient):
        """Test basic health endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_api_health(self, client: AsyncClient):
        """Test API v1 health endpoint."""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
