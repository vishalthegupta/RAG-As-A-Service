# Phase 6 — Polish & Infrastructure

## Context
Phases 1–5 complete. The application is fully functional end-to-end.
This final phase makes it production-ready: observability, rate limiting,
hardened Docker setup, and documentation.
Read all files in .kiro/steering/ before writing any code.

## Goal
A single `docker compose up` starts a production-grade application with
proper health checks, resource limits, rate limiting, and clear documentation.

## Rules
- Implement features in the exact order listed below
- After each feature: write tests, run them, confirm green, report, then proceed
- No feature is "too small to test" — every endpoint and config gets verified

---

## Feature 34 — Health Check Endpoints

### What to build

**`app/health/router.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health():
    return {
        "status": "ok",
        "version": settings.VERSION,
        "app": settings.APP_NAME
    }

@router.get("/detailed")
async def health_detailed(db: AsyncSession = Depends(get_db)):
    checks: dict[str, str] = {}

    # PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:50]}"

    # Redis
    try:
        import redis as redis_lib
        r = redis_lib.from_url(settings.REDIS_URL)
        r.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    # ChromaDB
    try:
        get_chroma_client().heartbeat()
        checks["chromadb"] = "ok"
    except Exception:
        checks["chromadb"] = "error"

    # Embedding model
    checks["embedding_model"] = (
        "loaded" if EmbeddingService._instance is not None else "not_loaded"
    )

    overall = "ok" if all(
        v in ("ok", "loaded") for v in checks.values()
    ) else "degraded"

    return {"status": overall, **checks}
```

Register in `main.py`:
```python
app.include_router(health_router)   # no /api/v1 prefix — health is at root
```

### Tests to write
```python
async def test_health_returns_ok(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert "version" in res.json()

async def test_health_detailed_all_ok(client):
    res = await client.get("/health/detailed")
    assert res.status_code == 200
    assert "database" in res.json()
    assert "redis" in res.json()
    assert "chromadb" in res.json()
    assert "embedding_model" in res.json()

async def test_health_detailed_db_failure(client, monkeypatch):
    # mock DB to raise exception
    res = await client.get("/health/detailed")
    assert res.json()["database"].startswith("error")
    assert res.json()["status"] == "degraded"
```

### Done when
- `GET /health` returns 200 with version
- `GET /health/detailed` correctly reflects real status of all dependencies
- DB failure shows "degraded" not "ok"

---

## Feature 35 — Rate Limiting

### What to build

**Install slowapi:**
```bash
pip install slowapi
```

**`app/main.py`** — add rate limiter:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**Apply rate limits to routers:**

Auth endpoints — `app/auth/router.py`:
```python
@router.post("/register")
@limiter.limit(settings.AUTH_RATE_LIMIT)   # 10/minute
async def register(request: Request, ...): ...

@router.post("/login")
@limiter.limit(settings.AUTH_RATE_LIMIT)   # 10/minute
async def login(request: Request, ...): ...
```

Document upload — `app/documents/router.py`:
```python
@router.post("/")
@limiter.limit(settings.UPLOAD_RATE_LIMIT)   # 10/minute
async def upload_document(request: Request, ...): ...
```

Chat endpoint — `app/chat/router.py`:
```python
@router.post("/sessions/{session_id}/messages")
@limiter.limit(settings.CHAT_RATE_LIMIT)   # 60/minute
async def send_message(request: Request, ...): ...
```

### Tests to write
```python
async def test_rate_limit_login(client):
    # send 11 login requests in a loop
    responses = [
        await client.post("/api/v1/auth/login", json={"email": "x@x.com", "password": "wrong"})
        for _ in range(11)
    ]
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes   # at least one must be rate limited

async def test_rate_limit_response_has_retry_after(client):
    # trigger rate limit
    # verify 429 response has Retry-After header
```

### Done when
- All 3 endpoints have rate limiting applied
- 429 response returns with `Retry-After` header
- Tests confirm rate limits trigger correctly

---

## Feature 36 — Production Dockerfiles + Compose

### What to build

