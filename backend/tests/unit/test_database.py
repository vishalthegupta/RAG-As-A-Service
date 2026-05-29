"""Tests for database setup"""
from __future__ import annotations

import pytest
from sqlalchemy import text

from app.database import AsyncSessionLocal, SyncSessionLocal
from app.models.base import Base


@pytest.mark.asyncio
async def test_async_session_creation():
    """Test that async database session can be created and closed cleanly"""
    async with AsyncSessionLocal() as session:
        assert session is not None
        # Test a simple query
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_sync_session_creation():
    """Test that sync database session can be created for Celery"""
    with SyncSessionLocal() as session:
        assert session is not None


@pytest.mark.asyncio
async def test_base_metadata_exists():
    """Test that Base.metadata exists and is importable"""
    assert Base.metadata is not None
    assert hasattr(Base.metadata, 'tables')
