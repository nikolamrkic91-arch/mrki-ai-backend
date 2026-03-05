"""Integration tests for API endpoints."""

import pytest


@pytest.mark.integration
class TestAPI:
    """Integration tests for API."""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_version_endpoint(self, client):
        """Test version endpoint."""
        response = client.get("/api/v1/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data["data"]
    
    def test_list_workflows(self, client):
        """Test listing workflows."""
        response = client.get("/api/v1/workflows")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    def test_create_workflow(self, client):
        """Test creating a workflow."""
        workflow_data = {
            "name": "test-workflow",
            "steps": [
                {"name": "step1", "action": "echo", "params": {"message": "Hello"}}
            ]
        }
        response = client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["name"] == "test-workflow"
