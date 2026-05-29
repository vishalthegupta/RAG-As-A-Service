# Phase 1 — Foundation

## Context
RAG-as-a-Service application. Users upload documents, get a RAG chatbot.
Tech stack: FastAPI + PostgreSQL + ChromaDB + Celery + Redis + React.
Read all files in .kiro/steering/ before writing any code.

## Goal
Build the complete project skeleton — folder structure, Docker setup, database
foundation, config, and error handling. Every subsequent phase depends on this
being solid. Do not cut corners here.

## Rules
- Implement features in the exact order listed below
- After each feature: write tests, run them, confirm green, report, then proceed
- Do not start the next feature until tests pass for the current one
- Follow all conventions in .kiro/steering/ files strictly

---

## Feature 1 — Project Scaffolding

### What to build
- Full folder structure for backend and frontend as defined in LLD
- Docker Compose with all 5 services: api, worker, db, redis, frontend
- `.env.example` with every environment variable documented with a comment
- `requirements.txt` with all backend dependencies pinned to specific versions
- `package.json` stub for frontend
- `README.md` with quickstart in 5 commands

### Folder structure to create
```
backend/
  app/
    auth/
    documents/
    chat/
    processing/
    vector_store/
    llm/
  alembic/
  tests/
    unit/
    integration/
  Dockerfile
  requirements.txt
  .env.example
  celery_app.py
  entrypoint.sh

frontend/
  src/
    api/
    store/
    pages/
    components/
    hooks/
    lib/
  Dockerfile
  package.json
  vite.config.js
  tailwind.config.js

docker-compose.yml
docker-compose.override.yml
.env.example
.gitignore
README.md
```

### Requirements.txt must include
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
asyncpg==0.29.0
alembic==1.13.1
pydantic==2.7.1
pydantic-settings==2.2.1
celery==5.4.0
redis==5.0.4
chromadb==0.5.0
sentence-transformers==2.7.0
torch==2.3.0
PyMuPDF==1.24.3
python-docx==1.1.0
python-multipart==0.0.9
python-magic==0.4.27
aiofiles==23.2.1
passlib[bcrypt]==1.7.4
PyJWT==2.8.0
structlog==24.1.0
slowapi==0.1.9
httpx==0.27.0
pytest==8.2.0
pytest-asyncio==0.23.6
aiosqlite==0.20.0
ruff==0.4.4
```

### .gitignore must include
```
.env
__pycache__/
*.pyc
.pytest_cache/
model_cache/
chroma_data/
uploads/
node_modules/
dist/
.vite/
coverage/
*.egg-info/
```

### Tests to write
- Test that `docker-compose.yml` has all 5 required services defined
- Test that `.env.example` contains all required variable names
- Verify folder structure exists

### Done when
- `docker compose config` runs with no errors
- All folders exist
- `.env.example` has every variable from `app/config.py` (next feature)

---

## Feature 2 — Database Setup

### What to build
- `app/database.py` — async engine + session factory + sync engine for Celery
- `app/models/base.py` — DeclarativeBase + TimestampMixin
- Alembic initialized with `env.py` configured for async
- `dependencies.py` — `get_db()` dependency

### database.py exact spec
```python
# Two engines: async for FastAPI, sync for Celery
# pool_size=10, max_overflow=20, pool_pre_ping=True on both
# AsyncSessionLocal with expire_on_commit=False
# SyncSessionLocal for Celery tasks
# get_db() async generator for FastAPI Depends()
```

### Alembic env.py requirements
- Must import all models so autogenerate detects them
- Must use async connection for migrations
- `target_metadata = Base.metadata`

### Tests to write
- Test that async DB session can be created and closed cleanly
- Test that `SELECT 1` works against a test SQLite database
- Test that Base.metadata exists and is importable

### Done when
- `alembic init alembic` done and `env.py` configured
- `from app.database import AsyncSessionLocal, SyncSessionLocal` works
- `from app.models.base import Base, TimestampMixin` works

---

## Feature 3 — All Database Models + Migration

### What to build
All 5 SQLAlchemy models as specified in LLD section 2 and DATABASE_SCHEMA.sql.

### Models to create
**`app/auth/models.py`** — User
- id (UUID PK), email (unique), hashed_password, full_name, is_active, timestamps
- Relationships: documents, chat_sessions

**`app/documents/models.py`** — Document, ProcessingJob
- Document: id, user_id (FK), name, description, original_filename, file_path,
  file_size_bytes, mime_type, status (DocumentStatus enum), chunk_count, error_message, timestamps
- ProcessingJob: id, document_id (unique FK), celery_task_id, status (JobStatus enum),
  progress_pct (0-100), started_at, completed_at, error_detail

**`app/chat/models.py`** — ChatSession, ChatMessage
- ChatSession: id, user_id (FK), title, timestamps
- ChatMessage: id, session_id (FK), role (MessageRole enum), content,
  sources (JSON), tokens_used, latency_ms, created_at

**`app/enums.py`** — All enums
```python
class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
```

### Migration requirements
- Single migration file: `alembic/versions/001_initial_schema.py`
- Creates all tables in correct FK dependency order
- Implements `downgrade()` that drops all tables
- All indexes from DATABASE_SCHEMA.sql must be included

### Tests to write
- Test each model can be instantiated with required fields
- Test that all relationships are accessible (user.documents, session.messages)
- Test that enums have correct string values
- Test that migration applies and rolls back cleanly against test DB

### Done when
- `alembic upgrade head` creates all 5 tables with correct columns
- `alembic downgrade base` drops all tables
- All model imports work

---

## Feature 4 — Config Module

### What to build
`app/config.py` — single Pydantic Settings class with every config value.

### All settings to include (exact names)
```python
# App
APP_NAME: str = "RAG-as-a-Service"
VERSION: str = "1.0.0"
DEBUG: bool = False
API_PREFIX: str = "/api/v1"

