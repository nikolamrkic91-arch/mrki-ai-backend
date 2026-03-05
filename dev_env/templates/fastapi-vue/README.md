# FastAPI + Vue Stack Template

This is a FastAPI + Vue stack project scaffolded by Mrki.

## Project Structure

```
myapp/
├── backend/           # FastAPI application
│   ├── app/          # Main application
│   │   ├── api/      # API routes
│   │   ├── core/     # Core configuration
│   │   ├── db/       # Database models
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   └── main.py   # Entry point
│   ├── alembic/      # Database migrations
│   ├── tests/        # Test files
│   └── requirements.txt
├── frontend/          # Vue.js application
│   ├── public/       # Static files
│   └── src/          # Vue source code
│       ├── assets/   # Static assets
│       ├── components/  # Vue components
│       ├── views/       # Page views
│       ├── router/      # Vue Router
│       ├── store/       # Pinia store
│       └── App.vue      # Main app component
├── docker-compose.yml # Docker configuration
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL
- Docker (optional)

### Installation

1. Create virtual environment and install backend dependencies:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

2. Set up the database:
```bash
# Create database
createdb myapp

# Run migrations
alembic upgrade head
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

### Running the Application

**Development Mode:**

```bash
# Start backend (from backend directory)
uvicorn app.main:app --reload

# Start frontend (from frontend directory, new terminal)
npm run dev
```

**Using Docker:**

```bash
docker-compose up -d
```

### API Documentation

FastAPI automatically generates interactive API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| GET | /api/items | List all items |
| POST | /api/items | Create new item |
| GET | /api/items/{id} | Get item by ID |
| PUT | /api/items/{id} | Update item |
| DELETE | /api/items/{id} | Delete item |

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm run test:unit
```

## Features

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **Alembic**: Database migration tool
- **Pydantic**: Data validation using Python type hints
- **Vue 3**: Progressive JavaScript framework
- **Pinia**: State management
- **Vue Router**: Client-side routing
- **Docker**: Containerization

## Deployment

See `docker-compose.prod.yml` for production deployment configuration.
