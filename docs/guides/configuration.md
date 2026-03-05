# Configuration Guide

This guide covers all configuration options for Mrki.

## Configuration Sources

Mrki loads configuration from multiple sources (in order of precedence):

1. Environment variables
2. Configuration file (`~/.config/mrki/config.yaml`)
3. Command-line arguments
4. Default values

## Configuration File

### Location

Default configuration file locations:

- **Linux/macOS**: `~/.config/mrki/config.yaml`
- **Windows**: `%APPDATA%\mrki\config.yaml`
- **Custom**: Set via `MRKI_CONFIG_FILE` environment variable

### Basic Structure

```yaml
# Mrki Configuration File
# Version: 1.0

# Server configuration
server:
  host: 0.0.0.0
  port: 8080
  debug: false
  workers: 4
  timeout: 30

# Database configuration
database:
  url: sqlite:///~/.config/mrki/mrki.db
  pool_size: 5
  max_overflow: 10
  pool_timeout: 30

# Security configuration
security:
  secret_key: "your-secret-key-here"
  jwt_algorithm: HS256
  jwt_expiration: 3600
  api_key_header: X-API-Key
  allowed_hosts:
    - localhost
    - 127.0.0.1

# Logging configuration
logging:
  level: INFO
  format: json  # or 'text'
  file: ~/.config/mrki/mrki.log
  max_size: 10MB
  max_files: 5

# Plugin configuration
plugins:
  directory: ~/.config/mrki/plugins
  auto_load: true
  enabled:
    - http
    - database
    - email

# Scheduler configuration
scheduler:
  enabled: true
  max_workers: 10
  timezone: UTC

# Web interface configuration
web:
  enabled: true
  title: Mrki
  theme: default
  custom_css: null
  custom_js: null
```

## Environment Variables

All configuration options can be set via environment variables using the prefix `MRKI_` and uppercase names with underscores.

### Examples

```bash
# Server settings
export MRKI_SERVER_HOST=0.0.0.0
export MRKI_SERVER_PORT=8080
export MRKI_SERVER_DEBUG=false

# Database settings
export MRKI_DATABASE_URL=postgresql://user:pass@localhost/mrki
export MRKI_DATABASE_POOL_SIZE=10

# Security settings
export MRKI_SECURITY_SECRET_KEY=your-secret-key
export MRKI_SECURITY_JWT_EXPIRATION=7200

# Logging settings
export MRKI_LOGGING_LEVEL=DEBUG
export MRKI_LOGGING_FORMAT=text
```

### Variable Mapping

| Config Path | Environment Variable |
|-------------|---------------------|
| `server.host` | `MRKI_SERVER_HOST` |
| `server.port` | `MRKI_SERVER_PORT` |
| `database.url` | `MRKI_DATABASE_URL` |
| `security.secret_key` | `MRKI_SECURITY_SECRET_KEY` |
| `logging.level` | `MRKI_LOGGING_LEVEL` |
| `plugins.directory` | `MRKI_PLUGINS_DIRECTORY` |

## Server Configuration

### Options

```yaml
server:
  # Host to bind to
  host: 0.0.0.0
  
  # Port to listen on
  port: 8080
  
  # Enable debug mode
  debug: false
  
  # Number of worker processes
  workers: 4
  
  # Request timeout in seconds
  timeout: 30
  
  # Maximum request body size
  max_body_size: 10MB
  
  # Enable CORS
  cors:
    enabled: true
    origins:
      - "http://localhost:3000"
    allow_credentials: true
    allow_methods:
      - GET
      - POST
      - PUT
      - DELETE
    allow_headers:
      - "*"
  
  # SSL/TLS configuration
  ssl:
    enabled: false
    cert_file: /path/to/cert.pem
    key_file: /path/to/key.pem
```

## Database Configuration

### SQLite (Default)

```yaml
database:
  url: sqlite:///~/.config/mrki/mrki.db
```

### PostgreSQL

```yaml
database:
  url: postgresql://user:password@localhost:5432/mrki
  pool_size: 5
  max_overflow: 10
  pool_timeout: 30
  pool_recycle: 3600
```

### MySQL

```yaml
database:
  url: mysql+pymysql://user:password@localhost:3306/mrki
  pool_size: 5
  max_overflow: 10
```

### Connection Pool Settings

```yaml
database:
  # Initial pool size
  pool_size: 5
  
  # Maximum connections beyond pool_size
  max_overflow: 10
  
  # Timeout for getting connection from pool
  pool_timeout: 30
  
  # Recycle connections after N seconds
  pool_recycle: 3600
  
  # Enable connection pre-ping
  pool_pre_ping: true
```

