"""Task model and operations."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class Task(BaseModel):
    """Task model.
    
    A task is a single unit of work that can be executed independently.
    
    Attributes:
        id: Unique task identifier.
        name: Task name.
        description: Optional task description.
        action: Action to execute.
        params: Parameters for the action.
        status: Current task status.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    
    Example:
        >>> task = Task(
        ...     name="send-email",
        ...     action="email.send",
        ...     params={"to": "user@example.com", "subject": "Hello"}
        ... )
    """
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    action: str
    params: Dict[str, Any] = Field(default_factory=dict)
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the task.
        
        Args:
            **kwargs: Execution parameters.
        
        Returns:
            Execution results.
        """
        # Placeholder for actual execution logic
        return {
            "task_id": self.id or self.name,
            "status": "completed",
            "result": {},
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat()
        }
    
    def validate(self) -> list:
        """Validate the task definition.
        
        Returns:
            List of validation errors, empty if valid.
        """
        errors = []
        
        if not self.name:
            errors.append("Task name is required")
        
        if not self.action:
            errors.append("Task action is required")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary.
        
        Returns:
            Dictionary representation of the task.
        """
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create task from dictionary.
        
        Args:
            data: Dictionary containing task data.
        
        Returns:
            Task instance.
        """
        return cls(**data)
