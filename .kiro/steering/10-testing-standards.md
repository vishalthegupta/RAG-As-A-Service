# Testing Standards

## Testing Philosophy
- Test behavior, not implementation
- Each test: one assertion group, one scenario
- Tests are documentation — name them like sentences

## Backend Test Structure
```
backend/tests/
├── conftest.py           ← shared fixtures: test DB, test client, mock user
├── unit/
│   ├── test_chunker.py
│   ├── test_embedder.py
│   ├── test_rag_pipeline.py
│   └── test_auth_utils.py
└── integration/
    ├── test_auth_routes.py
    ├── test_document_routes.py
    └── test_chat_routes.py
```

## Test Fixtures (conftest.py)
```python
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session():
    # Use in-memory SQLite for unit tests, test postgres for integration
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    ...

@pytest.fixture
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def auth_headers(client):
    # Register + login, return {"Authorization": "Bearer ..."}
    await client.post("/api/v1/auth/register", json={"email": "test@test.com", "password": "testpass123"})
    res = await client.post("/api/v1/auth/login", json={"email": "test@test.com", "password": "testpass123"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

## What Must Be Tested

### Unit Tests (no DB, no HTTP)
- `TextChunker.chunk_text()` — verify chunk sizes, overlap, metadata
- `EmbeddingService.encode()` — mock the model, verify output shape
- `build_rag_prompt()` — verify prompt structure with various inputs
- `hash_password()` and `verify_password()`
- `create_access_token()` and `decode_token()` — including expiry

### Integration Tests (real DB, real HTTP via httpx)
```python
# Pattern for route tests
async def test_upload_document_success(client, auth_headers, tmp_path):
    pdf_file = create_test_pdf(tmp_path)   # helper that creates a minimal valid PDF
    
    with open(pdf_file, "rb") as f:
        response = await client.post(
            "/api/v1/documents",
            headers=auth_headers,
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"name": "Test Doc", "description": "A test"}
        )
    
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Test Doc"
    assert body["status"] == "PENDING"
    assert "document_id" in body

async def test_upload_requires_auth(client):
    response = await client.post("/api/v1/documents", ...)
    assert response.status_code == 401

async def test_cannot_access_other_users_document(client, auth_headers, other_user_doc_id):
    response = await client.get(f"/api/v1/documents/{other_user_doc_id}", headers=auth_headers)
    assert response.status_code == 404    # not 403!
```

### Celery Task Tests
```python
# Test task logic directly (not via broker) using .apply()
def test_process_document_task(db_session, sample_pdf_path):
    doc = create_test_document(db_session, file_path=sample_pdf_path)
    
    # Run task synchronously in test
    result = process_document.apply(args=[str(doc.id)])
    
    assert result.status == "SUCCESS"
    db_session.refresh(doc)
    assert doc.status == DocumentStatus.READY
    assert doc.chunk_count > 0
```

## Mocking External Services
```python
# Mock Groq API in tests — never call real LLM in tests
@pytest.fixture
def mock_groq(monkeypatch):
    async def fake_stream(*args, **kwargs):
        for token in ["Hello", " ", "world"]:
            yield token
    monkeypatch.setattr(GroqProvider, "stream_chat", fake_stream)

# Mock ChromaDB in unit tests
@pytest.fixture
def mock_chroma(monkeypatch):
    monkeypatch.setattr("app.vector_store.client.get_chroma_client", lambda: FakeChromaClient())
```

## Running Tests
```bash
# Unit tests only (fast)
pytest tests/unit -v

# Integration tests (needs test DB)
pytest tests/integration -v

# All with coverage
pytest --cov=app --cov-report=html

# Minimum coverage gate: 70%
```

## Frontend Tests
- **Vitest** for unit tests
- **React Testing Library** for component tests
- Test custom hooks with `renderHook`
- Mock API calls with `msw` (Mock Service Worker)
- Must test: auth flow, document upload form validation, chat message rendering
