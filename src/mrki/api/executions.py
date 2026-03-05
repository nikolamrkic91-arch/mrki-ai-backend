"""Executions API client."""

from typing import Any, Dict, Optional

import httpx


class ExecutionsAPI:
    """API client for execution operations."""
    
    def __init__(self, client: httpx.Client):
        self._client = client
        self._base_path = "/api/v1/executions"
    
    def list(
        self,
        page: int = 1,
        per_page: int = 20,
        workflow: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all executions.
        
        Args:
            page: Page number for pagination.
            per_page: Number of items per page.
            workflow: Filter by workflow ID.
            status: Filter by execution status.
        
        Returns:
            List of executions with pagination metadata.
        """
        params = {"page": page, "per_page": per_page}
        if workflow:
            params["workflow"] = workflow
        if status:
            params["status"] = status
        
        response = self._client.get(self._base_path, params=params)
        response.raise_for_status()
        return response.json()
    
    def get(self, execution_id: str) -> Dict[str, Any]:
        """Get an execution by ID.
        
        Args:
            execution_id: The execution ID.
        
        Returns:
            Execution details.
        """
        response = self._client.get(f"{self._base_path}/{execution_id}")
        response.raise_for_status()
        return response.json()
    
    def cancel(self, execution_id: str) -> Dict[str, Any]:
        """Cancel a running execution.
        
        Args:
            execution_id: The execution ID.
        
        Returns:
            Updated execution details.
        """
        response = self._client.post(f"{self._base_path}/{execution_id}/cancel")
        response.raise_for_status()
        return response.json()
    
    def get_logs(
        self,
        execution_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get execution logs.
        
        Args:
            execution_id: The execution ID.
            limit: Maximum number of log entries.
            offset: Offset for pagination.
        
        Returns:
            Log entries.
        """
        params = {"limit": limit, "offset": offset}
        response = self._client.get(
            f"{self._base_path}/{execution_id}/logs",
            params=params
        )
        response.raise_for_status()
        return response.json()
