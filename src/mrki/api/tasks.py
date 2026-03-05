"""Tasks API client."""

from typing import Any, Dict, List, Optional

import httpx


class TasksAPI:
    """API client for task operations."""
    
    def __init__(self, client: httpx.Client):
        self._client = client
        self._base_path = "/api/v1/tasks"
    
    def list(
        self,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """List all tasks.
        
        Args:
            page: Page number for pagination.
            per_page: Number of items per page.
        
        Returns:
            List of tasks with pagination metadata.
        """
        params = {"page": page, "per_page": per_page}
        response = self._client.get(self._base_path, params=params)
        response.raise_for_status()
        return response.json()
    
    def get(self, task_id: str) -> Dict[str, Any]:
        """Get a task by ID.
        
        Args:
            task_id: The task ID or name.
        
        Returns:
            Task details.
        """
        response = self._client.get(f"{self._base_path}/{task_id}")
        response.raise_for_status()
        return response.json()
    
    def create(
        self,
        name: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new task.
        
        Args:
            name: Task name.
            action: Action to execute.
            params: Optional action parameters.
            description: Optional task description.
        
        Returns:
            Created task details.
        """
        data = {
            "name": name,
            "action": action,
        }
        if params:
            data["params"] = params
        if description:
            data["description"] = description
        
        response = self._client.post(self._base_path, json=data)
        response.raise_for_status()
        return response.json()
    
    def update(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """Update a task.
        
        Args:
            task_id: The task ID or name.
            **kwargs: Fields to update.
        
        Returns:
            Updated task details.
        """
        response = self._client.put(
            f"{self._base_path}/{task_id}",
            json=kwargs
        )
        response.raise_for_status()
        return response.json()
    
    def delete(self, task_id: str) -> None:
        """Delete a task.
        
        Args:
            task_id: The task ID or name.
        """
        response = self._client.delete(f"{self._base_path}/{task_id}")
        response.raise_for_status()
    
    def execute(self, task_id: str) -> Dict[str, Any]:
        """Execute a task.
        
        Args:
            task_id: The task ID or name.
        
        Returns:
            Execution results.
        """
        response = self._client.post(f"{self._base_path}/{task_id}/execute")
        response.raise_for_status()
        return response.json()
    
    def get_logs(
        self,
        task_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get task execution logs.
        
        Args:
            task_id: The task ID or name.
            limit: Maximum number of log entries.
            offset: Offset for pagination.
        
        Returns:
            Log entries.
        """
        params = {"limit": limit, "offset": offset}
        response = self._client.get(
            f"{self._base_path}/{task_id}/logs",
            params=params
        )
        response.raise_for_status()
        return response.json()
