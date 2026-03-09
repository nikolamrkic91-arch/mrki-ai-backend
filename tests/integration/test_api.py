"""Integration tests for API endpoints."""

import pytest


@pytest.mark.integration
class TestAPI:
    """Integration tests for API."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Mrki Unified API"

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "modules" in data

    def test_api_info(self, client):
        """Test API info endpoint."""
        response = client.get("/api/v1/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Mrki API"
        assert "endpoints" in data

    def test_core_health(self, client):
        """Test core module health check."""
        response = client.get("/api/v1/core/health")
        assert response.status_code == 200
        data = response.json()
        assert "module" in data
        assert data["module"] == "core"

    def test_visual_health(self, client):
        """Test visual engine health check."""
        response = client.get("/api/v1/visual/health")
        assert response.status_code == 200
        data = response.json()
        assert data["module"] == "visual_engine"

    def test_gamedev_engines(self, client):
        """Test listing game engines."""
        response = client.get("/api/v1/gamedev/engines")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["engines"]) == 3

    def test_auth_register_and_login(self, client):
        """Test user registration and login flow."""
        # Register
        response = client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "testpass123"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
