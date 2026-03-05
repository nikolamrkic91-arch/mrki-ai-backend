# Mrki Integration Guide

This guide covers how to integrate all components of the Mrki platform into a cohesive, working system.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Module Integration](#module-integration)
- [API Integration](#api-integration)
- [Docker Deployment](#docker-deployment)
- [Configuration](#configuration)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)

## Architecture Overview

Mrki is a modular platform with the following components:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Mrki Platform                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Core   │  │   Visual    │  │  DevEnv  │  │     MoE      │  │
│  │Orchestr.│  │   Engine    │  │          │  │   Router     │  │
│  │ 50+     │  │Visual-to-   │  │Full-Stack│  │  64 Experts  │  │
│  │ Agents  │  │   Code      │  │   Dev    │  │              │  │
│  └────┬────┘  └──────┬──────┘  └────┬─────┘  └──────┬───────┘  │
│       │              │              │               │          │
│  ┌────┴──────────────┴──────────────┴───────────────┴───────┐  │
│  │                    Unified API (FastAPI)                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌───────────────────────────┴───────────────────────────────┐  │
│  │              Infrastructure & Services                     │  │
│  │  PostgreSQL  │  Redis  │  MinIO  │  Prometheus  │ Grafana │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Module Responsibilities

| Module | Purpose | Key Features |
|--------|---------|--------------|
| **core** | Agent orchestration | 50+ sub-agents, 1,500 parallel tool calls, hierarchical supervision |
| **visual_engine** | Visual processing | Image/video analysis, sketch-to-code, design extraction |
| **dev_env** | Development tools | Project scaffolding, code generation, testing, CI/CD |
| **moe** | Expert routing | 64-expert MoE, top-k routing, load balancing |
| **gamedev** | Game development | Unity/Unreal/Godot code generation |
| **ide_integration** | IDE support | VS Code/Cursor/Zed extensions, LSP, DAP |
| **infrastructure** | Cloud deployment | K8s, Terraform, monitoring |

## Quick Start

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- Node.js 18+ (for client)
- Git

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/mrki/mrki.git
cd mrki

# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 2. Start with Docker Compose

```bash
# Start core services only
docker-compose up -d

# Start full development stack
docker-compose -f docker-compose.full.yml up -d

# Start with GPU support
docker-compose -f docker-compose.full.yml --profile gpu up -d

# Start with monitoring
docker-compose -f docker-compose.full.yml --profile monitoring up -d
```

### 3. Start Locally (Development)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[all]"

# Run the main application
python main.py

# Or with custom config
python main.py --config config.yaml --host 0.0.0.0 --port 8080
```

### 4. Verify Installation

```bash
# Health check
curl http://localhost:8080/health

# API info
curl http://localhost:8080/

# Module health
curl http://localhost:8080/api/v1/health
```

## Module Integration

### Core Orchestrator Integration

The Core module provides agent orchestration capabilities:

```python
from core.orchestrator import MrkiOrchestrator, SubTask

# Initialize orchestrator
orchestrator = MrkiOrchestrator()
await orchestrator.initialize()

# Create and execute a task
task = SubTask(
    name="analyze_code",
    description="Analyze Python code for issues",
    agent_type="code_analyzer",
    input_data={"code": "def foo(): pass"}
)

result = await orchestrator.execute_task(task)
```

### Visual Engine Integration

The Visual Engine provides visual-to-code capabilities:

```python
from visual_engine.analyzer import ImageAnalyzer
from visual_engine.code_generator import CodeGenerator, Framework, StyleSystem

# Analyze an image
analyzer = ImageAnalyzer()
result = analyzer.analyze_image("screenshot.png")

# Generate code from analysis
generator = CodeGenerator()
code = generator.generate_from_analysis(
    analysis=result.to_dict(),
    framework=Framework.REACT,
    style_system=StyleSystem.TAILWIND,
    component_name="MyComponent"
)
```

### Development Environment Integration

The Dev Environment provides full-stack development tools:

```python
from dev_env import ProjectScaffolder, APIBuilder

# Scaffold a new project
scaffolder = ProjectScaffolder()
scaffolder.scaffold(
    project_type="web",
    project_name="my-app",
    output_dir="./projects"
)

# Generate API endpoints
builder = APIBuilder()
builder.generate_api(
    name="UserAPI",
    endpoints=[
        {"method": "GET", "path": "/users", "handler": "list_users"},
        {"method": "POST", "path": "/users", "handler": "create_user"},
    ],
    framework="fastapi"
)
```

### MoE Integration

The MoE module provides expert routing:

```python
from moe.router import create_router
import torch

# Create router
router = create_router(
    input_dim=768,
    num_experts=64,
    top_k=2
)

# Route inputs to experts
inputs = torch.randn(4, 128, 768)
decision = router.route(inputs, training=False)

print(f"Selected experts: {decision.expert_indices}")
print(f"Routing time: {decision.routing_time_ms}ms")
```

### Game Development Integration

The GameDev module provides game code generation:

```python
from gamedev.code_gen.generator import (
    GameCodeGenerator,
    EngineType,
    TemplateType
)

generator = GameCodeGenerator()

# Generate Unity player controller
result = generator.generate_player_controller(
    engine=EngineType.UNITY,
    class_name="HeroController",
    namespace="AdventureGame"
)

print(result.code)
```

## API Integration

### Unified API Structure

The unified API combines all module endpoints:

```
/api/v1/
├── /           - API info
├── /health     - Health check
├── /core       - Core orchestration
│   ├── /health
│   ├── /execute
│   └── /metrics
├── /visual     - Visual engine
│   ├── /health
│   ├── /analyze/image
│   └── /generate/code
├── /dev        - Development environment
│   ├── /health
│   ├── /scaffold
│   └── /generate/api
├── /moe        - Mixture of Experts
│   ├── /health
│   ├── /experts
│   └── /route
└── /gamedev    - Game development
    ├── /health
    ├── /engines
    └── /generate
```

### API Usage Examples

#### Execute a Task

```bash
curl -X POST http://localhost:8080/api/v1/core/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "code_review",
    "description": "Review Python code",
    "agent_type": "code_reviewer",
    "input": {"code": "def hello(): print('world')"}
  }'
```

#### Generate Code from Visual

```bash
curl -X POST http://localhost:8080/api/v1/visual/generate/code \
  -H "Content-Type: application/json" \
  -d '{
    "analysis": {"elements": [...], "colors": {...}},
    "framework": "react",
    "style_system": "tailwind",
    "component_name": "Header"
  }'
```

#### Scaffold a Project

```bash
curl -X POST http://localhost:8080/api/v1/dev/scaffold \
  -H "Content-Type: application/json" \
  -d '{
    "project_type": "web",
    "project_name": "my-app",
    "output_dir": "./output"
  }'
```

#### Route to MoE Experts

```bash
curl -X POST http://localhost:8080/api/v1/moe/route \
  -H "Content-Type: application/json" \
  -d '{
    "input_dim": 768,
    "batch_size": 4,
    "seq_len": 128
  }'
