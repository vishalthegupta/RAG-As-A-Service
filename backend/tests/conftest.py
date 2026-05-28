"""Pytest configuration and shared fixtures"""
from __future__ import annotations

import pytest
import asyncio
from typing import AsyncGenerator

# Configure asyncio for tests
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# TODO: Add fixtures as modules are implemented:
# - db_session: Test database session
# - client: Test HTTP client
# - auth_headers: Authenticated user headers
# - test_user: Sample user for testing
# - test_document: Sample document for testing
