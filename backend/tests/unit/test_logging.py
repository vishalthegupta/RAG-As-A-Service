"""Tests for logging configuration"""
from __future__ import annotations

import pytest


def test_logging_setup_runs_without_errors():
    """Test that logging setup runs without errors"""
    from app.logging_config import setup_logging
    
    # Should not raise any exceptions
    setup_logging()


def test_structlog_logger_available():
    """Test that structlog logger can be imported and used"""
    import structlog
    
    logger = structlog.get_logger(__name__)
    assert logger is not None
    
    # Test that we can call log methods without errors
    logger.info("test.message", test_key="test_value")
