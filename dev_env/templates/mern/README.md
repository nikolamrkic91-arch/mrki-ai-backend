# MERN Stack Template

This is a MERN (MongoDB, Express, React, Node.js) stack project scaffolded by Mrki.

## Project Structure

```
myapp/
├── backend/           # Express.js API
│   ├── config/       # Configuration files
│   ├── controllers/  # Route controllers
│   ├── middleware/   # Express middleware
│   ├── models/       # Mongoose models
│   ├── routes/       # API routes
│   ├── utils/        # Utility functions
│   └── server.js     # Entry point
├── frontend/          # React application
│   ├── public/       # Static files
│   └── src/          # React source code
│       ├── components/  # React components
│       ├── pages/       # Page components
│       ├── hooks/       # Custom hooks
│       ├── context/     # React context
│       ├── utils/       # Utility functions
│       └── App.js       # Main app component
├── docker-compose.yml # Docker configuration
└── README.md
```

## Getting Started

### Prerequisites

- Node.js (v18+)
- MongoDB
- Docker (optional)

### Installation

1. Install backend dependencies:
```bash
cd backend
npm install
```

2. Install frontend dependencies:
```bash
cd frontend
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running the Application

**Development Mode:**

```bash
# Start MongoDB (if not using Docker)
mongod

# Start backend (from backend directory)
npm run dev

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
| GET | /api/health | Health check |
| GET | /api/items | List all items |
| POST | /api/items | Create new item |
| GET | /api/items/:id | Get item by ID |
| PUT | /api/items/:id | Update item |
| DELETE | /api/items/:id | Delete item |

### Testing

```bash
# Backend tests
cd backend
npm test

# Frontend tests
cd frontend
npm test
```

## Deployment

See `docker-compose.prod.yml` for production deployment configuration.