## Security Configuration

### Authentication

```yaml
security:
  # Secret key for JWT signing
  secret_key: "change-this-in-production"
  
  # JWT algorithm
  jwt_algorithm: HS256
  
  # JWT expiration in seconds
  jwt_expiration: 3600
  
  # Refresh token expiration
  refresh_expiration: 604800
  
  # API key header name
  api_key_header: X-API-Key
  
  # Allowed hosts
  allowed_hosts:
    - localhost
    - 127.0.0.1
    - mrki.example.com
  
  # Rate limiting
  rate_limit:
    enabled: true
    requests: 100
    window: 60
  
  # Password policy
  password_policy:
    min_length: 8
    require_uppercase: true
    require_lowercase: true
    require_numbers: true
    require_special: true
```

### API Keys

```yaml
security:
  api_keys:
    - name: production
      key: "prod-api-key-here"
      permissions:
        - workflows:read
        - workflows:write
        - tasks:execute
    - name: readonly
      key: "readonly-api-key-here"
      permissions:
        - workflows:read
        - tasks:read
```

## Logging Configuration

### Basic Logging

```yaml
logging:
  # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  level: INFO
  
  # Log format: json, text
  format: json
  
  # Log file path (optional)
  file: ~/.config/mrki/mrki.log
  
  # Maximum log file size
  max_size: 10MB
  
  # Number of backup files to keep
  max_files: 5
```

### Advanced Logging

```yaml
logging:
  version: 1
  disable_existing_loggers: false
  
  formatters:
    json:
      class: pythonjsonlogger.jsonlogger.JsonFormatter
      format: '%(asctime)s %(name)s %(levelname)s %(message)s'
    text:
      format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  
  handlers:
    console:
      class: logging.StreamHandler
      formatter: text
      level: INFO
    
    file:
      class: logging.handlers.RotatingFileHandler
      filename: ~/.config/mrki/mrki.log
      formatter: json
      maxBytes: 10485760
      backupCount: 5
      level: DEBUG
    
    syslog:
      class: logging.handlers.SysLogHandler
      address: /dev/log
      formatter: text
      level: WARNING
  
  loggers:
    mrki:
      level: DEBUG
      handlers: [console, file]
      propagate: false
    
    uvicorn:
      level: INFO
      handlers: [console]
      propagate: false
  
  root:
    level: WARNING
    handlers: [console, syslog]
```

## Plugin Configuration

### Plugin Settings

```yaml
plugins:
  # Plugin directory
  directory: ~/.config/mrki/plugins
  
  # Auto-load plugins on startup
  auto_load: true
  
  # List of enabled plugins
  enabled:
    - http
    - database
    - email
    - filesystem
  
  # Plugin-specific configuration
  config:
    http:
      timeout: 30
      max_retries: 3
      user_agent: "Mrki/1.0"
    
    database:
      default_connection: main
      connections:
        main:
          url: postgresql://user:pass@localhost/db
        analytics:
          url: postgresql://user:pass@analytics/db
    
    email:
      smtp_host: smtp.gmail.com
      smtp_port: 587
      smtp_user: user@gmail.com
      smtp_password: "${EMAIL_PASSWORD}"
      use_tls: true
```

## Scheduler Configuration

```yaml
scheduler:
  # Enable scheduler
  enabled: true
  
  # Maximum concurrent workers
  max_workers: 10
  
  # Default timezone
  timezone: UTC
  
  # Job defaults
  job_defaults:
    coalesce: true
    max_instances: 1
    misfire_grace_time: 3600
  
  # Executor configuration
  executors:
    default:
      type: threadpool
      max_workers: 20
  
  # Job store configuration
  jobstores:
    default:
      type: sqlalchemy
      url: sqlite:///~/.config/mrki/scheduler.db
```

## Web Interface Configuration

```yaml
web:
  # Enable web interface
  enabled: true
  
  # Dashboard title
  title: Mrki
  
  # Theme: default, dark, light
  theme: default
  
  # Custom CSS file
  custom_css: null
  
  # Custom JavaScript file
  custom_js: null
  
  # Navigation configuration
  navigation:
    - name: Dashboard
      icon: home
      path: /
    - name: Workflows
      icon: workflow
      path: /workflows
    - name: Tasks
      icon: task
      path: /tasks
    - name: Schedules
      icon: schedule
      path: /schedules
    - name: Logs
      icon: log
      path: /logs
  
  # Feature flags
  features:
    workflow_editor: true
    task_runner: true
    log_viewer: true
    settings_panel: true
```

