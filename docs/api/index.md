# API Reference

Complete reference for the Mrki API.

## Overview

Mrki provides a comprehensive REST API for programmatic access to all features. The API follows RESTful principles and uses JSON for data exchange.

## Base URL

```
http://localhost:8080/api/v1
```

## Authentication

The API supports multiple authentication methods:

### API Key

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8080/api/v1/workflows
```

### JWT Token

```bash
# Login to get token
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token
curl -H "Authorization: Bearer JWT_TOKEN" \
  http://localhost:8080/api/v1/workflows
```

### Basic Auth

```bash
curl -u username:password \
  http://localhost:8080/api/v1/workflows
```

## Response Format

All responses follow a standard format:

### Success Response

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "name",
      "issue": "required"
    }
  }
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `BAD_REQUEST` | 400 | Invalid request format |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Validation failed |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

## Pagination

List endpoints support pagination:

```bash
# Request specific page
curl "http://localhost:8080/api/v1/workflows?page=2&per_page=50"
```

Response includes pagination metadata:

```json
{
  "success": true,
  "data": [...],
  "meta": {
    "page": 2,
    "per_page": 50,
    "total": 150,
    "total_pages": 3,
    "has_next": true,
    "has_prev": true
  }
}
```

## Filtering

Filter results using query parameters:

```bash
# Filter by status
curl "http://localhost:8080/api/v1/workflows?status=active"

# Filter by multiple values
curl "http://localhost:8080/api/v1/workflows?status=active,pending"

# Filter by date range
curl "http://localhost:8080/api/v1/workflows?created_after=2024-01-01&created_before=2024-12-31"

# Full-text search
curl "http://localhost:8080/api/v1/workflows?q=data+processing"
```

## Sorting

Sort results using the `sort` parameter:

```bash
# Sort by name ascending
curl "http://localhost:8080/api/v1/workflows?sort=name"

# Sort by created date descending
curl "http://localhost:8080/api/v1/workflows?sort=-created_at"

