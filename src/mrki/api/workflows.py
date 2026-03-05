"""Workflows API client."""

from typing import Any, Dict, List, Optional

import httpx


class WorkflowsAPI:
    """API client for workflow operations."""
    
    def __init__(self, client: httpx.Client):
        self._client = client
        self._base_path = "/api/v1/workflows"
    
    def list(
        self,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all workflows.
        
        Args:
            page: Page number for pagination.
            per_page: Number of items per page.
            status: Filter by workflow status.
        
        Returns:
            List of workflows with pagination metadata.
        """
        params = {"page": page, "per_page": per_page}
        if status:
            params["status"] = status
        
        response = self._client.get(self._base_path, params=params)
        response.raise_for_status()
        return response.json()
    
    def get(self, workflow_id: str) -> Dict[str, Any]:
        """Get a workflow by ID.
        
        Args:
            workflow_id: The workflow ID or name.
        
        Returns:
            Workflow details.
        """
        response = self._client.get(f"{self._base_path}/{workflow_id}")
        response.raise_for_status()
        return response.json()
    
    def create(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        description: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new workflow.
        
        Args:
            name: Workflow name.
            steps: List of workflow steps.
            description: Optional workflow description.
            variables: Optional workflow variables.
        
        Returns:
            Created workflow details.
        """
        data = {
            "name": name,
            "steps": steps,
        }
        if description:
            data["description"] = description
        if variables:
            data["variables"] = variables
        
        response = self._client.post(self._base_path, json=data)
        response.raise_for_status()
        return response.json()
    
    def update(
        self,
        workflow_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Update a workflow.
        
        Args:
            workflow_id: The workflow ID or name.
            **kwargs: Fields to update.
        
        Returns:
            Updated workflow details.
        """
        response = self._client.put(
            f"{self._base_path}/{workflow_id}",
            json=kwargs
        )
        response.raise_for_status()
        return response.json()
    
    def delete(self, workflow_id: str) -> None:
        """Delete a workflow.
        
        Args:
            workflow_id: The workflow ID or name.
        """
        response = self._client.delete(f"{self._base_path}/{workflow_id}")
        response.raise_for_status()
    
    def execute(
        self,
        workflow_id: str,
        variables: Optional[Dict[str, Any]] = None,
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a workflow.
        
        Args:
            workflow_id: The workflow ID or name.
            variables: Optional variables to override.
            callback_url: Optional callback URL for completion.
        
        Returns:
            Execution details.
        """
        data = {}
        if variables:
            data["variables"] = variables
        if callback_url:
            data["callback_url"] = callback_url
        
        response = self._client.post(
            f"{self._base_path}/{workflow_id}/execute",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_executions(
        self,
        workflow_id: str,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """Get execution history for a workflow.
        
        Args:
            workflow_id: The workflow ID or name.
            page: Page number for pagination.
            per_page: Number of items per page.
        
        Returns:
            List of executions with pagination metadata.
        """
        params = {"page": page, "per_page": per_page}
        response = self._client.get(
            f"{self._base_path}/{workflow_id}/executions",
            params=params
        )
        response.raise_for_status()
        return response.json()
