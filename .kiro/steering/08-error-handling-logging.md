# Error Handling & Logging Standards

## Exception Hierarchy
All custom exceptions live in `app/exceptions.py`:
```python
class RagServiceError(Exception):
    """Base exception for all application errors"""
    pass

# Domain exceptions
class DocumentNotFoundError(RagServiceError): pass
class DocumentNotReadyError(RagServiceError): pass     # chat before doc is READY
class DocumentProcessingError(RagServiceError): pass   # error inside Celery task
class StorageError(RagServiceError): pass              # file read/write failure
class LLMUnavailableError(RagServiceError): pass       # Groq/HF API down
class EmbeddingError(RagServiceError): pass            # model inference failure
class DuplicateEmailError(RagServiceError): pass
class FileTooLargeError(RagServiceError): pass
class UnsupportedFileTypeError(RagServiceError): pass
```

## Global Exception Handlers (main.py)
```python
@app.exception_handler(DocumentNotFoundError)
async def _not_found(req, exc):
    return JSONResponse(404, {"detail": str(exc) or "Resource not found"})

@app.exception_handler(DocumentNotReadyError)
async def _not_ready(req, exc):
    return JSONResponse(409, {"detail": "Document is still processing. Please wait."})

@app.exception_handler(DuplicateEmailError)
async def _duplicate(req, exc):
    return JSONResponse(409, {"detail": "Email already registered"})

@app.exception_handler(LLMUnavailableError)
async def _llm_down(req, exc):
    return JSONResponse(503, {"detail": "AI service temporarily unavailable. Please retry."})

@app.exception_handler(StorageError)
async def _storage(req, exc):
    logger.error("storage.error", error=str(exc))
    return JSONResponse(500, {"detail": "File operation failed"})

# Catch-all — never expose internal details to client
@app.exception_handler(Exception)
async def _unhandled(req, exc):
    logger.exception("unhandled.error", error=str(exc))
    return JSONResponse(500, {"detail": "An unexpected error occurred"})
```

## Error Response Format
Every error response must follow this shape — never deviate:
```json
{
    "detail": "Human-readable message safe to show users"
}
```
For validation errors (422), FastAPI returns:
```json
{
    "detail": [{"loc": ["body", "field"], "msg": "...", "type": "..."}]
}
```

## Logging Setup
```python
# app/logging_config.py
import structlog
import logging

def setup_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer() if not settings.DEBUG
            else structlog.dev.ConsoleRenderer()
        ],
        logger_factory=structlog.PrintLoggerFactory(),
    )
    logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
```
- JSON logs in production (machine-parseable)
- Pretty console logs in development
- Call `setup_logging()` in `main.py` before the app starts

## What to Log
```python
# Document service
logger.info("document.uploaded", doc_id=str(doc.id), user_id=str(user_id), filename=filename, size_bytes=size)
logger.info("document.deleted", doc_id=str(doc_id), user_id=str(user_id))

# Processing worker
logger.info("task.started", doc_id=document_id, task_id=self.request.id)
logger.info("task.parsing.complete", doc_id=document_id, text_length=len(text))
logger.info("task.chunking.complete", doc_id=document_id, chunk_count=len(chunks))
logger.info("task.embedding.complete", doc_id=document_id, batch_count=batches)
logger.info("task.chromadb.upsert.complete", doc_id=document_id)
logger.info("task.complete", doc_id=document_id, duration_s=elapsed)
logger.error("task.failed", doc_id=document_id, error=str(exc), exc_info=True)

# Chat service
logger.info("chat.query", session_id=str(session_id), user_id=str(user_id), query_length=len(query))
logger.info("chat.retrieval.complete", session_id=str(session_id), chunks_found=len(chunks))
logger.info("chat.response.complete", session_id=str(session_id), latency_ms=latency)
```

## What NOT to Log
- Passwords, tokens, API keys
- Full document text (too verbose, potential PII)
- User email in most log lines (use user_id instead)
- Full LLM prompts (may contain user data)

## LLM Fallback Pattern
```python
async def get_llm_response(prompt):
    providers = [GroqProvider(), HuggingFaceProvider()]
    last_error = None
    
    for provider in providers:
        try:
            async for token in provider.stream_chat(prompt):
                yield token
            return
        except LLMUnavailableError as e:
            logger.warning("llm.provider.failed", provider=type(provider).__name__, error=str(e))
            last_error = e
            continue
    
    raise LLMUnavailableError("All LLM providers failed") from last_error
```
Always try Groq first, fall back to HuggingFace — never fail silently.
