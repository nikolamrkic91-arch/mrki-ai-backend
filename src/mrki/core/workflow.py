"""Workflow model and operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    """A single step in a workflow.
    
    Attributes:
        name: Unique name for the step.
        action: Action to execute.
        params: Parameters for the action.
        depends_on: List of step names this step depends on.
        on_error: Error handling configuration.
    """
    name: str
    action: str
    params: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    on_error: Optional[Dict[str, Any]] = None


class Workflow(BaseModel):
    """Workflow model.
    
    A workflow is a collection of steps that are executed in a specific order
    based on their dependencies.
    
    Attributes:
        id: Unique workflow identifier.
        name: Workflow name.
        description: Optional workflow description.
        version: Workflow version.
        steps: List of workflow steps.
        variables: Workflow-level variables.
        status: Current workflow status.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    
    Example:
        >>> workflow = Workflow(
        ...     name="example",
        ...     steps=[
        ...         WorkflowStep(name="step1", action="echo", params={"message": "Hello"})
        ...     ]
        ... )
    """
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    version: str = "1.0"
    steps: List[WorkflowStep]
    variables: Dict[str, Any] = Field(default_factory=dict)
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def execute(self, **kwargs) -> "Execution":
        """Execute the workflow.
        
        Args:
            **kwargs: Execution parameters.
        
        Returns:
            Execution instance.
        """
        # Placeholder for actual execution logic
        from mrki.core.execution import Execution
        return Execution(
            workflow_id=self.id or self.name,
            status="pending",
            started_at=datetime.utcnow()
        )
    
    def validate(self) -> List[str]:
        """Validate the workflow definition.
        
        Returns:
            List of validation errors, empty if valid.
        """
        errors = []
        
        # Check for duplicate step names
        names = [step.name for step in self.steps]
        if len(names) != len(set(names)):
            errors.append("Duplicate step names found")
        
        # Check dependencies exist
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in names:
                    errors.append(f"Dependency '{dep}' not found for step '{step.name}'")
        
        # Check for circular dependencies
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str, graph: Dict[str, List[str]]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, graph):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        graph = {step.name: step.depends_on for step in self.steps}
        for step_name in graph:
            if step_name not in visited:
                if has_cycle(step_name, graph):
                    errors.append("Circular dependency detected")
                    break
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary.
        
        Returns:
            Dictionary representation of the workflow.
        """
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        """Create workflow from dictionary.
        
        Args:
            data: Dictionary containing workflow data.
        
        Returns:
            Workflow instance.
        """
        return cls(**data)
