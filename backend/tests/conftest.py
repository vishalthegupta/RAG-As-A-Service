"""Pytest configuration and shared fixtures"""
from __future__ import annotations

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.models.base import Base


# Configure asyncio for tests
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session using SQLite in-memory"""
    # Use SQLite for unit tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    
    async with async_session() as session:
        yield session
    
    # Cleanup
    await engine.dispose()


# TODO: Add more fixtures as modules are implemented:
# - client: Test HTTP client
# - auth_headers: Authenticated user headers
# - test_user: Sample user for testing
# - test_document: Sample document for testing
