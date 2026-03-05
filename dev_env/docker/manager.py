#!/usr/bin/env python3
"""
Mrki Docker Manager
Generates Docker configurations and manages containers
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class ServiceType(Enum):
    """Docker service types"""
    WEB = "web"
    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    WORKER = "worker"
    QUEUE = "queue"


@dataclass
class DockerService:
    """Docker Compose service definition"""
    name: str
    image: str
    service_type: ServiceType
    ports: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    volumes: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    networks: List[str] = field(default_factory=list)
    command: Optional[str] = None
    build_context: Optional[str] = None
    dockerfile: Optional[str] = None
    healthcheck: Optional[Dict[str, Any]] = None
    restart: str = "unless-stopped"


class DockerManager:
    """Docker configuration manager"""
    
    def __init__(self, output_path: str = "."):
        self.output_path = Path(output_path)
    
    def generate_docker_files(self, project_path: Path, stack_type: str) -> List[str]:
        """Generate Docker files for a project"""
        created_files = []
        
        # Generate Dockerfile for backend
        dockerfile_backend = project_path / "backend" / "Dockerfile"
        dockerfile_backend.parent.mkdir(parents=True, exist_ok=True)
        dockerfile_backend.write_text(self._get_backend_dockerfile(stack_type))
        created_files.append(str(dockerfile_backend))
        
        # Generate Dockerfile for frontend
        dockerfile_frontend = project_path / "frontend" / "Dockerfile"
        dockerfile_frontend.parent.mkdir(parents=True, exist_ok=True)
        dockerfile_frontend.write_text(self._get_frontend_dockerfile())
        created_files.append(str(dockerfile_frontend))
        
        # Generate docker-compose.yml
        compose_file = project_path / "docker-compose.yml"
        compose_file.write_text(self._get_docker_compose(stack_type))
        created_files.append(str(compose_file))
        
        # Generate docker-compose.prod.yml
        compose_prod_file = project_path / "docker-compose.prod.yml"
        compose_prod_file.write_text(self._get_docker_compose_prod(stack_type))
        created_files.append(str(compose_prod_file))
        
        # Generate .dockerignore
        dockerignore = project_path / ".dockerignore"
        dockerignore.write_text(self._get_dockerignore())
        created_files.append(str(dockerignore))
        
        # Generate nginx config for production
        nginx_dir = project_path / "nginx"
        nginx_dir.mkdir(exist_ok=True)
        nginx_conf = nginx_dir / "nginx.conf"
        nginx_conf.write_text(self._get_nginx_config())
        created_files.append(str(nginx_conf))
        
        return created_files
    
    def _get_backend_dockerfile(self, stack_type: str) -> str:
        """Get backend Dockerfile based on stack"""
        if "django" in stack_type.lower():
            return self._get_python_dockerfile()
        elif "fastapi" in stack_type.lower():
            return self._get_python_dockerfile()
        elif "go" in stack_type.lower():
            return self._get_go_dockerfile()
        elif "rust" in stack_type.lower():
            return self._get_rust_dockerfile()
        elif "java" in stack_type.lower() or "spring" in stack_type.lower():
            return self._get_java_dockerfile()
        elif "dotnet" in stack_type.lower():
            return self._get_dotnet_dockerfile()
        else:
            return self._get_node_dockerfile()
    
    def _get_node_dockerfile(self) -> str:
        """Get Node.js Dockerfile"""
        return '''# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source
COPY . .

# Production stage
FROM node:18-alpine AS production

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001

# Copy dependencies and source
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nodejs:nodejs /app .

USER nodejs

EXPOSE 3000

CMD ["node", "server.js"]
'''
    
    def _get_python_dockerfile(self) -> str:
        """Get Python Dockerfile"""
        return '''# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential libpq-dev && \\
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim AS production

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy dependencies
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application
COPY . .

# Change ownership
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "main:app"]
'''
    
    def _get_go_dockerfile(self) -> str:
        """Get Go Dockerfile"""
        return '''# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Install dependencies
RUN apk add --no-cache git

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source
COPY . .

# Build
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# Production stage
FROM alpine:latest

WORKDIR /root/

# Copy binary
COPY --from=builder /app/main .

EXPOSE 8080

CMD ["./main"]
'''
    
    def _get_rust_dockerfile(self) -> str:
        """Get Rust Dockerfile"""
        return '''# Build stage
FROM rust:1.74-slim AS builder

WORKDIR /app

# Copy Cargo files
COPY Cargo.toml Cargo.lock ./
COPY src ./src

# Build release
RUN cargo build --release

# Production stage
FROM debian:bookworm-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && \\
    rm -rf /var/lib/apt/lists/*

# Copy binary
COPY --from=builder /app/target/release/app ./

EXPOSE 8080

CMD ["./app"]
'''
    
    def _get_java_dockerfile(self) -> str:
        """Get Java Dockerfile"""
        return '''# Build stage
FROM maven:3.9-eclipse-temurin-17-alpine AS builder

WORKDIR /app

# Copy pom.xml and download dependencies
COPY pom.xml .
RUN mvn dependency:go-offline

# Copy source and build
COPY src ./src
RUN mvn clean package -DskipTests

# Production stage
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# Copy JAR
COPY --from=builder /app/target/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
'''
    
    def _get_dotnet_dockerfile(self) -> str:
        """Get .NET Dockerfile"""
        return '''# Build stage
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS builder

WORKDIR /src

# Copy csproj and restore
COPY *.csproj ./
RUN dotnet restore

# Copy source and build
COPY . .
RUN dotnet publish -c Release -o /app/publish

# Production stage
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS production

WORKDIR /app

# Copy published files
COPY --from=builder /app/publish .

EXPOSE 8080

ENTRYPOINT ["dotnet", "app.dll"]
'''
    
    def _get_frontend_dockerfile(self) -> str:
        """Get frontend Dockerfile (React/Vue/Angular)"""
        return '''# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files
COPY --from=builder /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
'''
    
    def _get_docker_compose(self, stack_type: str) -> str:
        """Get docker-compose.yml for development"""
        return '''version: "3.8"

services:
  # Backend API
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - NODE_ENV=development
      - DB_HOST=db
      - DB_PORT=5432
      - DB_NAME=myapp
      - DB_USER=postgres
      - DB_PASSWORD=password
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    volumes:
      - ./backend:/app
      - /app/node_modules
    depends_on:
      - db
      - redis
    command: npm run dev
    networks:
      - app-network

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: builder
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:5000/api
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm start
    networks:
      - app-network

  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - app-network

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - app-network

  # MongoDB (optional)
  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=password
      - MONGO_INITDB_DATABASE=myapp
    volumes:
      - mongo_data:/data/db
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:
  mongo_data:

networks:
  app-network:
    driver: bridge
'''
    
    def _get_docker_compose_prod(self, stack_type: str) -> str:
        """Get docker-compose.yml for production"""
        return '''version: "3.8"

services:
  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
      - frontend
    networks:
      - app-network
    restart: unless-stopped

  # Backend API
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    environment:
      - NODE_ENV=production
      - DB_HOST=db
      - DB_PORT=5432
      - DB_NAME=myapp
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_HOST=redis
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - db
      - redis
    networks:
      - app-network
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: production
    networks:
      - app-network
    restart: unless-stopped

  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

  # Redis Cache
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - app-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
'''
    
    def _get_dockerignore(self) -> str:
        """Get .dockerignore file"""
        return '''# Dependencies
node_modules
vendor
__pycache__
*.pyc

# Build outputs
dist
build
target
*.egg-info

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode
.idea
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs

# Testing
coverage
.nyc_output

# Git
.git
.gitignore

# Documentation
README.md
CHANGELOG.md
docs

# Docker
Dockerfile*
docker-compose*
.dockerignore
'''
    
    def _get_nginx_config(self) -> str:
        """Get nginx configuration"""
        return '''upstream api {
    server api:5000;
}

server {
    listen 80;
    server_name localhost;

    # Frontend
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api {
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Static files caching
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
'''
    
    def generate_kubernetes_manifests(self, namespace: str = "default") -> Dict[str, str]:
        """Generate Kubernetes manifests"""
        manifests = {}
        
        # Namespace
        manifests["namespace.yaml"] = f'''apiVersion: v1
kind: Namespace
metadata:
  name: {namespace}
'''
        
        # Deployment
        manifests["deployment.yaml"] = f'''apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: {namespace}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: myapp/api:latest
        ports:
        - containerPort: 5000
        env:
        - name: NODE_ENV
          value: "production"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
'''
        
        # Service
        manifests["service.yaml"] = f'''apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: {namespace}
spec:
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 5000
  type: ClusterIP
'''
        
        # Ingress
        manifests["ingress.yaml"] = f'''apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api
  namespace: {namespace}
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
'''
        
        # ConfigMap
        manifests["configmap.yaml"] = f'''apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
  namespace: {namespace}
data:
  DB_HOST: "postgres"
  DB_PORT: "5432"
  DB_NAME: "myapp"
'''
        
        # Secret
        manifests["secret.yaml"] = f'''apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
  namespace: {namespace}
type: Opaque
stringData:
  DB_PASSWORD: "changeme"
  JWT_SECRET: "changeme"
'''
        
        return manifests
    
    def save_kubernetes_manifests(self, output_dir: str, namespace: str = "default") -> List[Path]:
        """Save Kubernetes manifests to files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        manifests = self.generate_kubernetes_manifests(namespace)
        saved_files = []
        
        for filename, content in manifests.items():
            filepath = output_path / filename
            filepath.write_text(content)
            saved_files.append(filepath)
        
        return saved_files


if __name__ == "__main__":
    manager = DockerManager()
    
    # Example: Generate Kubernetes manifests
    manifests = manager.save_kubernetes_manifests("./k8s", namespace="myapp")
    print(f"Generated {len(manifests)} Kubernetes manifests")