## Cache Configuration

```yaml
cache:
  # Cache backend: memory, redis, memcached
  backend: memory
  
  # Default TTL in seconds
  default_ttl: 300
  
  # Maximum cache size (for memory backend)
  max_size: 1000
  
  # Redis configuration
  redis:
    url: redis://localhost:6379/0
    password: null
    ssl: false
  
  # Memcached configuration
  memcached:
    servers:
      - localhost:11211
    username: null
    password: null
```

## Message Queue Configuration

```yaml
queue:
  # Queue backend: memory, redis, rabbitmq, sqs
  backend: memory
  
  # Redis configuration
  redis:
    url: redis://localhost:6379/1
  
  # RabbitMQ configuration
  rabbitmq:
    url: amqp://guest:guest@localhost:5672/
    queue: mrki_tasks
    exchange: mrki
  
  # SQS configuration
  sqs:
    region: us-east-1
    queue_url: https://sqs.us-east-1.amazonaws.com/123456789/mrki
    access_key_id: "${AWS_ACCESS_KEY_ID}"
    secret_access_key: "${AWS_SECRET_ACCESS_KEY}"
```

## Monitoring Configuration

```yaml
monitoring:
  # Enable metrics collection
  enabled: true
  
  # Metrics endpoint
  endpoint: /metrics
  
  # Prometheus configuration
  prometheus:
    enabled: true
    port: 9090
  
  # Health check configuration
  health:
    enabled: true
    endpoint: /health
    checks:
      - database
      - cache
      - queue
  
  # Tracing configuration
  tracing:
    enabled: false
    backend: jaeger
    jaeger:
      host: localhost
      port: 6831
```

## Backup Configuration

```yaml
backup:
  # Enable automatic backups
  enabled: true
  
  # Backup schedule (cron expression)
  schedule: "0 2 * * *"
  
  # Backup directory
  directory: ~/.config/mrki/backups
  
  # Number of backups to keep
  keep_count: 7
  
  # Backup targets
  targets:
    - database
    - workflows
    - configurations
  
  # Remote storage
  remote:
    enabled: false
    type: s3  # s3, gcs, azure
    s3:
      bucket: mrki-backups
      region: us-east-1
      access_key_id: "${AWS_ACCESS_KEY_ID}"
      secret_access_key: "${AWS_SECRET_ACCESS_KEY}"
```

## Complete Example

```yaml
# Mrki Production Configuration

server:
  host: 0.0.0.0
  port: 8080
  debug: false
  workers: 4
  cors:
    enabled: true
    origins:
      - "https://mrki.example.com"
  ssl:
    enabled: true
    cert_file: /etc/ssl/certs/mrki.crt
    key_file: /etc/ssl/private/mrki.key

database:
  url: postgresql://mrki:${DB_PASSWORD}@db.example.com:5432/mrki
  pool_size: 10
  max_overflow: 20

security:
  secret_key: "${SECRET_KEY}"
  jwt_expiration: 3600
  allowed_hosts:
    - mrki.example.com
  rate_limit:
    enabled: true
    requests: 1000
    window: 60

logging:
  level: INFO
  format: json
  file: /var/log/mrki/mrki.log
  max_size: 100MB
  max_files: 10

plugins:
  directory: /opt/mrki/plugins
  auto_load: true
  enabled:
    - http
    - database
    - email
    - slack
    - webhook

cache:
  backend: redis
  redis:
    url: redis://cache.example.com:6379/0

queue:
  backend: rabbitmq
  rabbitmq:
    url: amqp://mrki:${MQ_PASSWORD}@mq.example.com:5672/

monitoring:
  enabled: true
  prometheus:
    enabled: true
    port: 9090
```

## Configuration Validation

Validate your configuration:

```bash
# Check configuration file
mrki config validate

# Show effective configuration
mrki config show

# Test database connection
mrki config test database

# Test all connections
mrki config test all
```

## Environment-Specific Configurations

### Development

```yaml
# config.development.yaml
server:
  debug: true
  port: 8080

logging:
  level: DEBUG
  format: text
```

### Staging

```yaml
# config.staging.yaml
server:
  debug: false
  port: 8080

database:
  url: postgresql://mrki:pass@staging-db/mrki
```

### Production

```yaml
# config.production.yaml
server:
  debug: false
  port: 8080
  workers: 8

database:
  url: postgresql://mrki:${DB_PASSWORD}@prod-db/mrki
  pool_size: 20

security:
  secret_key: "${SECRET_KEY}"
```

Use environment-specific configs:

```bash
export MRKI_ENV=production
mrki server start
```
