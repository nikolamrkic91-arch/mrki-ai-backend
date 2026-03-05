# Examples

This page contains practical examples of using Mrki for various automation tasks.

## Table of Contents

- [Basic Examples](#basic-examples)
- [Data Processing](#data-processing)
- [API Integration](#api-integration)
- [Scheduled Tasks](#scheduled-tasks)
- [Error Handling](#error-handling)

## Basic Examples

### Hello World

```yaml
name: hello-world
description: Simple hello world workflow

steps:
  - name: greet
    action: echo
    params:
      message: "Hello, World!"
```

### Multiple Steps

```yaml
name: multi-step
description: Workflow with multiple steps

steps:
  - name: step1
    action: echo
    params:
      message: "Step 1 completed"
  
  - name: step2
    action: echo
    params:
      message: "Step 2 completed"
    depends_on:
      - step1
  
  - name: step3
    action: echo
    params:
      message: "Step 3 completed"
    depends_on:
      - step2
```

## Data Processing

### Process CSV File

```yaml
name: process-csv
description: Process a CSV file and save results

variables:
  input_file: "/data/input.csv"
  output_file: "/data/output.json"

steps:
  - name: read-csv
    action: file.read
    params:
      path: "{{ variables.input_file }}"
  
  - name: parse-csv
    action: transform.csv_to_json
    params:
      data: "{{ steps.read-csv.output }}"
    depends_on:
      - read-csv
  
  - name: process-data
    action: transform.map
    params:
      data: "{{ steps.parse-csv.output }}"
      operation: "uppercase_names"
    depends_on:
      - parse-csv
  
  - name: save-results
    action: file.write
    params:
      path: "{{ variables.output_file }}"
      content: "{{ steps.process-data.output | to_json }}"
    depends_on:
      - process-data
```

### Database ETL

```yaml
name: database-etl
description: Extract, transform, and load data

variables:
  source_db: "postgresql://user:pass@source/db"
  target_db: "postgresql://user:pass@target/db"

steps:
  - name: extract
    action: database.query
    params:
      connection: "{{ variables.source_db }}"
      query: "SELECT * FROM source_table WHERE created_at > NOW() - INTERVAL '1 day'"
  
  - name: transform
    action: transform.apply
    params:
      data: "{{ steps.extract.output }}"
      transformations:
        - normalize_email
        - format_phone
    depends_on:
      - extract
  
  - name: load
    action: database.insert
    params:
      connection: "{{ variables.target_db }}"
      table: target_table
      data: "{{ steps.transform.output }}"
    depends_on:
      - transform
```

## API Integration

### REST API Workflow

```yaml
name: api-integration
description: Integrate with external REST API

variables:
  api_base: "https://api.example.com/v1"
  api_key: "{{ env.API_KEY }}"

steps:
  - name: fetch-users
    action: http.get
    params:
      url: "{{ variables.api_base }}/users"
      headers:
        Authorization: "Bearer {{ variables.api_key }}"
  
  - name: process-users
    action: transform.filter
    params:
      data: "{{ steps.fetch-users.output }}"
      condition: "active == true"
    depends_on:
      - fetch-users
  
  - name: notify
    action: webhook.post
    params:
      url: "https://hooks.slack.com/services/..."
      body:
        text: "Processed {{ steps.process-users.output | length }} users"
    depends_on:
      - process-users
```

### Webhook Handler

```yaml
name: webhook-handler
description: Handle incoming webhook and process data

steps:
  - name: validate-payload
    action: validate.json_schema
    params:
      schema: "{{ env.WEBHOOK_SCHEMA }}"
  
  - name: process-event
    action: custom.process_webhook
    params:
      event: "{{ input.event_type }}"
      data: "{{ input.payload }}"
    depends_on:
      - validate-payload
  
  - name: send-acknowledgment
    action: http.post
    params:
      url: "{{ input.callback_url }}"
      body:
        status: "received"
        id: "{{ steps.process-event.output.id }}"
    depends_on:
      - process-event
```

## Scheduled Tasks

### Daily Report

```yaml
name: daily-report
description: Generate and send daily report

variables:
  report_date: "{{ now() | format_date('YYYY-MM-DD') }}"

steps:
  - name: generate-report
    action: report.generate
    params:
      template: "daily_report"
      date: "{{ variables.report_date }}"
  
  - name: save-report
    action: file.write
    params:
      path: "/reports/daily_{{ variables.report_date }}.pdf"
      content: "{{ steps.generate-report.output }}"
    depends_on:
      - generate-report
  
  - name: email-report
    action: email.send
    params:
      to: "management@example.com"
      subject: "Daily Report - {{ variables.report_date }}"
      body: "Please find attached the daily report."
      attachments:
        - "/reports/daily_{{ variables.report_date }}.pdf"
    depends_on:
      - save-report
```

Schedule this workflow:

```bash
mrki schedule create \
  --name daily-report \
  --workflow daily-report \
  --cron "0 9 * * *" \
  --timezone "America/New_York"
```

### Cleanup Job

```yaml
name: cleanup-job
description: Clean up old files and data

variables:
  retention_days: 30

steps:
  - name: cleanup-logs
    action: filesystem.delete_old
    params:
      path: "/var/log/app"
      pattern: "*.log"
      older_than_days: "{{ variables.retention_days }}"
  
  - name: cleanup-temp
    action: filesystem.delete_old
    params:
      path: "/tmp"
      pattern: "app_*"
      older_than_days: 7
  
  - name: archive-database
    action: database.archive
    params:
      connection: "{{ env.DATABASE_URL }}"
      table: events
      older_than_days: "{{ variables.retention_days }}"
      archive_table: events_archive
```

## Error Handling

### Retry Logic

```yaml
name: with-retry
description: Workflow with automatic retry

steps:
  - name: unreliable-operation
    action: http.get
    params:
      url: "https://api.example.com/data"
    on_error:
      action: retry
      retry_count: 3
      retry_delay: 5
      retry_backoff: exponential
```

### Fallback Action

```yaml
name: with-fallback
description: Workflow with fallback action

steps:
  - name: primary-api
    action: http.get
    params:
      url: "https://primary-api.example.com/data"
    on_error:
      action: fallback
      fallback_step: secondary-api
  
  - name: secondary-api
    action: http.get
    params:
      url: "https://secondary-api.example.com/data"
```

### Conditional Execution

```yaml
name: conditional
description: Workflow with conditional steps

steps:
  - name: check-condition
    action: condition.evaluate
    params:
      expression: "{{ env.ENVIRONMENT }} == 'production'"
  
  - name: production-only
    action: notify.send
    params:
      message: "Running in production"
    condition: "{{ steps.check-condition.output }} == true"
  
  - name: always-run
    action: log.write
    params:
      message: "This runs regardless"
```

## Advanced Examples

### Parallel Processing

```yaml
name: parallel-processing
description: Process data in parallel

steps:
  - name: fetch-data
    action: http.get
    params:
      url: "https://api.example.com/items"
  
  - name: process-batch-1
    action: transform.process
    params:
      data: "{{ steps.fetch-data.output[0:100] }}"
    depends_on:
      - fetch-data
  
  - name: process-batch-2
    action: transform.process
    params:
      data: "{{ steps.fetch-data.output[100:200] }}"
    depends_on:
      - fetch-data
  
  - name: process-batch-3
    action: transform.process
    params:
      data: "{{ steps.fetch-data.output[200:300] }}"
    depends_on:
      - fetch-data
  
  - name: merge-results
    action: transform.merge
    params:
      sources:
        - "{{ steps.process-batch-1.output }}"
        - "{{ steps.process-batch-2.output }}"
        - "{{ steps.process-batch-3.output }}"
    depends_on:
      - process-batch-1
      - process-batch-2
      - process-batch-3
```

### Multi-Environment Deployment

```yaml
name: deploy-app
description: Deploy application to multiple environments

variables:
  version: "{{ input.version }}"
  environments:
    - staging
    - production

steps:
  - name: build
    action: docker.build
    params:
      tag: "myapp:{{ variables.version }}"
  
  - name: deploy-staging
    action: kubernetes.deploy
    params:
      environment: staging
      image: "myapp:{{ variables.version }}"
    depends_on:
      - build
  
  - name: test-staging
    action: test.run
    params:
      environment: staging
      suite: integration
    depends_on:
      - deploy-staging
  
  - name: deploy-production
    action: kubernetes.deploy
    params:
      environment: production
      image: "myapp:{{ variables.version }}"
    depends_on:
      - test-staging
    condition: "{{ steps.test-staging.output.passed }} == true"
```

## Using with Python

```python
import mrki

# Create client
client = mrki.Client()

# Create workflow from YAML
with open("workflow.yaml") as f:
    import yaml
    workflow_def = yaml.safe_load(f)

workflow = client.workflows.create(**workflow_def)

# Execute
execution = workflow.execute()

# Monitor
while execution.status == "running":
    execution.refresh()
    time.sleep(1)

print(f"Status: {execution.status}")
print(f"Result: {execution.result}")
```

## Using with CLI

```bash
# Create workflow
mrki workflow create --name my-workflow --file workflow.yaml

# Execute
mrki workflow run my-workflow

# Schedule
mrki schedule create \
  --name hourly-task \
  --workflow my-workflow \
  --cron "0 * * * *"

# Monitor
mrki execution logs <execution-id>
```
