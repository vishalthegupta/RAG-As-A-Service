# API Design & Streaming Standards

## REST Conventions
- Resources are nouns, always plural: `/documents`, `/sessions`, `/messages`
- Actions via HTTP verbs: `POST` create, `GET` read, `DELETE` remove, `PUT`/`PATCH` update
- Nested resources for ownership: `/sessions/{session_id}/messages`
- Status sub-resource for polling: `/documents/{id}/status`
- Version prefix always: `/api/v1/`

## Request/Response Schema Naming
```python
# schemas.py naming convention:
class DocumentCreateRequest(BaseModel): ...    # request body for POST
class DocumentResponse(BaseModel): ...         # single resource response
class DocumentListResponse(BaseModel): ...     # paginated list response
class DocumentStatusResponse(BaseModel): ...   # status polling response
```

## Pagination (Apply to All List Endpoints)
```python
# Query params: ?skip=0&limit=50
# Always return total count so frontend can paginate
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int

# Usage
@router.get("/documents", response_model=PaginatedResponse[DocumentResponse])
async def list_documents(skip: int = 0, limit: int = Query(default=50, le=100)):
    ...
```
Max `limit`: 100 — never return unbounded lists.

## SSE (Server-Sent Events) for Chat Streaming
```python
# chat/router.py
from fastapi.responses import StreamingResponse
import json

@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: UUID, request: ChatRequest, ...):
    
    async def event_generator():
        try:
            async for token in rag_pipeline.stream(user_id, session_id, request.message):
                # Each SSE event: "data: {json}\n\n"
                yield f"data: {json.dumps({'token': token})}\n\n"
            
            # After stream: send sources and done signal
            sources = rag_pipeline.get_last_sources()
            yield f"data: {json.dumps({'sources': sources})}\n\n"
            yield f"data: {json.dumps({'done': True, 'latency_ms': latency})}\n\n"
        
        except LLMUnavailableError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",    # disables nginx buffering for SSE
            "Connection": "keep-alive"
        }
    )
```

## SSE Event Types (Standard — Never Change This Contract)
```
event: token      data: {"token": "Hello"}         ← streamed word-by-word
event: sources    data: {"sources": [...]}          ← after full response
event: done       data: {"latency_ms": 340}         ← terminal signal
event: error      data: {"error": "...message"}     ← on failure
```
Frontend must handle all four. `done` or `error` signals end of stream.

## Request Validation
```python
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000, strip_whitespace=True)

class DocumentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255, strip_whitespace=True)
    description: str | None = Field(default=None, max_length=1000)

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
```
- `strip_whitespace=True` on all string fields — prevents " " as valid input
- `EmailStr` from pydantic — validates email format
- Max lengths on all string fields — prevents abuse

## API Documentation
FastAPI generates OpenAPI docs at `/docs` (Swagger) and `/redoc`.
- Always set `summary` and `description` on every route
- Use `response_model` on every route — it documents and validates output
- Tag routes by domain: `tags=["documents"]`, `tags=["auth"]`, `tags=["chat"]`

```python
@router.post(
    "/",
    response_model=DocumentResponse,
    status_code=201,
    summary="Upload a document",
    description="Upload a PDF, TXT, or DOCX file. Processing starts automatically."
)
async def upload_document(...):
    ...
```

## Health Check Endpoint
```python
@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": settings.VERSION}

@app.get("/health/detailed", tags=["health"])
async def health_detailed(db: AsyncSession = Depends(get_db)):
    checks = {}
    
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
    
    try:
        get_chroma_client().heartbeat()
        checks["chromadb"] = "ok"
    except Exception:
        checks["chromadb"] = "error"
    
    checks["embedding_model"] = "loaded" if EmbeddingService._instance else "not_loaded"
    
    overall = "ok" if all(v == "ok" for v in checks.values() if v != "not_loaded") else "degraded"
    return {"status": overall, **checks}
```
Docker Compose `healthcheck` should call `/health` every 30s.
