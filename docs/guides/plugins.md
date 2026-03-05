# Plugin Development Guide

This guide covers how to create custom plugins for Mrki.

## Overview

Mrki's plugin system allows you to extend functionality by creating custom actions that can be used in workflows and tasks.

## Plugin Structure

A basic plugin consists of:

```
my_plugin/
├── __init__.py
├── actions.py
└── config.py
```

## Creating a Plugin

### 1. Define Your Action

```python
# my_plugin/actions.py
from mrki.actions import Action, register_action

@register_action("my_plugin.my_action")
class MyAction(Action):
    """My custom action.
    
    Args:
        message: The message to display.
        count: Number of times to repeat.
    
    Returns:
        A dictionary with the result.
    """
    
    def execute(self, params: dict) -> dict:
        message = params.get("message", "Hello")
        count = params.get("count", 1)
        
        result = {
            "messages": [message] * count,
            "total": count
        }
        
        return result
```

### 2. Create Plugin Entry Point

```python
# my_plugin/__init__.py
from my_plugin.actions import MyAction

__all__ = ["MyAction"]
```

### 3. Add Configuration (Optional)

```python
# my_plugin/config.py
from pydantic import BaseModel

class MyPluginConfig(BaseModel):
    """Configuration for my plugin."""
    default_message: str = "Hello from My Plugin"
    max_count: int = 100
```

## Action Types

### Simple Action

```python
@register_action("example.echo")
class EchoAction(Action):
    """Echo a message."""
    
    def execute(self, params: dict) -> dict:
        return {"output": params.get("message", "")}
```

### Async Action

```python
import asyncio

@register_action("example.async_action")
class AsyncAction(Action):
    """An async action example."""
    
    async def execute(self, params: dict) -> dict:
        await asyncio.sleep(params.get("delay", 1))
        return {"status": "completed"}
```

### Action with Validation

```python
from pydantic import BaseModel, validator

class MyActionParams(BaseModel):
    url: str
    timeout: int = 30
    
    @validator("timeout")
    def validate_timeout(cls, v):
        if v < 0 or v > 300:
            raise ValueError("Timeout must be between 0 and 300")
        return v

@register_action("example.validated")
class ValidatedAction(Action):
    """Action with parameter validation."""
    
    def execute(self, params: dict) -> dict:
        validated = MyActionParams(**params)
        # Use validated parameters
        return {"url": validated.url, "timeout": validated.timeout}
```

## Best Practices

1. **Use descriptive names**: `my_plugin.action_name`
2. **Document parameters**: Use docstrings
3. **Validate inputs**: Use Pydantic models
4. **Handle errors gracefully**: Return meaningful error messages
5. **Support async operations**: When appropriate
6. **Write tests**: Include unit tests for your actions

## Publishing Plugins

### Package Structure

```
mrki-plugin-myplugin/
├── pyproject.toml
├── README.md
├── LICENSE
└── src/
    └── mrki_plugin_myplugin/
        ├── __init__.py
        └── actions.py
```

### Setup.py Example

```python
# pyproject.toml
[project]
name = "mrki-plugin-myplugin"
version = "1.0.0"
description = "My Mrki plugin"
dependencies = [
    "mrki>=1.0.0",
]

[project.entry-points."mrki.plugins"]
myplugin = "mrki_plugin_myplugin"
```

## Example Plugins

### HTTP Request Plugin

```python
import httpx
from mrki.actions import Action, register_action

@register_action("http.get")
class HttpGetAction(Action):
    """Make HTTP GET request.
    
    Args:
        url: URL to request
        headers: Optional headers dict
        timeout: Request timeout in seconds
    
    Returns:
        Response data including status_code, headers, body
    """
    
    def execute(self, params: dict) -> dict:
        url = params["url"]
        headers = params.get("headers", {})
        timeout = params.get("timeout", 30)
        
        response = httpx.get(url, headers=headers, timeout=timeout)
        
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "json": response.json() if response.headers.get("content-type", "").startswith("application/json") else None
        }
```

### Database Plugin

```python
from sqlalchemy import create_engine, text
from mrki.actions import Action, register_action

@register_action("database.query")
class DatabaseQueryAction(Action):
    """Execute database query.
    
    Args:
        connection: Database connection string
        query: SQL query to execute
        params: Optional query parameters
    
    Returns:
        Query results
    """
    
    def execute(self, params: dict) -> dict:
        connection_url = params["connection"]
        query = params["query"]
        query_params = params.get("params", {})
        
        engine = create_engine(connection_url)
        
        with engine.connect() as conn:
            result = conn.execute(text(query), query_params)
            rows = [dict(row._mapping) for row in result]
        
        return {
            "rows": rows,
            "row_count": len(rows)
        }
```

### Email Plugin

```python
import smtplib
from email.mime.text import MIMEText
from mrki.actions import Action, register_action

@register_action("email.send")
class EmailSendAction(Action):
    """Send email.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body
        smtp_host: SMTP server host
        smtp_port: SMTP server port
        smtp_user: SMTP username
        smtp_password: SMTP password
    
    Returns:
        Send status
    """
    
    def execute(self, params: dict) -> dict:
        msg = MIMEText(params["body"])
        msg["Subject"] = params["subject"]
        msg["From"] = params.get("from", params["smtp_user"])
        msg["To"] = params["to"]
        
        with smtplib.SMTP(params["smtp_host"], params["smtp_port"]) as server:
            server.starttls()
            server.login(params["smtp_user"], params["smtp_password"])
            server.send_message(msg)
        
        return {"sent": True, "to": params["to"]}
```

## Testing Plugins

```python
# tests/test_my_plugin.py
import pytest
from my_plugin.actions import MyAction

class TestMyAction:
    def test_execute(self):
        action = MyAction()
        result = action.execute({"message": "Hello", "count": 3})
        
        assert result["total"] == 3
        assert len(result["messages"]) == 3
        assert all(m == "Hello" for m in result["messages"])
```

## Troubleshooting

### Plugin Not Loading

1. Check plugin is in the plugins directory
2. Verify `__init__.py` exists
3. Check for syntax errors
4. Review logs for error messages

### Action Not Found

1. Verify action is registered with `@register_action`
2. Check action name is correct
3. Ensure plugin is enabled in config

## Resources

- [Built-in Actions Reference](../api/actions.md)
- [Plugin API Documentation](../api/plugins.md)
- [Example Plugins Repository](https://github.com/mrki/plugins)
