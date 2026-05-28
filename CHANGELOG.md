# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup and folder structure
- Configuration management with Pydantic Settings
- Custom exception hierarchy
- Embedding service with sentence-transformers
- ChromaDB client singleton
- Structured logging with structlog
- FastAPI application with global exception handlers
- Docker Compose configuration for all services
- Comprehensive documentation (README, HLD, LLD)
- Environment setup verification script
- Steering rules for development workflow

### Infrastructure
- PostgreSQL 15 for primary database
- Redis 7 for task queue
- ChromaDB for vector storage
- Celery for async processing
- Docker containerization

## [1.0.0] - TBD

### Planned Features
- User authentication (register, login, JWT)
- Document upload and processing
- PDF, DOCX, TXT parsing
- Text chunking and embedding
- Vector storage in ChromaDB
- RAG pipeline with context retrieval
- Streaming chat responses via SSE
- Chat session management
- React frontend with Tailwind CSS
- Real-time processing status
- Rate limiting
- Comprehensive test suite
