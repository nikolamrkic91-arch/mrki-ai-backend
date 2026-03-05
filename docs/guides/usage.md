# User Guide

This guide covers the basic usage of Mrki for common tasks.

## Table of Contents

- [Getting Started](#getting-started)
- [CLI Usage](#cli-usage)
- [Python API](#python-api)
- [REST API](#rest-api)
- [Web Interface](#web-interface)
- [Workflows](#workflows)
- [Tasks](#tasks)
- [Scheduling](#scheduling)

## Getting Started

After [installing Mrki](installation.md), you can start using it immediately.

### Start the Server

```bash
# Start the Mrki server
mrki server start

# Start with custom port
mrki server start --port 9000

# Start in background
mrki server start --daemon
```

### Verify Installation

```bash
# Check version
mrki --version

# Health check
mrki health

# List available commands
mrki --help
```

## CLI Usage

The Mrki CLI provides powerful commands for managing workflows and tasks.

### Basic Commands

```bash
# Show help
mrki --help

# Show version
mrki --version

# Configuration management
mrki config show
mrki config set key value
mrki config get key
```

### Workflow Management

```bash
# List workflows
mrki workflow list

# Create a workflow
mrki workflow create --name my-workflow --file workflow.yaml

# Get workflow details
mrki workflow get my-workflow

# Execute a workflow
mrki workflow run my-workflow

# Delete a workflow
mrki workflow delete my-workflow
```

### Task Management

```bash
# List tasks
mrki task list

# Create a task
mrki task create --name my-task --action echo --params '{"message": "Hello"}'

# Execute a task
mrki task run my-task

# View task logs
mrki task logs my-task

# Delete a task
mrki task delete my-task
```

### Scheduling

```bash
# List schedules
mrki schedule list

# Create a schedule
mrki schedule create --name daily-report --workflow my-workflow --cron "0 9 * * *"

# Pause a schedule
mrki schedule pause daily-report

# Resume a schedule
mrki schedule resume daily-report

# Delete a schedule
mrki schedule delete daily-report
```

## Python API

Mrki provides a comprehensive Python API for programmatic access.

### Basic Usage

```python
import mrki

# Create a client
client = mrki.Client(base_url="http://localhost:8080")

# Authenticate (if required)
client.authenticate("your-api-key")
```

### Working with Workflows

```python
# Create a workflow
workflow = client.workflows.create(
    name="data-processing",
    description="Process daily data",
    steps=[
        {
            "name": "fetch-data",
            "action": "http.get",
            "params": {"url": "https://api.example.com/data"}
        },
        {
            "name": "process-data",
            "action": "transform.json",
            "params": {"operation": "filter"},
            "depends_on": ["fetch-data"]
        },
        {
            "name": "save-results",
            "action": "database.insert",
            "params": {"table": "results"},
            "depends_on": ["process-data"]
        }
    ]
)

# Execute the workflow
execution = workflow.execute()
print(f"Execution ID: {execution.id}")
print(f"Status: {execution.status}")

# Monitor execution
while execution.status == "running":
    execution.refresh()
    time.sleep(1)

print(f"Final status: {execution.status}")
print(f"Results: {execution.results}")
```

### Working with Tasks

```python
# Create a task
task = client.tasks.create(
    name="send-email",
    action="email.send",
    params={
        "to": "user@example.com",
        "subject": "Hello from Mrki",
        "body": "This is a test email."
    }
)

# Execute the task
result = task.execute()
print(result)

# Get task history
history = task.get_history()
for execution in history:
    print(f"{execution.started_at}: {execution.status}")
```

### Scheduling

```python
# Create a schedule
schedule = client.schedules.create(
    name="daily-cleanup",
    workflow="cleanup-workflow",
    cron="0 2 * * *",  # Run at 2 AM daily
    timezone="UTC"
)

# List all schedules
schedules = client.schedules.list()
for schedule in schedules:
    print(f"{schedule.name}: {schedule.cron}")

# Pause a schedule
schedule.pause()

# Resume a schedule
schedule.resume()

# Delete a schedule
schedule.delete()
```

## REST API

Mrki provides a comprehensive REST API for integration with other systems.

### Authentication

```bash
# Using API key
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8080/api/v1/workflows

# Using basic auth
curl -u username:password \
  http://localhost:8080/api/v1/workflows
```

### API Endpoints

#### Workflows

```bash
# List workflows
curl http://localhost:8080/api/v1/workflows

# Create workflow
curl -X POST http://localhost:8080/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-workflow",
    "steps": [
      {"name": "step1", "action": "echo", "params": {"message": "Hello"}}
    ]
  }'

# Get workflow
curl http://localhost:8080/api/v1/workflows/my-workflow

# Execute workflow
curl -X POST http://localhost:8080/api/v1/workflows/my-workflow/execute

# Delete workflow
curl -X DELETE http://localhost:8080/api/v1/workflows/my-workflow
```

#### Tasks

```bash
# List tasks
curl http://localhost:8080/api/v1/tasks

# Create task
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-task",
    "action": "echo",
    "params": {"message": "Hello"}
  }'

# Execute task
curl -X POST http://localhost:8080/api/v1/tasks/my-task/execute

# Get task logs
curl http://localhost:8080/api/v1/tasks/my-task/logs
```

#### Schedules

```bash
# List schedules
curl http://localhost:8080/api/v1/schedules

# Create schedule
curl -X POST http://localhost:8080/api/v1/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "daily-task",
    "workflow": "my-workflow",
    "cron": "0 9 * * *"
  }'

# Pause schedule
curl -X POST http://localhost:8080/api/v1/schedules/daily-task/pause

# Resume schedule
curl -X POST http://localhost:8080/api/v1/schedules/daily-task/resume
```

## Web Interface

Mrki includes a web interface for visual management.

### Accessing the Dashboard

1. Start the server: `mrki server start`
2. Open your browser: `http://localhost:8080`
3. Log in with your credentials

### Dashboard Features

- **Overview**: System status and recent activity
- **Workflows**: Create, edit, and manage workflows
- **Tasks**: View and execute individual tasks
- **Schedules**: Manage scheduled executions
- **Logs**: View execution logs and history
- **Settings**: Configure system settings

### Creating a Workflow via UI

1. Navigate to **Workflows** → **Create New**
2. Enter workflow name and description
3. Add steps using the visual editor
4. Configure step parameters
5. Save and execute

## Workflows

Workflows are the core concept in Mrki. They define a sequence of steps to be executed.

### Workflow Structure

```yaml
name: example-workflow
description: An example workflow
version: "1.0"

variables:
  api_url: "https://api.example.com"
  timeout: 30

steps:
  - name: fetch-data
    action: http.get
    params:
      url: "{{ variables.api_url }}/data"
      timeout: "{{ variables.timeout }}"
    
  - name: process-data
    action: transform.json
    params:
      input: "{{ steps.fetch-data.output }}"
      operation: filter
    depends_on:
      - fetch-data
  
  - name: save-results
    action: database.insert
    params:
      table: results
      data: "{{ steps.process-data.output }}"
    depends_on:
      - process-data
```

### Variables and Templating

Use Jinja2 templating for dynamic values:

```yaml
params:
  message: "Hello, {{ user.name }}!"
  timestamp: "{{ now() }}"
  data: "{{ steps.previous_step.output.data }}"
```

### Error Handling

```yaml
steps:
  - name: risky-operation
    action: http.post
    params:
      url: "https://api.example.com/risky"
    on_error:
      action: continue  # or 'stop', 'retry'
      retry_count: 3
      retry_delay: 5
```

## Tasks

Tasks are individual units of work that can be executed independently.

### Built-in Actions

| Action | Description | Parameters |
|--------|-------------|------------|
| `echo` | Print a message | `message` |
| `http.get` | HTTP GET request | `url`, `headers`, `params` |
| `http.post` | HTTP POST request | `url`, `headers`, `body` |
| `database.query` | Execute SQL query | `query`, `connection` |
| `file.read` | Read file contents | `path` |
| `file.write` | Write to file | `path`, `content` |
| `email.send` | Send email | `to`, `subject`, `body` |

### Custom Actions

Create custom actions using plugins:

```python
from mrki.actions import Action, register_action

@register_action("custom.my-action")
class MyAction(Action):
    def execute(self, params):
        # Your logic here
        return {"result": "success"}
```

## Scheduling

Schedule workflows to run at specific times or intervals.

### Cron Expressions

```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday = 0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

### Examples

```bash
# Every minute
* * * * *

# Every hour at minute 0
0 * * * *

# Every day at 9 AM
0 9 * * *

# Every Monday at 8 AM
0 8 * * 1

# Every first day of month at midnight
0 0 1 * *
```

## Best Practices

1. **Use meaningful names** for workflows and tasks
2. **Add descriptions** to document purpose
3. **Handle errors** gracefully
4. **Use variables** for reusable values
5. **Monitor executions** and review logs
6. **Test workflows** before scheduling
7. **Use version control** for workflow definitions

## Next Steps

- Learn about [Configuration](configuration.md)
- Explore the [API Reference](../api/index.md)
- Read about [Plugins](plugins.md)
- Check out [Examples](examples.md)
