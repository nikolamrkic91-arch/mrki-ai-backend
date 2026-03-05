"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for API tests."""
    from fastapi import FastAPI
    
    app = FastAPI()
    
    @app.get("/health")
    def health():
        return {"success": True, "data": {"status": "healthy"}}
    
    @app.get("/api/v1/version")
    def version():
        return {"success": True, "data": {"version": "1.0.0"}}
    
    @app.get("/api/v1/workflows")
    def list_workflows():
        return {"success": True, "data": [], "meta": {"total": 0}}
    
    @app.post("/api/v1/workflows")
    def create_workflow(workflow: dict):
        return {"success": True, "data": workflow}
    
    return TestClient(app)


@pytest.fixture
def sample_workflow_data():
    """Sample workflow data for tests."""
    return {
        "name": "test-workflow",
        "description": "Test workflow description",
        "steps": [
            {
                "name": "step1",
                "action": "echo",
                "params": {"message": "Hello"}
            },
            {
                "name": "step2",
                "action": "echo",
                "params": {"message": "World"},
                "depends_on": ["step1"]
            }
        ]
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for tests."""
    return {
        "name": "test-task",
        "description": "Test task description",
        "action": "echo",
        "params": {"message": "Hello"}
    }
