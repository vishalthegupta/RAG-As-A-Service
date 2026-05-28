# Python Coding Standards

## Style & Formatting
- Formatter: **Black** (line length 88) — run on every save
- Linter: **Ruff** — must pass with zero warnings before committing
- Type checker: **mypy** (strict mode) — all public functions must be fully typed
- Import order: stdlib → third-party → local (enforced by Ruff isort rules)

## Type Annotations — Mandatory
```python
# WRONG
def get_user(user_id):
    ...

# RIGHT
async def get_user(user_id: UUID, db: AsyncSession) -> User | None:
    ...
```
- Every function parameter and return type must be annotated
- Use `from __future__ import annotations` at top of every file
- Prefer `X | None` over `Optional[X]` (Python 3.10+ style)
- Use `list[str]` not `List[str]`, `dict[str, Any]` not `Dict[str, Any]`

## Pydantic v2 Models
```python
# schemas.py
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime

class DocumentResponse(BaseModel):
    id: UUID
    name: str
    status: str
    chunk_count: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # replaces orm_mode=True
```
- Always use `model_config = ConfigDict(from_attributes=True)` on response schemas
- Use `Field(...)` for validation constraints: `Field(min_length=1, max_length=255)`
- Never return raw ORM objects from routes — always convert to Pydantic schema

## SQLAlchemy 2.0 Style
```python
# WRONG — legacy style
users = db.query(User).filter(User.id == user_id).all()

# RIGHT — 2.0 style
from sqlalchemy import select
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()
```
- Always use `select()`, `insert()`, `update()`, `delete()` from `sqlalchemy`
- Use `scalar_one_or_none()` when expecting 0 or 1 result
- Use `scalars().all()` for lists
- Always `await db.commit()` after writes, `await db.refresh(obj)` if you need updated fields

## Custom Exceptions
```python
# All in app/exceptions.py
class RagServiceError(Exception): pass
class DocumentNotFoundError(RagServiceError): pass
class DocumentNotReadyError(RagServiceError): pass
class StorageError(RagServiceError): pass
class LLMUnavailableError(RagServiceError): pass
class EmbeddingError(RagServiceError): pass
class DuplicateEmailError(RagServiceError): pass
```
- Services raise these — never raise `HTTPException` in service layer
- Routers never catch these — global exception handlers in `main.py` map them to HTTP responses
- Add new exceptions to `exceptions.py` — never create inline exception classes

## Logging
```python
import structlog
logger = structlog.get_logger(__name__)

# Always log with context, never with string formatting
logger.info("document.processing.started", doc_id=str(doc_id), user_id=str(user_id))
logger.error("document.processing.failed", doc_id=str(doc_id), error=str(e))
```
- Use **structlog** for structured JSON logging (searchable in prod)
- Log at INFO for major lifecycle events, DEBUG for verbose steps, ERROR for failures
- Always include relevant IDs (user_id, doc_id, session_id) as log fields, not in the message string
- Never log passwords, tokens, or PII

## Naming Conventions
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private helpers: `_leading_underscore`
- UUID variables: always name them `{entity}_id` (e.g., `user_id`, `doc_id`)

## No Magic Numbers or Strings
```python
# WRONG
if document.status == "READY":
    ...

# RIGHT — use Enum
class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"

if document.status == DocumentStatus.READY:
    ...
```
Define all enums in `app/enums.py`. Use them everywhere.

## Function Length
- Max 30 lines per function. If longer, extract helpers.
- One function = one responsibility. If you need "and" to describe it, split it.
