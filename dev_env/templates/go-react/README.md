# Go + React Stack Template

This is a Go + React stack project scaffolded by Mrki.

## Project Structure

```
myapp/
├── backend/           # Go application
│   ├── cmd/          # Application entry points
│   │   └── api/      # API server
│   ├── internal/     # Private application code
│   │   ├── config/   # Configuration
│   │   ├── db/       # Database connection
│   │   ├── handlers/ # HTTP handlers
│   │   ├── models/   # Data models
│   │   ├── middleware/ # HTTP middleware
│   │   └── services/ # Business logic
│   ├── pkg/          # Public libraries
│   ├── migrations/   # Database migrations
│   ├── go.mod        # Go module file
│   └── Dockerfile
├── frontend/          # React application
│   ├── public/       # Static files
│   └── src/          # React source code
│       ├── components/  # React components
│       ├── pages/       # Page components
│       ├── hooks/       # Custom hooks
│       ├── services/    # API services
│       └── App.js       # Main app component
├── docker-compose.yml # Docker configuration
└── README.md
```

## Getting Started

### Prerequisites

- Go 1.21+
- Node.js 18+
- PostgreSQL
- Docker (optional)

### Installation

1. Install Go dependencies:
```bash
cd backend
go mod download
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

### Running the Application

**Development Mode:**

```bash
# Start PostgreSQL (if not using Docker)
# Configure your database in .env

# Start backend (from backend directory)
go run cmd/api/main.go

# Start frontend (from frontend directory, new terminal)
npm start
```

**Using Docker:**

```bash
docker-compose up -d
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| GET | /api/items | List all items |
| POST | /api/items | Create new item |
| GET | /api/items/:id | Get item by ID |
| PUT | /api/items/:id | Update item |
| DELETE | /api/items/:id | Delete item |

### Database Migrations

```bash
# Install migrate tool
go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest

# Create new migration
migrate create -ext sql -dir migrations -seq create_users_table

# Apply migrations
migrate -database "${DATABASE_URL}" -path migrations up

# Rollback migration
migrate -database "${DATABASE_URL}" -path migrations down 1
```

### Testing

```bash
# Backend tests
cd backend
go test ./...

# Frontend tests
cd frontend
npm test
```

## Features

- **Gin**: High-performance HTTP web framework
- **GORM**: Fantastic ORM library for Golang
- **PostgreSQL**: Powerful, open source object-relational database
- **React**: Library for building user interfaces
- **Axios**: Promise based HTTP client
- **Docker**: Containerization
- **Hot Reload**: Air for Go development

## Project Layout

This project follows the [Standard Go Project Layout](https://github.com/golang-standards/project-layout).

- `/cmd`: Main applications for this project
- `/internal`: Private application and library code
- `/pkg`: Library code that's OK to use by external applications
- `/migrations`: Database migration files

## Deployment

See `docker-compose.prod.yml` for production deployment configuration.
