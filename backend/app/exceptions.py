"""Custom exceptions for the RAG service"""
from __future__ import annotations


class RagServiceError(Exception):
    """Base exception for all application errors"""
    pass


class DocumentNotFoundError(RagServiceError):
    """Document does not exist or user does not have access"""
    pass


class DocumentNotReadyError(RagServiceError):
    """Document is still processing and not ready for chat"""
    pass


class DocumentProcessingError(RagServiceError):
    """Error occurred during document processing"""
    pass


class StorageError(RagServiceError):
    """File storage operation failed"""
    pass


class LLMUnavailableError(RagServiceError):
    """LLM provider is unavailable"""
    pass


class EmbeddingError(RagServiceError):
    """Embedding generation failed"""
    pass


class DuplicateEmailError(RagServiceError):
    """Email already registered"""
    pass


class FileTooLargeError(RagServiceError):
    """Uploaded file exceeds size limit"""
    pass


class UnsupportedFileTypeError(RagServiceError):
    """File type is not supported"""
    pass


class SessionNotFoundError(RagServiceError):
    """Chat session does not exist or user does not have access"""
    pass
