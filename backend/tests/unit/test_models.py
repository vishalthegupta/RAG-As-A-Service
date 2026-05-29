"""Tests for database models"""
from __future__ import annotations

import pytest
from uuid import uuid4

from app.auth.models import User
from app.documents.models import Document, ProcessingJob
from app.chat.models import ChatSession, ChatMessage
from app.enums import DocumentStatus, JobStatus, MessageRole


@pytest.mark.asyncio
async def test_user_model_creation(db_session):
    """Test User model can be instantiated with required fields"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed_password_here",
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_document_model_creation(db_session):
    """Test Document model can be instantiated with required fields"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed_password_here",
    )
    db_session.add(user)
    await db_session.commit()
    
    document = Document(
        id=uuid4(),
        user_id=user.id,
        name="Test Document",
        original_filename="test.pdf",
        file_path="/uploads/test.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        status=DocumentStatus.PENDING.value,
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    
    assert document.id is not None
    assert document.user_id == user.id
    assert document.status == DocumentStatus.PENDING.value


@pytest.mark.asyncio
async def test_processing_job_model_creation(db_session):
    """Test ProcessingJob model can be instantiated"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed_password_here",
    )
    db_session.add(user)
    
    document = Document(
        id=uuid4(),
        user_id=user.id,
        name="Test Document",
        original_filename="test.pdf",
        file_path="/uploads/test.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
    )
    db_session.add(document)
    await db_session.commit()
    
    job = ProcessingJob(
        id=uuid4(),
        document_id=document.id,
        status=JobStatus.QUEUED.value,
        progress_pct=0,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    
    assert job.id is not None
    assert job.document_id == document.id
    assert job.status == JobStatus.QUEUED.value
    assert job.progress_pct == 0


@pytest.mark.asyncio
async def test_chat_session_model_creation(db_session):
    """Test ChatSession model can be instantiated"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed_password_here",
    )
    db_session.add(user)
    await db_session.commit()
    
    session = ChatSession(
        id=uuid4(),
        user_id=user.id,
        title="Test Chat",
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    
    assert session.id is not None
    assert session.user_id == user.id
    assert session.title == "Test Chat"


@pytest.mark.asyncio
async def test_chat_message_model_creation(db_session):
    """Test ChatMessage model can be instantiated"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed_password_here",
    )
    db_session.add(user)
    
    session = ChatSession(
        id=uuid4(),
        user_id=user.id,
        title="Test Chat",
    )
    db_session.add(session)
    await db_session.commit()
    
    message = ChatMessage(
        id=uuid4(),
        session_id=session.id,
        role=MessageRole.USER.value,
        content="Hello, world!",
    )
    db_session.add(message)
    await db_session.commit()
    await db_session.refresh(message)
    
    assert message.id is not None
    assert message.session_id == session.id
    assert message.role == MessageRole.USER.value
    assert message.content == "Hello, world!"


@pytest.mark.asyncio
async def test_user_documents_relationship(db_session):
    """Test that user.documents relationship is accessible"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed_password_here",
    )
    db_session.add(user)
    
    document = Document(
        id=uuid4(),
        user_id=user.id,
        name="Test Document",
        original_filename="test.pdf",
        file_path="/uploads/test.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
    )
    db_session.add(document)
    await db_session.commit()
    
    # Properly load the relationship using refresh with attribute names
    await db_session.refresh(user, attribute_names=['documents'])
    
    # Access relationship
    assert len(user.documents) == 1
    assert user.documents[0].name == "Test Document"


@pytest.mark.asyncio
async def test_session_messages_relationship(db_session):
    """Test that session.messages relationship is accessible"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed_password_here",
    )
    db_session.add(user)
    
    session = ChatSession(
        id=uuid4(),
        user_id=user.id,
        title="Test Chat",
    )
    db_session.add(session)
    
    message = ChatMessage(
        id=uuid4(),
        session_id=session.id,
        role=MessageRole.USER.value,
        content="Hello!",
    )
    db_session.add(message)
    await db_session.commit()
    
    # Properly load the relationship using refresh with attribute names
    await db_session.refresh(session, attribute_names=['messages'])
    
    # Access relationship
    assert len(session.messages) == 1
    assert session.messages[0].content == "Hello!"


def test_enums_have_correct_values():
    """Test that enums have correct string values"""
    assert DocumentStatus.PENDING.value == "PENDING"
    assert DocumentStatus.PROCESSING.value == "PROCESSING"
    assert DocumentStatus.READY.value == "READY"
    assert DocumentStatus.FAILED.value == "FAILED"
    
    assert JobStatus.QUEUED.value == "QUEUED"
    assert JobStatus.RUNNING.value == "RUNNING"
    assert JobStatus.DONE.value == "DONE"
    assert JobStatus.FAILED.value == "FAILED"
    
    assert MessageRole.USER.value == "user"
    assert MessageRole.ASSISTANT.value == "assistant"
