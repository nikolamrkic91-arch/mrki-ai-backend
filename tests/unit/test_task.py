"""Unit tests for Task model."""

import pytest
from datetime import datetime

from mrki.core.task import Task


class TestTask:
    """Test cases for Task model."""
    
    def test_task_creation(self):
        """Test basic task creation."""
        task = Task(
            name="test-task",
            action="echo",
            params={"message": "Hello"}
        )
        
        assert task.name == "test-task"
        assert task.action == "echo"
        assert task.params["message"] == "Hello"
    
    def test_task_validation_valid(self):
        """Test validation of valid task."""
        task = Task(
            name="test-task",
            action="echo"
        )
        
        errors = task.validate()
        assert len(errors) == 0
    
    def test_task_validation_missing_name(self):
        """Test validation catches missing name."""
        task = Task(
            name="",
            action="echo"
        )
        
        errors = task.validate()
        assert len(errors) == 1
        assert "name is required" in errors[0]
    
    def test_task_validation_missing_action(self):
        """Test validation catches missing action."""
        task = Task(
            name="test-task",
            action=""
        )
        
        errors = task.validate()
        assert len(errors) == 1
        assert "action is required" in errors[0]
    
    def test_task_to_dict(self):
        """Test task serialization to dict."""
        task = Task(
            name="test-task",
            description="Test description",
            action="echo",
            params={"message": "Hello"}
        )
        
        data = task.to_dict()
        
        assert data["name"] == "test-task"
        assert data["description"] == "Test description"
        assert data["action"] == "echo"
    
    def test_task_from_dict(self):
        """Test task deserialization from dict."""
        data = {
            "name": "test-task",
            "action": "echo",
            "params": {"message": "Hello"}
        }
        
        task = Task.from_dict(data)
        
        assert task.name == "test-task"
        assert task.action == "echo"
        assert task.params["message"] == "Hello"
    
    def test_task_execute(self):
        """Test task execution."""
        task = Task(
            name="test-task",
            action="echo",
            params={"message": "Hello"}
        )
        
        result = task.execute()
        
        assert result["status"] == "completed"
        assert result["task_id"] == "test-task"
        assert "started_at" in result
        assert "completed_at" in result
    
    def test_task_default_params(self):
        """Test task default parameters."""
        task = Task(name="test-task", action="echo")
        
        assert task.params == {}
        assert task.status == "active"
