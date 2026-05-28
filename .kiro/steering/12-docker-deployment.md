# Docker & Deployment Standards

## Docker Image Rules
- Base image: `python:3.11-slim` for backend (not full, not alpine — slim is the balance)
- Base image: `node:20-slim` for frontend build, `nginx:alpine` for serving
- Never run containers as root — always set `USER` directive
- Multi-stage builds for frontend to keep image small

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system deps first (cached layer)
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps before copying code (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Non-root user
RUN useradd -m -u 1000 raguser && chown -R raguser:raguser /app
USER raguser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

```dockerfile
# frontend/Dockerfile — multi-stage
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
```

## Docker Compose Structure
```yaml
# Always define these services: api, worker, db, redis, frontend
# Optional: flower (Celery monitoring)

services:
  api:
    build: ./backend
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker:
    build: ./backend
    command: celery -A celery_app worker --loglevel=info --concurrency=2
    restart: unless-stopped
    # worker shares volumes with api — same uploads and model_cache

  db:
    image: postgres:15-alpine
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 10s

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

  flower:
    image: mher/flower
    command: celery --broker=redis://redis:6379/0 flower --port=5555
    ports: ["5555:5555"]
    depends_on: [redis]
    profiles: ["monitoring"]    # only starts with: docker compose --profile monitoring up
```

## Volume Strategy
```yaml
volumes:
  postgres_data:     # DB files
  chroma_data:       # Vector store
  upload_data:       # User uploaded files
  model_cache:       # Downloaded sentence-transformer model
```
All four must be named volumes (not bind mounts) — persist across container restarts.

## Environment Variable Strategy
```yaml
# docker-compose.yml — use env_file, not hardcoded values
services:
  api:
    env_file: .env
  worker:
    env_file: .env    # worker needs same env as api
```
`.env.example` documents every variable. `.env` is gitignored.

## Startup Order & Dependencies
```yaml
# Use depends_on with condition for proper ordering
services:
  api:
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
  worker:
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
```

## Running DB Migrations on Start
```bash
# backend/entrypoint.sh
#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"
```
```dockerfile
ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Development vs Production
```yaml
# docker-compose.override.yml — only applied in dev (auto-loaded)
services:
  api:
    volumes:
      - ./backend:/app    # live reload in dev
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  frontend:
    volumes:
      - ./frontend:/app   # live reload
    command: npm run dev
```
Production uses the base `docker-compose.yml` only.

## Resource Limits (Production)
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 1G
  worker:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 2G    # needs more — runs embedding model
  redis:
    deploy:
      resources:
        limits:
          memory: 512M
```