# Multiple sort fields
curl "http://localhost:8080/api/v1/workflows?sort=status,-created_at"
```

## Rate Limiting

API requests are rate-limited:

- 100 requests per minute for authenticated users
- 20 requests per minute for anonymous users

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Endpoints

### Workflows

#### List Workflows

```http
GET /api/v1/workflows
```

Query parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number |
| `per_page` | integer | Items per page (max 100) |
| `status` | string | Filter by status |
| `q` | string | Search query |
| `sort` | string | Sort field |

Response:

```json
{
  "success": true,
  "data": [
    {
      "id": "wf-123",
      "name": "data-processing",
      "description": "Process daily data",
      "status": "active",
      "version": "1.0",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 1
  }
}
```

#### Get Workflow

```http
GET /api/v1/workflows/{id}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "wf-123",
    "name": "data-processing",
    "description": "Process daily data",
    "status": "active",
    "version": "1.0",
    "steps": [
      {
        "name": "fetch-data",
        "action": "http.get",
        "params": {"url": "https://api.example.com/data"},
        "depends_on": []
      }
    ],
    "variables": {},
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

#### Create Workflow

```http
POST /api/v1/workflows
```

Request body:

```json
{
  "name": "my-workflow",
  "description": "My workflow description",
  "steps": [
    {
      "name": "step1",
      "action": "echo",
      "params": {"message": "Hello"}
    }
  ],
  "variables": {
    "api_url": "https://api.example.com"
  }
}
```

#### Update Workflow

```http
PUT /api/v1/workflows/{id}
```

Request body:

```json
{
  "name": "updated-name",
  "description": "Updated description",
  "steps": [...]
}
```

#### Delete Workflow

```http
DELETE /api/v1/workflows/{id}
```

#### Execute Workflow

```http
POST /api/v1/workflows/{id}/execute
```

Request body (optional):

```json
{
  "variables": {
    "override": "value"
  },
  "callback_url": "https://example.com/callback"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "execution_id": "exec-456",
    "status": "pending",
    "started_at": "2024-01-01T00:00:00Z"
  }
}
```

#### Get Workflow Executions

```http
GET /api/v1/workflows/{id}/executions
```

Response:

```json
{
  "success": true,
  "data": [
    {
      "id": "exec-456",
      "status": "completed",
      "started_at": "2024-01-01T00:00:00Z",
      "completed_at": "2024-01-01T00:01:00Z",
      "duration": 60,
      "result": {...}
    }
  ]
}
```

### Tasks

#### List Tasks

```http
GET /api/v1/tasks
```

#### Get Task

```http
GET /api/v1/tasks/{id}
```

#### Create Task

```http
POST /api/v1/tasks
```

Request body:

```json
{
  "name": "my-task",
  "action": "http.get",
  "params": {
    "url": "https://api.example.com/data"
  },
  "description": "Fetch data from API"
}
```

#### Execute Task

```http
POST /api/v1/tasks/{id}/execute
```

Response:

```json
{
  "success": true,
  "data": {
    "execution_id": "exec-789",
    "status": "completed",
    "result": {
      "status_code": 200,
      "body": {...}
    },
    "started_at": "2024-01-01T00:00:00Z",
    "completed_at": "2024-01-01T00:00:01Z"
  }
}
```

#### Get Task Logs

```http
GET /api/v1/tasks/{id}/logs
```

Query parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Number of log entries |
| `offset` | integer | Offset for pagination |
| `level` | string | Filter by log level |

### Schedules

#### List Schedules

```http
GET /api/v1/schedules
```

#### Create Schedule

```http
POST /api/v1/schedules
```

Request body:

```json
{
  "name": "daily-report",
  "workflow": "report-workflow",
  "cron": "0 9 * * *",
  "timezone": "UTC",
  "enabled": true,
  "variables": {
    "report_type": "daily"
  }
}
```

#### Get Schedule

```http
GET /api/v1/schedules/{id}
```

#### Update Schedule

```http
PUT /api/v1/schedules/{id}
```

#### Delete Schedule

```http
DELETE /api/v1/schedules/{id}
```

#### Pause Schedule

```http
POST /api/v1/schedules/{id}/pause
```

#### Resume Schedule

```http
POST /api/v1/schedules/{id}/resume
```

### Executions

#### List Executions

```http
GET /api/v1/executions
```

Query parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `workflow` | string | Filter by workflow ID |
| `status` | string | Filter by status |
| `started_after` | datetime | Filter by start time |

#### Get Execution

```http
GET /api/v1/executions/{id}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "exec-456",
    "workflow_id": "wf-123",
    "status": "completed",
    "steps": [
      {
        "name": "fetch-data",
        "status": "completed",
        "started_at": "2024-01-01T00:00:00Z",
        "completed_at": "2024-01-01T00:00:30Z",
        "output": {...}
      }
    ],
    "variables": {...},
    "result": {...},
    "started_at": "2024-01-01T00:00:00Z",
    "completed_at": "2024-01-01T00:01:00Z",
    "duration": 60
  }
}
```

#### Cancel Execution

```http
POST /api/v1/executions/{id}/cancel
```

#### Get Execution Logs

```http
GET /api/v1/executions/{id}/logs
```

### System

#### Health Check

```http
GET /api/v1/health
```

Response:

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 86400,
    "checks": {
      "database": "ok",
      "cache": "ok",
      "queue": "ok"
    }
  }
}
```

#### Get Metrics

```http
GET /api/v1/metrics
```

Returns Prometheus-compatible metrics.

#### Get Version

```http
GET /api/v1/version
```

Response:

```json
{
  "success": true,
  "data": {
    "version": "1.0.0",
    "commit": "abc123",
    "build_date": "2024-01-01T00:00:00Z"
  }
}
```

## WebSocket API

Real-time updates via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8080/api/v1/ws');

ws.onopen = () => {
  // Subscribe to execution updates
  ws.send(JSON.stringify({
    action: 'subscribe',
    channel: 'executions'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

## SDKs

Official SDKs for popular languages:

- [Python SDK](https://github.com/mrki/mrki-python)
- [JavaScript SDK](https://github.com/mrki/mrki-js)
- [Go SDK](https://github.com/mrki/mrki-go)

## Code Examples

### Python

```python
import mrki

client = mrki.Client("http://localhost:8080", api_key="your-key")

# List workflows
workflows = client.workflows.list()

# Create workflow
workflow = client.workflows.create(
    name="example",
    steps=[{"name": "step1", "action": "echo", "params": {"message": "Hello"}}]
)

# Execute
execution = workflow.execute()
print(execution.id)
```

### JavaScript

```javascript
import { MrkiClient } from '@mrki/sdk';

const client = new MrkiClient({
  baseUrl: 'http://localhost:8080',
  apiKey: 'your-key'
});

// List workflows
const workflows = await client.workflows.list();

// Create workflow
const workflow = await client.workflows.create({
  name: 'example',
  steps: [{ name: 'step1', action: 'echo', params: { message: 'Hello' } }]
});

// Execute
const execution = await workflow.execute();
console.log(execution.id);
```

### cURL

```bash
# List workflows
curl -H "Authorization: Bearer YOUR_KEY" \
  http://localhost:8080/api/v1/workflows

# Create workflow
curl -X POST \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"test","steps":[]}' \
  http://localhost:8080/api/v1/workflows

# Execute workflow
curl -X POST \
  -H "Authorization: Bearer YOUR_KEY" \
  http://localhost:8080/api/v1/workflows/test/execute
```