**`backend/Dockerfile`** — production-ready:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libmagic1 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 raguser && chown -R raguser:raguser /app
USER raguser

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

**`backend/entrypoint.sh`:**
```bash
#!/bin/bash
set -e
echo "Running migrations..."
alembic upgrade head
echo "Starting application..."
exec "$@"
```

**`frontend/Dockerfile`** — multi-stage:
```dockerfile
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

**`frontend/nginx.conf`:**
```nginx
server {
    listen 3000;
    root /usr/share/nginx/html;
    index index.html;

    # SPA routing — all non-file requests go to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API calls to backend
    location /api/ {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        # SSE support
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }
}
```

**`docker-compose.yml`** — production version with:
```yaml
services:
  api:
    build: ./backend
    restart: unless-stopped
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - CHROMA_PERSIST_DIRECTORY=/app/chroma_data
      - UPLOAD_DIR=/app/uploads
      - DEBUG=false
    volumes:
      - chroma_data:/app/chroma_data
      - upload_data:/app/uploads
      - model_cache:/app/model_cache
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 1G

  worker:
    build: ./backend
    command: celery -A celery_app worker --loglevel=info --concurrency=2
    restart: unless-stopped
    environment: *api-env
    volumes: *api-volumes
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 2G

  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-raguser}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-ragpass}
      POSTGRES_DB: ${POSTGRES_DB:-ragdb}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    restart: unless-stopped
    depends_on: [api]

  flower:
    image: mher/flower
    command: celery --broker=${REDIS_URL} flower --port=5555
    ports: ["5555:5555"]
    depends_on: [redis]
    profiles: ["monitoring"]

volumes:
  postgres_data:
  chroma_data:
  upload_data:
  model_cache:
```

**`docker-compose.override.yml`** — dev overrides (auto-applied in dev):
```yaml
services:
  api:
    volumes:
      - ./backend:/app
      - chroma_data:/app/chroma_data
      - upload_data:/app/uploads
      - model_cache:/app/model_cache
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      - DEBUG=true
    ports: ["8000:8000"]

  worker:
    volumes:
      - ./backend:/app
      - chroma_data:/app/chroma_data
      - upload_data:/app/uploads
      - model_cache:/app/model_cache
    command: celery -A celery_app worker --loglevel=debug --concurrency=1

  frontend:
    build:
      context: ./frontend
      target: builder
    command: npm run dev -- --host
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports: ["3000:3000"]
    environment:
      - VITE_API_URL=http://localhost:8000

  db:
    ports: ["5432:5432"]

  redis:
    ports: ["6379:6379"]
```

### Tests to write
```bash
# Shell-based tests — run these manually and verify output

# Test 1: fresh build succeeds
docker compose build --no-cache
echo "Exit code: $?"   # must be 0

# Test 2: all services start and become healthy
docker compose up -d
sleep 30
docker compose ps   # all must show "healthy" or "running"

# Test 3: migrations run automatically
docker compose logs api | grep "Running migrations"
docker compose logs api | grep "Starting application"

# Test 4: health endpoint reachable
curl -f http://localhost:8000/health
echo "Exit code: $?"   # must be 0

# Test 5: frontend serves correctly
curl -f http://localhost:3000
echo "Exit code: $?"   # must be 0
```

Write these as a `scripts/healthcheck.sh` script that runs all 5 checks and prints PASS/FAIL for each.

### Done when
- `docker compose build` succeeds with no errors
- `docker compose up` starts all services within 60 seconds
- `/health` endpoint returns 200 through the nginx proxy
- Worker container starts and connects to Redis successfully
- Model cache volume persists across container restarts (model not re-downloaded)

---

## Feature 37 — README + Environment Finalization

### What to build

**`README.md`** — complete, accurate quickstart:
```markdown
# RAG-as-a-Service

Upload your documents. Get a RAG chatbot. No code required.

