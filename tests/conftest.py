"""Pytest configuration and fixtures."""

import os
import pytest
from fastapi.testclient import TestClient

# Disable auth and rate limiting for tests
os.environ["MRKI_AUTH_ENABLED"] = "false"
os.environ["RATE_LIMIT_ENABLED"] = "false"


@pytest.fixture
def client():
    """Create a test client using the real API app."""
    from api.main import create_unified_app

    app = create_unified_app()
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
                "params": {"message": "Hello"},
            },
            {
                "name": "step2",
                "action": "echo",
                "params": {"message": "World"},
                "depends_on": ["step1"],
            },
        ],
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for tests."""
    return {
        "name": "test-task",
        "description": "Test task description",
        "action": "echo",
        "params": {"message": "Hello"},
    }
