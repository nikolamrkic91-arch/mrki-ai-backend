"""Mrki client for programmatic API access."""

from typing import Optional
import httpx


class Client:
    """Main client for interacting with Mrki API.
    
    This client provides a high-level interface for creating and managing
    workflows, tasks, and schedules through the Mrki REST API.
    
    Args:
        base_url: The base URL of the Mrki server.
        api_key: Optional API key for authentication.
        timeout: Request timeout in seconds.
    
    Example:
        >>> client = Client("http://localhost:8080", api_key="my-key")
        >>> workflows = client.workflows.list()
        >>> print(workflows)
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self) -> None:
        """Close the client connection."""
        self._client.close()
    
    @property
    def workflows(self) -> "WorkflowsAPI":
        """Access the workflows API."""
        from mrki.api.workflows import WorkflowsAPI
        return WorkflowsAPI(self._client)
    
    @property
    def tasks(self) -> "TasksAPI":
        """Access the tasks API."""
        from mrki.api.tasks import TasksAPI
        return TasksAPI(self._client)
    
    @property
    def schedules(self) -> "SchedulesAPI":
        """Access the schedules API."""
        from mrki.api.schedules import SchedulesAPI
        return SchedulesAPI(self._client)
    
    @property
    def executions(self) -> "ExecutionsAPI":
        """Access the executions API."""
        from mrki.api.executions import ExecutionsAPI
        return ExecutionsAPI(self._client)
    
    def health(self) -> dict:
        """Check the health status of the server.
        
        Returns:
            Health status information.
        """
        response = self._client.get("/health")
        response.raise_for_status()
        return response.json()
    
    def version(self) -> dict:
        """Get the server version information.
        
        Returns:
            Version information.
        """
        response = self._client.get("/api/v1/version")
        response.raise_for_status()
        return response.json()