```

#### Generate Game Code

```bash
curl -X POST http://localhost:8080/api/v1/gamedev/generate \
  -H "Content-Type: application/json" \
  -d '{
    "engine": "unity",
    "template": "player_controller",
    "class_name": "HeroController",
    "namespace": "AdventureGame"
  }'
```

## Docker Deployment

### Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Network                          │
│  ┌──────────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │   mrki-api   │  │ postgres │  │  redis   │  │  minio  │ │
│  │   :8080      │  │  :5432   │  │  :6379   │  │  :9000  │ │
│  └──────────────┘  └──────────┘  └──────────┘  └─────────┘ │
│  ┌──────────────┐  ┌──────────┐  ┌──────────┐              │
│  │visual-engine │  │moe-inf.  │  │gamedev   │              │
│  │   :8001      │  │  :8003   │  │  :8004   │              │
│  └──────────────┘  └──────────┘  └──────────┘              │
│  ┌──────────────┐  ┌──────────┐  ┌──────────┐              │
│  │celery-worker │  │prometheus│  │ grafana  │              │
│  │              │  │  :9090   │  │  :3000   │              │
│  └──────────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### Docker Compose Profiles

| Profile | Services | Use Case |
|---------|----------|----------|
| (default) | Core services only | Minimal setup |
| `gpu` | GPU-enabled visual engine | ML inference |
| `monitoring` | Prometheus, Grafana, Jaeger | Observability |
| `training` | MoE training service | Model training |
| `proxy` | Nginx reverse proxy | Production |
| `dev` | pgAdmin, MailHog, Redis Commander | Development |

### Environment-Specific Deployment

#### Development

```bash
# Start with dev tools
docker-compose -f docker-compose.full.yml --profile dev up -d

# Access:
# - API: http://localhost:8080
# - pgAdmin: http://localhost:5050
# - MailHog: http://localhost:8025
# - Redis Commander: http://localhost:8081
```

#### Staging

```bash
# Start with monitoring
docker-compose -f docker-compose.full.yml --profile monitoring up -d

# Access:
# - API: http://localhost:8080
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000
# - Jaeger: http://localhost:16686
```

#### Production

```bash
# Start with proxy and monitoring
docker-compose -f docker-compose.full.yml \
  --profile proxy \
  --profile monitoring \
  up -d

