"""Schedules API client."""

from typing import Any, Dict, List, Optional

import httpx


class SchedulesAPI:
    """API client for schedule operations."""
    
    def __init__(self, client: httpx.Client):
        self._client = client
        self._base_path = "/api/v1/schedules"
    
    def list(
        self,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """List all schedules.
        
        Args:
            page: Page number for pagination.
            per_page: Number of items per page.
        
        Returns:
            List of schedules with pagination metadata.
        """
        params = {"page": page, "per_page": per_page}
        response = self._client.get(self._base_path, params=params)
        response.raise_for_status()
        return response.json()
    
    def get(self, schedule_id: str) -> Dict[str, Any]:
        """Get a schedule by ID.
        
        Args:
            schedule_id: The schedule ID or name.
        
        Returns:
            Schedule details.
        """
        response = self._client.get(f"{self._base_path}/{schedule_id}")
        response.raise_for_status()
        return response.json()
    
    def create(
        self,
        name: str,
        workflow: str,
        cron: str,
        timezone: str = "UTC",
        enabled: bool = True,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new schedule.
        
        Args:
            name: Schedule name.
            workflow: Workflow ID or name to execute.
            cron: Cron expression for scheduling.
            timezone: Timezone for the schedule.
            enabled: Whether the schedule is enabled.
            variables: Optional variables to pass to the workflow.
        
        Returns:
            Created schedule details.
        """
        data = {
            "name": name,
            "workflow": workflow,
            "cron": cron,
            "timezone": timezone,
            "enabled": enabled,
        }
        if variables:
            data["variables"] = variables
        
        response = self._client.post(self._base_path, json=data)
        response.raise_for_status()
        return response.json()
    
    def update(self, schedule_id: str, **kwargs) -> Dict[str, Any]:
        """Update a schedule.
        
        Args:
            schedule_id: The schedule ID or name.
            **kwargs: Fields to update.
        
        Returns:
            Updated schedule details.
        """
        response = self._client.put(
            f"{self._base_path}/{schedule_id}",
            json=kwargs
        )
        response.raise_for_status()
        return response.json()
    
    def delete(self, schedule_id: str) -> None:
        """Delete a schedule.
        
        Args:
            schedule_id: The schedule ID or name.
        """
        response = self._client.delete(f"{self._base_path}/{schedule_id}")
        response.raise_for_status()
    
    def pause(self, schedule_id: str) -> Dict[str, Any]:
        """Pause a schedule.
        
        Args:
            schedule_id: The schedule ID or name.
        
        Returns:
            Updated schedule details.
        """
        response = self._client.post(f"{self._base_path}/{schedule_id}/pause")
        response.raise_for_status()
        return response.json()
    
    def resume(self, schedule_id: str) -> Dict[str, Any]:
        """Resume a paused schedule.
        
        Args:
            schedule_id: The schedule ID or name.
        
        Returns:
            Updated schedule details.
        """
        response = self._client.post(f"{self._base_path}/{schedule_id}/resume")
        response.raise_for_status()
        return response.json()
