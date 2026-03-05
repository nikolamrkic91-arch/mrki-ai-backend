"""Execution model and operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StepExecution(BaseModel):
    """Execution details for a single step.
    
    Attributes:
        name: Step name.
        status: Execution status.
        started_at: Start timestamp.
        completed_at: Completion timestamp.
        output: Step output.
        error: Error message if failed.
    """
    name: str
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: Optional[Any] = None
    error: Optional[str] = None


class Execution(BaseModel):
    """Execution model.
    
    Represents the execution of a workflow or task.
    
    Attributes:
        id: Unique execution identifier.
        workflow_id: ID of the workflow being executed.
        task_id: ID of the task being executed (if applicable).
        status: Current execution status.
        steps: Step execution details.
        variables: Execution variables.
        result: Execution result.
        started_at: Start timestamp.
        completed_at: Completion timestamp.
        duration: Execution duration in seconds.
    
    Example:
        >>> execution = Execution(
        ...     workflow_id="wf-123",
        ...     status="running",
        ...     started_at=datetime.utcnow()
        ... )
    """
    id: Optional[str] = None
    workflow_id: Optional[str] = None
    task_id: Optional[str] = None
    status: str = "pending"
    steps: List[StepExecution] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def complete(self, result: Optional[Any] = None) -> None:
        """Mark the execution as completed.
        
        Args:
            result: Optional execution result.
        """
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.result = result
        
        if self.started_at:
            self.duration = (self.completed_at - self.started_at).total_seconds()
    
    def fail(self, error: str) -> None:
        """Mark the execution as failed.
        
        Args:
            error: Error message.
        """
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            self.duration = (self.completed_at - self.started_at).total_seconds()
    
    def cancel(self) -> None:
        """Mark the execution as cancelled."""
        self.status = "cancelled"
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            self.duration = (self.completed_at - self.started_at).total_seconds()
    
    def refresh(self) -> None:
        """Refresh execution status from server.
        
        This is a placeholder for actual refresh logic.
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert execution to dictionary.
        
        Returns:
            Dictionary representation of the execution.
        """
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Execution":
        """Create execution from dictionary.
        
        Args:
            data: Dictionary containing execution data.
        
        Returns:
            Execution instance.
        """
        return cls(**data)