# Configure SSL certificates in nginx/ssl/
# Update nginx/nginx.conf for your domain
```

## Configuration

### Configuration Hierarchy

Configuration is loaded in the following order (later overrides earlier):

1. Default values in code
2. `config.yaml` file
3. Environment variables (`MRKI_*`)
4. Command-line arguments

### Key Configuration Files

| File | Purpose |
|------|---------|
| `config.yaml` | Main configuration |
| `.env` | Environment variables |
| `docker-compose.yml` | Docker services |
| `docker-compose.full.yml` | Full stack services |

### Environment Variables

See `.env.example` for all available options. Key variables:

```bash
# Required
MRKI_SECRET_KEY=your-secure-key
MRKI_DATABASE_URL=postgresql://...
MRKI_REDIS_URL=redis://...

# Optional
MRKI_LOG_LEVEL=INFO
MRKI_SERVER_PORT=8080
MRKI_SERVER_WORKERS=4
```

### Module Configuration

Each module can be configured independently:

```yaml
# config.yaml
modules:
  core:
    enabled: true
    config:
      max_concurrent_agents: 100
      max_parallel_tool_calls: 1500
  
  visual_engine:
    enabled: true
    config:
      model_path: ./models/visual
      device: cuda
  
  moe:
    enabled: true
    config:
      num_experts: 64
      top_k: 2
```

## Development Workflow

### Local Development

```bash
# 1. Start infrastructure services
docker-compose up -d postgres redis minio

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Run tests
pytest

# 4. Start development server
python main.py --debug

# 5. Make changes and hot-reload
```

### Adding a New Module

1. Create module directory:
```bash
mkdir my_module
touch my_module/__init__.py
```

2. Implement module interface:
```python
# my_module/__init__.py
class MyModule:
    async def initialize(self, config):
        # Initialize module
        pass
    
    async def shutdown(self):
        # Cleanup
        pass
```

3. Register in main.py:
```python
# main.py
try:
    from my_module import MyModule
    module_registry.register("my_module", MyModule())
except ImportError:
    pass
```

4. Add API routes:
```python
# api/main.py
my_module_router = APIRouter(prefix="/my_module")

@my_module_router.get("/health")
async def my_module_health():
    return {"status": "healthy"}

router.include_router(my_module_router)
```

### Testing Integration

```bash
# Run all tests
pytest

# Run specific module tests
pytest tests/core/
pytest tests/visual_engine/

# Run integration tests
pytest tests/integration/ -v

# Run with coverage
pytest --cov=mrki --cov-report=html
```

## Troubleshooting

### Common Issues

#### Module Not Available

```
Error: Module 'visual_engine' not available
```

**Solution:**
```bash
# Check if module is installed
pip install -e ".[visual]"

# Or install all extras
pip install -e ".[all]"
```

#### Database Connection Failed

```
Error: Could not connect to database
```

**Solution:**
```bash
# Start PostgreSQL
docker-compose up -d postgres

# Check connection
psql $MRKI_DATABASE_URL -c "SELECT 1"
```

#### Redis Connection Failed

```
Error: Redis connection error
```

**Solution:**
```bash
# Start Redis
docker-compose up -d redis

# Test connection
redis-cli ping
```

#### Port Already in Use

```
Error: Address already in use
```

**Solution:**
```bash
# Find process using port
lsof -i :8080

# Kill process or use different port
python main.py --port 8081
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Environment variable
export MRKI_LOG_LEVEL=DEBUG

# Command line
python main.py --debug

# Docker
MRKI_LOG_LEVEL=DEBUG docker-compose up
```

### Health Checks

```bash
# Check all services
curl http://localhost:8080/health

# Check specific module
curl http://localhost:8080/api/v1/core/health
curl http://localhost:8080/api/v1/visual/health

# Check Docker containers
docker-compose ps
docker-compose logs <service>
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f mrki-api

# View with tail
docker-compose logs -f --tail=100 mrki-api
```

## API Reference

### Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/api/v1/` | GET | API v1 info |
| `/api/v1/health` | GET | Detailed health |
| `/api/v1/core/execute` | POST | Execute task |
| `/api/v1/visual/analyze/image` | POST | Analyze image |
| `/api/v1/visual/generate/code` | POST | Generate code |
| `/api/v1/dev/scaffold` | POST | Scaffold project |
| `/api/v1/moe/route` | POST | Route to experts |
| `/api/v1/gamedev/generate` | POST | Generate game code |

### Authentication

API key authentication (if enabled):

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8080/api/v1/...
```

### Rate Limiting

Default limits: 100 requests per 60 seconds per IP.

Configure in `.env`:
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

## Support

- Documentation: https://mrki.readthedocs.io
- Issues: https://github.com/mrki/mrki/issues
- Discussions: https://github.com/mrki/mrki/discussions