## Prerequisites
- Docker 24+
- Docker Compose v2.20+
- A free Groq API key (https://console.groq.com)

## Quickstart (5 commands)

    git clone <repo>
    cd <repo>
    cp .env.example .env
    # Edit .env: add your GROQ_API_KEY and a random JWT_SECRET_KEY
    docker compose up

App available at:
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- Celery monitor: docker compose --profile monitoring up → http://localhost:5555

## Environment Variables
See .env.example — every variable has an inline comment.

## Running Tests
    cd backend && pytest
    cd frontend && npm test -- --run

## Architecture
See docs/HLD.md and docs/LLD.md
```

**`.env.example`** — final version, every variable documented:
```bash
# ── App ──────────────────────────────────────────────────────
APP_NAME="RAG-as-a-Service"
DEBUG=false

# ── Auth (REQUIRED) ──────────────────────────────────────────
# Generate with: openssl rand -hex 32
JWT_SECRET_KEY=your-secret-key-here-at-least-32-chars

# ── Database (REQUIRED) ──────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://raguser:ragpass@db:5432/ragdb
SYNC_DATABASE_URL=postgresql+psycopg2://raguser:ragpass@db:5432/ragdb
POSTGRES_USER=raguser
POSTGRES_PASSWORD=ragpass
POSTGRES_DB=ragdb

# ── Redis ────────────────────────────────────────────────────
REDIS_URL=redis://redis:6379/0

# ── LLM (REQUIRED — get free key at console.groq.com) ───────
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key-here

# ── LLM Fallback (optional) ──────────────────────────────────
HUGGINGFACE_API_KEY=
HUGGINGFACE_MODEL=mistralai/Mistral-7B-Instruct-v0.2

# ── Storage ──────────────────────────────────────────────────
STORAGE_BACKEND=local
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50

# ── RAG Tuning ───────────────────────────────────────────────
CHUNK_SIZE=512
CHUNK_OVERLAP=64
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.8
RAG_MAX_HISTORY_MESSAGES=6

# ── CORS (comma-separated) ───────────────────────────────────
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### Tests to write
```python
def test_env_example_has_all_required_vars():
    """Every variable in Settings that has no default must exist in .env.example"""
    required = ["JWT_SECRET_KEY", "DATABASE_URL", "SYNC_DATABASE_URL", "GROQ_API_KEY"]
    with open(".env.example") as f:
        content = f.read()
    for var in required:
        assert var in content, f"Missing required var in .env.example: {var}"

def test_readme_has_quickstart_section():
    with open("README.md") as f:
        content = f.read()
    assert "Quickstart" in content
    assert "docker compose up" in content
    assert "localhost:8000/docs" in content
```

### Done when
- `cp .env.example .env` + filling GROQ_API_KEY + JWT_SECRET_KEY is all that's needed to run
- README quickstart works exactly as written (tested manually)
- All 37 features documented in architecture docs

---

## Phase 6 Complete — Final Checklist

This is the full application checklist. Every item must be verified before the project is done.

### Functionality
- [ ] Register → Login → Upload PDF → Processing → READY → Chat → Receive streamed response
- [ ] Document delete removes file, DB record, and ChromaDB chunks
- [ ] Token refresh works transparently (user never sees a re-login prompt)
- [ ] LLM fallback: Groq fails → HuggingFace takes over
- [ ] Rate limiting returns 429 after threshold

### Infrastructure
- [ ] `docker compose up` starts in under 60 seconds
- [ ] All 5 services healthy
- [ ] `alembic upgrade head` runs automatically on api startup
- [ ] Named volumes persist data across `docker compose restart`
- [ ] `docker compose --profile monitoring up` shows Flower at :5555

### Code Quality
- [ ] `pytest tests/` exits with 0 failures
- [ ] `ruff check backend/` exits with 0 warnings
- [ ] `npm test -- --run` exits with 0 failures
- [ ] No `.env` file committed to git

### Documentation
- [ ] README quickstart works in 5 commands
- [ ] All env vars documented in `.env.example`
- [ ] API docs auto-generated at `/docs`

Report this summary when done:
```
✅ Phase 6 complete
   Features: 4/4 (cumulative: 37/37)
   Tests: N passed, 0 failed
   🎉 Application complete — all 37 features shipped and tested
```
