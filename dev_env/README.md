# Mrki - Full-Stack Development Environment

A comprehensive toolkit for building modern full-stack applications with support for multiple languages, databases, and deployment platforms.

## Features

### 🚀 Code Generation
- **Python**: FastAPI, Django, Flask
- **JavaScript/TypeScript**: Express, NestJS, React, Vue, Angular
- **Go**: Gin, Echo, Fiber
- **Rust**: Actix-web, Axum
- **Java**: Spring Boot
- **C#**: .NET Core

### 🗄️ Database Support
- **PostgreSQL**: Schema generation, migrations, ERD diagrams
- **MongoDB**: Mongoose schemas, migrations
- **Redis**: Key patterns, caching strategies
- **MySQL**: Schema generation
- **SQLite**: Development database

### 📡 API Development
- OpenAPI 3.0 specification generation
- Swagger UI integration
- Postman collection export
- Client SDK generation (TypeScript, JavaScript, Python, Go)
- CRUD endpoint scaffolding

### 🐳 Containerization
- Docker & Docker Compose configurations
- Multi-stage builds for production
- Kubernetes manifests
- Nginx reverse proxy setup

### 🧪 Testing
- Unit test generation
- Integration test setup
- E2E test scaffolding (Playwright, Cypress)
- Code coverage configuration

### 🔧 Git Operations
- Conventional commits support
- Branch management (GitFlow)
- Stash operations
- Tag management
- Hook installation

### 🚀 CI/CD
- GitHub Actions workflows
- GitLab CI configuration
- Azure DevOps pipelines
- Jenkins pipelines
- CircleCI configuration
- Travis CI configuration

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/mrki.git
cd mrki

# Install dependencies
pip install -r requirements.txt

# Install as package
pip install -e .
```

## Quick Start

### Scaffold a New Project

```bash
# Create a MERN stack project
mrki scaffold myapp --stack mern --description "My awesome app"

# Create a FastAPI + Vue project
mrki scaffold myapp --stack fastapi-vue

# Create a Go + React project
mrki scaffold myapp --stack go-react
```

### Git Operations

```bash
# Create a conventional commit
mrki git commit -m "Add user authentication" --type feat --scope auth

# Create a feature branch
mrki git branch create --name user-auth --branch-type feature

# Get repository status
mrki git status
```

### Database Operations

```bash
# Generate PostgreSQL schema
mrki db generate-schema --tables '[
  {"name": "users", "columns": [
    {"name": "id", "type": "uuid", "primary_key": true},
    {"name": "email", "type": "string", "unique": true}
  ]}
]' --db-type postgresql

# Generate ERD diagram
mrki db generate-erd --tables '[...]' --format mermaid

# Create migration
mrki db create-migration add_users --up "CREATE TABLE users (...)"
```

### API Development

```bash
# Initialize OpenAPI spec
mrki api init --title "My API" --version 1.0.0

# Add CRUD endpoints
mrki api add-crud User

# Generate TypeScript client
mrki api generate-client typescript --output ./client
```

### Docker & Kubernetes

```bash
# Generate Docker files
mrki docker generate --path ./myapp --stack mern

# Generate Kubernetes manifests
mrki docker k8s --output ./k8s --namespace production
```

### Testing

```bash
# Generate test files
mrki test generate --path ./myapp --stack mern
```

### CI/CD

```bash
# Generate GitHub Actions workflows
mrki cicd --platform github_actions --stack mern

