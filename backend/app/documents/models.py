"""Document models"""
from __future__ import annotations

from uuid import UUID, uuid4
from sqlalchemy import String, Text, BigInteger, Integer, ForeignKey, Column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.models.base import Base, TimestampMixin
from app.enums import DocumentStatus, JobStatus


class Document(Base, TimestampMixin):
    """Document model"""
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    original_filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )
    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DocumentStatus.PENDING.value,
        index=True,
    )
    chunk_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="documents",
    )
    processing_job: Mapped["ProcessingJob | None"] = relationship(
        "ProcessingJob",
        back_populates="document",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, name={self.name}, status={self.status})>"


class ProcessingJob(Base):
    """Processing job model"""
    __tablename__ = "processing_jobs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    celery_task_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=JobStatus.QUEUED.value,
        index=True,
    )
    progress_pct: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    error_detail: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="processing_job",
    )

    def __repr__(self) -> str:
        return f"<ProcessingJob(id={self.id}, document_id={self.document_id}, status={self.status})>"
