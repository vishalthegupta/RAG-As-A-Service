"""Tests for configuration module"""
from __future__ import annotations

import pytest
import os
from pydantic import ValidationError

from app.config import Settings


def test_settings_load_with_defaults():
    """Test settings load correctly with default values"""
    # Set required environment variables
    os.environ["JWT_SECRET_KEY"] = "test_secret_key_at_least_32_chars_long"
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost/testdb"
    os.environ["SYNC_DATABASE_URL"] = "postgresql://user:pass@localhost/testdb"
    
    settings = Settings()
    
    assert settings.APP_NAME == "RAG-as-a-Service"
    assert settings.VERSION == "1.0.0"
    assert settings.DEBUG is False
    assert settings.API_PREFIX == "/api/v1"
    assert settings.CHUNK_SIZE == 512
    assert settings.CHUNK_OVERLAP == 64
    assert settings.RAG_TOP_K == 5
    assert settings.RAG_SIMILARITY_THRESHOLD == 0.8


def test_settings_required_fields_missing():
    """Test that required fields raise error if missing"""
    # Clear required env vars
    for key in ["JWT_SECRET_KEY", "DATABASE_URL", "SYNC_DATABASE_URL"]:
        if key in os.environ:
            del os.environ[key]
    
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    
    # Check that error mentions missing fields
    error_str = str(exc_info.value)
    assert "JWT_SECRET_KEY" in error_str or "DATABASE_URL" in error_str


def test_settings_default_values_correct_types():
    """Test default values are correct types"""
    os.environ["JWT_SECRET_KEY"] = "test_secret_key_at_least_32_chars_long"
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost/testdb"
    os.environ["SYNC_DATABASE_URL"] = "postgresql://user:pass@localhost/testdb"
    
    settings = Settings()
    
    # Check types
    assert isinstance(settings.CHUNK_SIZE, int)
    assert isinstance(settings.CHUNK_OVERLAP, int)
    assert isinstance(settings.RAG_SIMILARITY_THRESHOLD, float)
    assert isinstance(settings.DEBUG, bool)
    assert isinstance(settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)


def test_allowed_origins_list_property():
    """Test that allowed_origins_list property parses correctly"""
    os.environ["JWT_SECRET_KEY"] = "test_secret_key_at_least_32_chars_long"
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost/testdb"
    os.environ["SYNC_DATABASE_URL"] = "postgresql://user:pass@localhost/testdb"
    os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000,http://localhost:5173,https://example.com"
    
    settings = Settings()
    
    origins = settings.allowed_origins_list
    assert isinstance(origins, list)
    assert len(origins) == 3
    assert "http://localhost:3000" in origins
    assert "http://localhost:5173" in origins
    assert "https://example.com" in origins