# Generate GitLab CI
mrki cicd --platform gitlab_ci --stack fastapi-vue
```

## Supported Stacks

| Stack | Backend | Frontend | Database |
|-------|---------|----------|----------|
| MERN | Node.js/Express | React | MongoDB |
| PERN | Node.js/Express | React | PostgreSQL |
| Django+React | Django | React | PostgreSQL |
| FastAPI+Vue | FastAPI | Vue.js | PostgreSQL |
| Go+React | Go/Gin | React | PostgreSQL |
| Next.js | Next.js | Next.js | PostgreSQL |
| Rust+React | Rust/Actix | React | PostgreSQL |
| Java+Angular | Spring Boot | Angular | PostgreSQL |
| .NET+React | .NET Core | React | PostgreSQL |

## Project Structure

```
mrki/
├── dev_env/
│   ├── __init__.py
│   ├── cli.py              # Main CLI entry point
│   ├── project_scaffolder.py
│   ├── git_ops.py
│   ├── code_gen/           # Language-specific generators
│   │   ├── __init__.py
│   │   ├── generator.py    # Base generator class
│   │   ├── python_gen.py
│   │   ├── javascript_gen.py
│   │   ├── typescript_gen.py
│   │   ├── go_gen.py
│   │   ├── rust_gen.py
│   │   ├── java_gen.py
│   │   └── csharp_gen.py
│   ├── database/           # Database management
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   ├── schema.py
│   │   └── migrations.py
│   ├── api_builder/        # API development
│   │   ├── __init__.py
│   │   ├── builder.py
│   │   └── openapi.py
│   ├── docker/             # Containerization
│   │   ├── __init__.py
│   │   └── manager.py
│   ├── testing/            # Testing framework
│   │   ├── __init__.py
│   │   └── manager.py
│   ├── cicd.py             # CI/CD generators
│   └── templates/          # Project templates
│       ├── mern/
│       ├── pern/
│       ├── django-react/
│       ├── fastapi-vue/
│       └── go-react/
├── setup.py
├── requirements.txt
└── README.md
```

## Configuration

### Environment Variables

```bash
# Database
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
DB_USER=postgres
DB_PASSWORD=password

# API
API_TITLE="My API"
API_VERSION=1.0.0

# Docker
DOCKER_REGISTRY=ghcr.io
DOCKER_IMAGE=myapp
```

### Configuration File

Create a `mrki.yaml` file in your project root:

```yaml
project:
  name: myapp
  stack: mern
  description: My awesome application

database:
  type: postgresql
  host: localhost
  port: 5432
  name: myapp

api:
  title: My API
  version: 1.0.0
  base_path: /api

docker:
  registry: ghcr.io
  namespace: myorg

cicd:
  platform: github_actions
  branches:
    - main
    - develop
```

## Examples

### Complete Workflow

```bash
# 1. Scaffold a new project
mrki scaffold myapp --stack fastapi-vue --description "My API application"

# 2. Navigate to project
cd myapp

# 3. Initialize git repository
git init
git add .
mrki git commit -m "Initial commit" --type chore

# 4. Generate additional API endpoints
mrki api add-crud Product
mrki api add-crud Order

# 5. Generate database migration
mrki db create-migration add_products --up "CREATE TABLE products (...)"

# 6. Generate test files
mrki test generate --stack fastapi-vue

# 7. Generate CI/CD configuration
mrki cicd --platform github_actions --stack fastapi-vue

# 8. Generate Docker files
mrki docker generate --stack fastapi-vue

# 9. Start development
make dev
```

## API Reference

### Project Scaffolder

```python
from mrki import ProjectScaffolder, ProjectConfig, StackType

config = ProjectConfig(
    name="myapp",
    stack=StackType.MERN,
    description="My app",
    docker=True,
    ci_cd=True,
    testing=True,
)

scaffolder = ProjectScaffolder()
result = scaffolder.scaffold(config)
```

### Git Operations

```python
from mrki import GitOps, CommitMessage

git = GitOps("./myapp")

# Create conventional commit
msg = CommitMessage(
    type="feat",
    scope="auth",
    description="Add user login"
)
git.commit_conventional(msg)

# Create feature branch
git.create_branch("user-auth", branch_type=BranchType.FEATURE)
```

### Database Manager

```python
from mrki import DatabaseManager, DatabaseType

manager = DatabaseManager()

# Generate schema
tables = [...]
schema = manager.generate_schema(tables, DatabaseType.POSTGRESQL)

# Generate ERD
erd = manager.generate_erd(tables, format="mermaid")
```

### API Builder

```python
from mrki import APIBuilder, HTTPMethod, Parameter, ParameterLocation

builder = APIBuilder()
builder.set_info("My API", "1.0.0")

# Add endpoint
endpoint = Endpoint(
    path="/users",
    method=HTTPMethod.GET,
    summary="List users",
    parameters=[
        Parameter("page", ParameterLocation.QUERY, "integer", False),
    ],
)
builder.add_endpoint(endpoint)

# Save OpenAPI spec
builder.save_openapi("openapi.json")
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- 📧 Email: support@mrki.dev
- 💬 Discord: [Join our community](https://discord.gg/mrki)
- 📖 Documentation: [https://docs.mrki.dev](https://docs.mrki.dev)

---

Built with ❤️ by the Mrki Team
