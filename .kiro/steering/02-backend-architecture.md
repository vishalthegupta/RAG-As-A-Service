# Backend Architecture Rules

## Module Structure
Every domain (auth, documents, chat, processing) is a self-contained package with:
```
domain/
├── router.py    ← FastAPI routes ONLY. No business logic here.
├── service.py   ← All business logic. Receives DB session + validated input. Returns domain objects.
├── schemas.py   ← Pydantic v2 models for request/response. Never expose ORM models directly.
├── models.py    ← SQLAlchemy ORM models. Never import these in router.py directly.
└── (extras)     ← storage.py, utils.py etc. as needed
```

## Layer Rules — Strictly Enforced

**Router layer** (`router.py`):
- Only handles HTTP concerns: parse request, call service, return response
- Inject dependencies via `Depends()` only — never create objects directly
- Never write SQL or touch ChromaDB
- Never catch business exceptions — let the global exception handler do it

**Service layer** (`service.py`):
- All business logic lives here
- Receives: db session, current_user (as User object), validated Pydantic schema
- Returns: Pydantic schema or raises a custom exception (never raise HTTPException)
- Enforces ownership: always filter queries by `user_id` before returning data

**Models layer** (`models.py`):
- SQLAlchemy 2.0 style with type annotations
- Every table has: `id (UUID PK)`, `created_at`, `updated_at` (via trigger)
- Never put business logic in models

## Async First
- All route handlers: `async def`
- All service methods: `async def`
- All DB operations: use `AsyncSession` from `sqlalchemy.ext.asyncio`
- Use `await` everywhere. Never use sync blocking calls inside async functions.
- File I/O inside Celery tasks (sync context) is fine — don't mix async into Celery

## Dependency Injection Pattern
```python
# dependencies.py — the ONLY place these are defined
async def get_db() -> AsyncGenerator[AsyncSession, None]: ...
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User: ...

# In routers — always inject, never instantiate
@router.get("/documents")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await document_service.list_documents(db, current_user)
```

## Configuration
- All config via `app/config.py` using `pydantic_settings.BaseSettings`
- Read from `.env` file
- Never hardcode secrets, URLs, or magic numbers in code
- Import settings as: `from app.config import settings`
- Config values are typed — if it's an int, declare it as `int`

## API Versioning
- All routes under `/api/v1/`
- Prefix set in `main.py` via `app.include_router(router, prefix="/api/v1")`
- Never put version in individual route decorators

## Response Conventions
- Success creates: HTTP 201
- Success reads: HTTP 200
- Success deletes: HTTP 200 with `{"message": "..."}`
- Not found: HTTP 404
- Validation error: HTTP 422 (FastAPI handles automatically)
- Auth error: HTTP 401
- Ownership violation: HTTP 404 (not 403 — don't leak existence)
- Conflict (e.g. duplicate email): HTTP 409

## Startup & Shutdown
```python
# main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: load embedding model, verify DB connection, verify ChromaDB
    EmbeddingService.get_instance()
    yield
    # shutdown: cleanup if needed
```