# Auth
JWT_SECRET_KEY: str           # required, no default
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
REFRESH_TOKEN_EXPIRE_DAYS: int = 7

# Database
DATABASE_URL: str             # required — postgresql+asyncpg://...
SYNC_DATABASE_URL: str        # required — postgresql+psycopg2://...

# Redis
REDIS_URL: str = "redis://localhost:6379/0"

# ChromaDB
CHROMA_PERSIST_DIRECTORY: str = "./chroma_data"

# Storage
STORAGE_BACKEND: str = "local"
UPLOAD_DIR: str = "./uploads"
MAX_FILE_SIZE_MB: int = 50
ALLOWED_MIME_TYPES: list[str] = [
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
]

# Embedding
EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_BATCH_SIZE: int = 32

# LLM
LLM_PROVIDER: str = "groq"
GROQ_API_KEY: str = ""
HUGGINGFACE_API_KEY: str = ""
HUGGINGFACE_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.2"

# RAG
RAG_TOP_K: int = 5
RAG_SIMILARITY_THRESHOLD: float = 0.8
RAG_MAX_HISTORY_MESSAGES: int = 6
CHUNK_SIZE: int = 512
CHUNK_OVERLAP: int = 64

# Rate limiting
CHAT_RATE_LIMIT: str = "60/minute"
AUTH_RATE_LIMIT: str = "10/minute"
UPLOAD_RATE_LIMIT: str = "10/minute"

# CORS
ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
```

### Tests to write
- Test settings load correctly from environment variables
- Test that required fields (JWT_SECRET_KEY, DATABASE_URL) raise error if missing
- Test default values are correct types

### Done when
- `from app.config import settings` works
- `settings.CHUNK_SIZE` returns `512`
- Missing required env var raises clear `ValidationError`

---

## Feature 5 — Exception Handlers + Logging

### What to build

**`app/exceptions.py`** — full exception hierarchy
```python
class RagServiceError(Exception): pass
class DocumentNotFoundError(RagServiceError): pass
class DocumentNotReadyError(RagServiceError): pass
class DocumentProcessingError(RagServiceError): pass
class StorageError(RagServiceError): pass
class LLMUnavailableError(RagServiceError): pass
class EmbeddingError(RagServiceError): pass
class DuplicateEmailError(RagServiceError): pass
class FileTooLargeError(RagServiceError): pass
class UnsupportedFileTypeError(RagServiceError): pass
```

**`app/logging_config.py`** — structlog setup
- JSON output in production (`DEBUG=False`)
- Pretty console output in development (`DEBUG=True`)
- `setup_logging()` function called once on startup

**`app/main.py`** — FastAPI app with
- Lifespan context manager (startup/shutdown)
- All exception handlers registered
- CORS middleware
- API router included with `/api/v1` prefix
- `setup_logging()` called on startup

### Exception → HTTP mapping (exact)
```
DocumentNotFoundError       → 404
DocumentNotReadyError       → 409 "Document still processing"
DuplicateEmailError         → 409 "Email already registered"
LLMUnavailableError         → 503 "AI service temporarily unavailable"
StorageError                → 500 "File operation failed"
FileTooLargeError           → 413
UnsupportedFileTypeError    → 400
Exception (catch-all)       → 500 "An unexpected error occurred"
```

### Tests to write
- Test each exception maps to the correct HTTP status code
- Test catch-all returns 500 and does not expose internal error message
- Test that logging setup runs without errors
- Test that CORS headers are present on responses

### Done when
- `uvicorn app.main:app` starts without errors
- `GET /health` returns `{"status": "ok"}`
- Raising `DocumentNotFoundError` in a test route returns HTTP 404
- Logs appear in correct format based on DEBUG setting

---

## Phase 1 Complete — Checklist

Before moving to Phase 2, verify all of the following:

- [ ] `docker compose up` starts all 5 services without errors
- [ ] `alembic upgrade head` applies migration cleanly
- [ ] `pytest tests/` exits with code 0, zero failures
- [ ] `from app.config import settings` works
- [ ] `from app.exceptions import DocumentNotFoundError` works
- [ ] `GET /health` returns 200
- [ ] `.env.example` has every variable that `config.py` reads
- [ ] `.gitignore` includes `.env`, `model_cache/`, `chroma_data/`, `uploads/`

Report this summary when done:
```
✅ Phase 1 complete
   Features: 5/5
   Tests: N passed, 0 failed
   Ready for Phase 2: Auth
```
