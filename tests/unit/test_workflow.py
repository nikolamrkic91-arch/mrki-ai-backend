"""Unit tests for Workflow model."""

import pytest
from datetime import datetime

from mrki.core.workflow import Workflow, WorkflowStep


class TestWorkflow:
    """Test cases for Workflow model."""
    
    def test_workflow_creation(self):
        """Test basic workflow creation."""
        workflow = Workflow(
            name="test-workflow",
            steps=[
                WorkflowStep(name="step1", action="echo", params={"message": "Hello"})
            ]
        )
        
        assert workflow.name == "test-workflow"
        assert len(workflow.steps) == 1
        assert workflow.steps[0].name == "step1"
    
    def test_workflow_validation_valid(self):
        """Test validation of valid workflow."""
        workflow = Workflow(
            name="test-workflow",
            steps=[
                WorkflowStep(name="step1", action="echo"),
                WorkflowStep(name="step2", action="echo", depends_on=["step1"])
            ]
        )
        
        errors = workflow.validate()
        assert len(errors) == 0
    
    def test_workflow_validation_duplicate_names(self):
        """Test validation catches duplicate step names."""
        workflow = Workflow(
            name="test-workflow",
            steps=[
                WorkflowStep(name="step1", action="echo"),
                WorkflowStep(name="step1", action="echo")
            ]
        )
        
        errors = workflow.validate()
        assert len(errors) == 1
        assert "Duplicate step names" in errors[0]
    
    def test_workflow_validation_missing_dependency(self):
        """Test validation catches missing dependencies."""
        workflow = Workflow(
            name="test-workflow",
            steps=[
                WorkflowStep(name="step1", action="echo", depends_on=["nonexistent"])
            ]
        )
        
        errors = workflow.validate()
        assert len(errors) == 1
        assert "not found" in errors[0]
    
    def test_workflow_validation_circular_dependency(self):
        """Test validation catches circular dependencies."""
        workflow = Workflow(
            name="test-workflow",
            steps=[
                WorkflowStep(name="step1", action="echo", depends_on=["step2"]),
                WorkflowStep(name="step2", action="echo", depends_on=["step1"])
            ]
        )
        
        errors = workflow.validate()
        assert len(errors) == 1
        assert "Circular dependency" in errors[0]
    
    def test_workflow_to_dict(self):
        """Test workflow serialization to dict."""
        workflow = Workflow(
            name="test-workflow",
            description="Test description",
            steps=[
                WorkflowStep(name="step1", action="echo", params={"message": "Hello"})
            ]
        )
        
        data = workflow.to_dict()
        
        assert data["name"] == "test-workflow"
        assert data["description"] == "Test description"
        assert len(data["steps"]) == 1
    
    def test_workflow_from_dict(self):
        """Test workflow deserialization from dict."""
        data = {
            "name": "test-workflow",
            "steps": [
                {"name": "step1", "action": "echo", "params": {"message": "Hello"}}
            ]
        }
        
        workflow = Workflow.from_dict(data)
        
        assert workflow.name == "test-workflow"
        assert len(workflow.steps) == 1
        assert workflow.steps[0].params["message"] == "Hello"


class TestWorkflowStep:
    """Test cases for WorkflowStep model."""
    
    def test_step_creation(self):
        """Test basic step creation."""
        step = WorkflowStep(
            name="test-step",
            action="echo",
            params={"message": "Hello"}
        )
        
        assert step.name == "test-step"
        assert step.action == "echo"
        assert step.params["message"] == "Hello"
    
    def test_step_with_dependencies(self):
        """Test step with dependencies."""
        step = WorkflowStep(
            name="test-step",
            action="echo",
            depends_on=["step1", "step2"]
        )
        
        assert len(step.depends_on) == 2
        assert "step1" in step.depends_on
        assert "step2" in step.depends_on
    
    def test_step_default_params(self):
        """Test step default parameters."""
        step = WorkflowStep(name="test-step", action="echo")
        
        assert step.params == {}
        assert step.depends_on == []
