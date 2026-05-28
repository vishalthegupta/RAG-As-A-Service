"""FastAPI application factory and configuration"""
from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.config import settings
from app.logging_config import setup_logging
from app.exceptions import (
    DocumentNotFoundError,
    DocumentNotReadyError,
    DocumentProcessingError,
    StorageError,
    LLMUnavailableError,
    EmbeddingError,
    DuplicateEmailError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    SessionNotFoundError,
)
from app.processing.embedder import EmbeddingService

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    setup_logging()
    logger.info("app.startup", version=settings.VERSION)
    
    # Load embedding model
    try:
        EmbeddingService.get_instance()
        logger.info("app.startup.embedding.ready")
    except Exception as e:
        logger.error("app.startup.embedding.failed", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("app.shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)


# Exception handlers
@app.exception_handler(DocumentNotFoundError)
async def document_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc) or "Document not found"}
    )


@app.exception_handler(SessionNotFoundError)
async def session_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc) or "Session not found"}
    )


@app.exception_handler(DocumentNotReadyError)
async def document_not_ready_handler(request, exc):
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc) or "Document is still processing"}
    )


@app.exception_handler(DuplicateEmailError)
async def duplicate_email_handler(request, exc):
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc) or "Email already registered"}
    )


@app.exception_handler(FileTooLargeError)
async def file_too_large_handler(request, exc):
    return JSONResponse(
        status_code=413,
        content={"detail": str(exc) or "File too large"}
    )


@app.exception_handler(UnsupportedFileTypeError)
async def unsupported_file_type_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc) or "Unsupported file type"}
    )


@app.exception_handler(LLMUnavailableError)
async def llm_unavailable_handler(request, exc):
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc) or "AI service temporarily unavailable"}
    )


@app.exception_handler(StorageError)
async def storage_error_handler(request, exc):
    logger.error("storage.error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "File operation failed"}
    )


@app.exception_handler(EmbeddingError)
async def embedding_error_handler(request, exc):
    logger.error("embedding.error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Embedding generation failed"}
    )


@app.exception_handler(DocumentProcessingError)
async def processing_error_handler(request, exc):
    logger.error("processing.error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "Document processing failed"}
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    logger.exception("unhandled.error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"}
    )


# Health check endpoints
@app.get("/health", tags=["health"])
async def health():
    """Basic health check"""
    return {"status": "ok", "version": settings.VERSION}


@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs"
    }


# TODO: Add routers here as they are implemented
# app.include_router(auth_router, prefix=f"{settings.API_PREFIX}/auth", tags=["auth"])
# app.include_router(documents_router, prefix=f"{settings.API_PREFIX}/documents", tags=["documents"])
# app.include_router(chat_router, prefix=f"{settings.API_PREFIX}/chat", tags=["chat"])
