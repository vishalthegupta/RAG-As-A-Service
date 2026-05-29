"""Database configuration and session management"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

# Determine if we're using SQLite (for testing) or PostgreSQL (for production)
is_sqlite = "sqlite" in settings.DATABASE_URL.lower()

# Async engine for FastAPI
if is_sqlite:
    # SQLite doesn't support pool_size and max_overflow
    async_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
    )
else:
    # PostgreSQL with connection pooling
    async_engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# Sync engine for Celery workers
if is_sqlite:
    # SQLite doesn't support pool_size and max_overflow
    sync_engine = create_engine(
        settings.SYNC_DATABASE_URL,
        echo=settings.DEBUG,
    )
else:
    # PostgreSQL with connection pooling
    sync_engine = create_engine(
        settings.SYNC_DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )

SyncSessionLocal = sessionmaker(
    sync_engine,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
