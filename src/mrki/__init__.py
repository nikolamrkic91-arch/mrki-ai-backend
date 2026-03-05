"""Mrki - A powerful workflow automation platform.

Mrki provides a comprehensive solution for creating, scheduling, and monitoring
automated workflows and tasks. It features a flexible plugin system, REST API,
CLI tools, and a web interface for easy management.

Example:
    Basic usage::

        import mrki

        # Create a client
        client = mrki.Client()

        # Create a workflow
        workflow = client.workflows.create(
            name="my-workflow",
            steps=[{"name": "step1", "action": "echo", "params": {"message": "Hello"}}]
        )

        # Execute the workflow
        result = workflow.execute()
        print(result)
"""

try:
    from mrki._version import version as __version__
except ImportError:
    __version__ = "unknown"

from mrki.client import Client
from mrki.core.workflow import Workflow
from mrki.core.task import Task

__all__ = [
    "__version__",
    "Client",
    "Workflow",
    "Task",
]
