"""Tests for exception handling"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.exceptions import (
    DocumentNotFoundError,
    DocumentNotReadyError,
    DuplicateEmailError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    LLMUnavailableError,
    StorageError,
    EmbeddingError,
    DocumentProcessingError,
    SessionNotFoundError,
)


def test_exception_hierarchy():
    """Test that all exceptions inherit from RagServiceError"""
    from app.exceptions import RagServiceError
    
    exceptions = [
        DocumentNotFoundError,
        DocumentNotReadyError,
        DuplicateEmailError,
        FileTooLargeError,
        UnsupportedFileTypeError,
        LLMUnavailableError,
        StorageError,
        EmbeddingError,
        DocumentProcessingError,
        SessionNotFoundError,
    ]
    
    for exc_class in exceptions:
        assert issubclass(exc_class, RagServiceError)


def test_exception_handlers_registered():
    """Test that exception handlers are registered in main app"""
    from app.main import app
    
    # Check that app has exception handlers
    assert hasattr(app, 'exception_handlers')
    assert len(app.exception_handlers) > 0


def test_document_not_found_returns_404():
    """Test DocumentNotFoundError maps to 404"""
    from app.main import app
    
    @app.get("/test-404")
    async def test_route():
        raise DocumentNotFoundError("Test document not found")
    
    client = TestClient(app)
    response = client.get("/test-404")
    
    assert response.status_code == 404
    assert "detail" in response.json()


def test_document_not_ready_returns_409():
    """Test DocumentNotReadyError maps to 409"""
    from app.main import app
    
    @app.get("/test-409-ready")
    async def test_route():
        raise DocumentNotReadyError("Document still processing")
    
    client = TestClient(app)
    response = client.get("/test-409-ready")
    
    assert response.status_code == 409
    assert "detail" in response.json()


def test_duplicate_email_returns_409():
    """Test DuplicateEmailError maps to 409"""
    from app.main import app
    
    @app.get("/test-409-email")
    async def test_route():
        raise DuplicateEmailError("Email already registered")
    
    client = TestClient(app)
    response = client.get("/test-409-email")
    
    assert response.status_code == 409
    assert "detail" in response.json()


def test_file_too_large_returns_413():
    """Test FileTooLargeError maps to 413"""
    from app.main import app
    
    @app.get("/test-413")
    async def test_route():
        raise FileTooLargeError("File too large")
    
    client = TestClient(app)
    response = client.get("/test-413")
    
    assert response.status_code == 413
    assert "detail" in response.json()


def test_unsupported_file_type_returns_400():
    """Test UnsupportedFileTypeError maps to 400"""
    from app.main import app
    
    @app.get("/test-400")
    async def test_route():
        raise UnsupportedFileTypeError("Unsupported file type")
    
    client = TestClient(app)
    response = client.get("/test-400")
    
    assert response.status_code == 400
    assert "detail" in response.json()


def test_llm_unavailable_returns_503():
    """Test LLMUnavailableError maps to 503"""
    from app.main import app
    
    @app.get("/test-503")
    async def test_route():
        raise LLMUnavailableError("AI service unavailable")
    
    client = TestClient(app)
    response = client.get("/test-503")
    
    assert response.status_code == 503
    assert "detail" in response.json()


def test_storage_error_returns_500():
    """Test StorageError maps to 500"""
    from app.main import app
    
    @app.get("/test-500-storage")
    async def test_route():
        raise StorageError("Storage failed")
    
    client = TestClient(app)
    response = client.get("/test-500-storage")
    
    assert response.status_code == 500
    assert "detail" in response.json()
    assert response.json()["detail"] == "File operation failed"


def test_unhandled_exception_returns_500():
    """Test catch-all returns 500 and does not expose internal error"""
    from app.main import app
    from fastapi.testclient import TestClient
    
    # Create a test client with raise_server_exceptions=False to test error handling
    client = TestClient(app, raise_server_exceptions=False)
    
    # Create a temporary test route that raises an exception
    @app.get("/test-500-unhandled-temp")
    async def test_route():
        raise ValueError("Internal error message that should not be exposed")
    
    response = client.get("/test-500-unhandled-temp")
    
    # The exception handler should catch it and return 500
    assert response.status_code == 500
    assert "detail" in response.json()
    # Verify the internal error message is not exposed
    response_detail = response.json()["detail"]
    assert "Internal error message" not in str(response_detail)
    # Note: Test route persists in app but this is acceptable for test isolation
