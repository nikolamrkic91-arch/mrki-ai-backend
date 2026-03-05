FROM python:3.14-slim

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code
COPY . .

# Install additional dependencies
RUN pip install fastapi uvicorn sqlalchemy alembic pydantic python-jose passlib httpx click rich structlog apscheduler croniter python-dateutil tenacity jinja2 pyyaml python-multipart aiohttp watchdog

# Expose port
EXPOSE 8000

# Run the server
CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "8000"]
