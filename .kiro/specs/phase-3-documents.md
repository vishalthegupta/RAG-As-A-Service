# Phase 3 — Documents

## Context
Phases 1 and 2 are complete. Auth works, DB is ready, config and exceptions
are all set. Now build the full document lifecycle — upload, async processing
(parse → chunk → embed → store), and CRUD endpoints.
Read all files in .kiro/steering/ before writing any code.

## Goal
A user can upload a document, the system processes it asynchronously, and the
document becomes ready for RAG. This phase builds the entire processing pipeline.

## Rules
- Implement features in the exact order listed — each builds on the previous
- Features 11–14 are individual pipeline modules, each tested in isolation
- Feature 15 (Celery task) wires 11–14 together — do NOT start it until all four pass
- After each feature: write tests, run them, confirm green, report, then proceed

---

## Feature 10 — POST /documents (Upload Endpoint)

### What to build

**`app/documents/storage.py`** — Storage abstraction
```python
class StorageBackend(ABC):
    @abstractmethod
    async def save(self, file_data: bytes, path: str) -> str: ...
    @abstractmethod
    async def read(self, path: str) -> bytes: ...
    @abstractmethod
    async def delete(self, path: str) -> None: ...
    @abstractmethod
    def get_storage_path(self, user_id: str, doc_id: str, filename: str) -> str: ...

class LocalFileStorage(StorageBackend):
    # Implement all 4 methods
    # get_storage_path returns: {UPLOAD_DIR}/{user_id}/{doc_id}/{secure_filename}
    # save creates parent dirs automatically
    # Uses aiofiles for async read/write

def get_storage_backend() -> StorageBackend:
    # reads settings.STORAGE_BACKEND
    # returns LocalFileStorage(settings.UPLOAD_DIR)
```

**`app/documents/schemas.py`**
```python
class DocumentUploadResponse(BaseModel):
    id: UUID
    name: str
    status: str
    created_at: datetime

class DocumentResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    original_filename: str
    file_size_bytes: int
    mime_type: str
    status: str
    chunk_count: int | None
    created_at: datetime
    processing_job: "ProcessingJobResponse | None"
    model_config = ConfigDict(from_attributes=True)

class ProcessingJobResponse(BaseModel):
    status: str
    progress_pct: int
    error_detail: str | None
    model_config = ConfigDict(from_attributes=True)

class DocumentStatusResponse(BaseModel):
    status: str
    progress_pct: int
    chunk_count: int | None
    error_detail: str | None
```

**`app/documents/service.py`** — upload_document()
```python
async def upload_document(
    db: AsyncSession,
    current_user: User,
    file: UploadFile,
    name: str,
    description: str | None
) -> Document:
    # 1. Validate file size (< settings.MAX_FILE_SIZE_MB)
    # 2. Validate MIME type using python-magic on first 2048 bytes
    #    Raise FileTooLargeError or UnsupportedFileTypeError accordingly
    # 3. Read full file content
    # 4. Create Document DB record (status=PENDING)
    # 5. Create ProcessingJob record (status=QUEUED)
    # 6. Save file to storage backend
    # 7. Queue Celery task: process_document.apply_async(args=[str(doc.id)], countdown=1)
    # 8. Save celery_task_id to ProcessingJob
    # 9. Commit and return Document
```

**`app/documents/router.py`**
```python
POST /documents
  Auth: required (get_current_user)
  Body: multipart/form-data {file, name: str, description: str (optional)}
  Response 201: DocumentUploadResponse
  Rate limit: settings.UPLOAD_RATE_LIMIT
```

### Tests to write
```python
async def test_upload_pdf_success(client, auth_headers, sample_pdf):
    res = await client.post("/api/v1/documents", headers=auth_headers,
        files={"file": ("test.pdf", sample_pdf, "application/pdf")},
        data={"name": "Test Doc"})
    assert res.status_code == 201
    assert res.json()["status"] == "PENDING"

async def test_upload_requires_auth(client, sample_pdf):
    assert res.status_code == 401

async def test_upload_invalid_mime_type(client, auth_headers):
    # upload an .exe file
    assert res.status_code == 400

async def test_upload_file_too_large(client, auth_headers):
    # file > 50MB
    assert res.status_code == 413

async def test_upload_creates_processing_job(client, auth_headers, db, sample_pdf):
    # verify ProcessingJob record was created in DB
    job = db.query(ProcessingJob).filter_by(document_id=doc_id).first()
    assert job is not None
    assert job.status == JobStatus.QUEUED
```

### Done when
- All 5 tests pass
- File saved to correct path in UPLOAD_DIR
- ProcessingJob created with QUEUED status
- Celery task queued (can verify via mock)

---

## Feature 11 — Document Parser

### What to build

**`app/processing/parser.py`**
```python
class DocumentParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> str:
        """Extract plain text. Raise DocumentProcessingError on failure."""

class PdfParser(DocumentParser):
    def parse(self, file_path: str) -> str:
        # Use fitz (PyMuPDF)
        # Join pages with "\n\n"
        # Skip blank pages
        # Raise DocumentProcessingError if file unreadable

class DocxParser(DocumentParser):
    def parse(self, file_path: str) -> str:
        # Use python-docx
        # Join non-empty paragraphs with "\n\n"

class TxtParser(DocumentParser):
    def parse(self, file_path: str) -> str:
        # Read with utf-8, errors="replace"

PARSERS: dict[str, type[DocumentParser]] = {
    "application/pdf": PdfParser,
    "text/plain": TxtParser,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxParser,
}

def get_parser(mime_type: str) -> DocumentParser:
    cls = PARSERS.get(mime_type)
    if not cls:
        raise UnsupportedFileTypeError(f"No parser for {mime_type}")
    return cls()
```

### Tests to write
```python
def test_parse_pdf(sample_pdf_path):
    parser = get_parser("application/pdf")
    text = parser.parse(sample_pdf_path)
    assert isinstance(text, str)
    assert len(text) > 0

def test_parse_txt(sample_txt_path):
    parser = get_parser("text/plain")
    text = parser.parse(sample_txt_path)
    assert "expected content" in text

def test_parse_docx(sample_docx_path):
    parser = get_parser("application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    text = parser.parse(sample_docx_path)
    assert len(text) > 0

def test_unsupported_mime_raises(tmp_path):
    with pytest.raises(UnsupportedFileTypeError):
        get_parser("application/octet-stream")

def test_corrupt_pdf_raises(tmp_path):
    bad_pdf = tmp_path / "bad.pdf"
    bad_pdf.write_bytes(b"not a pdf")
    with pytest.raises(DocumentProcessingError):
        PdfParser().parse(str(bad_pdf))
```

### Done when
- All 5 tests pass
- Each parser returns a non-empty string for valid files
- Corrupt file raises DocumentProcessingError

---

## Feature 12 — Text Chunker

### What to build

**`app/processing/chunker.py`**
```python
@dataclass
class ChunkMetadata:
    doc_id: str
    chunk_index: int
    text: str
    char_start: int
    char_end: int

class TextChunker:
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        min_chunk_size: int = 100
    ): ...

    def chunk_text(self, text: str, doc_id: str) -> list[ChunkMetadata]:
        """
        Split algorithm:
        1. Split by "\n\n" first (paragraphs)
        2. If segment > chunk_size: split by "\n", then ". ", then " "
        3. Merge adjacent segments smaller than min_chunk_size
        4. Add overlap: prepend last chunk_overlap chars of previous chunk
        5. Hard cap: never exceed chunk_size + overlap in final chunk
        6. Track char_start and char_end for each chunk
        7. Return list with chunk_index assigned sequentially
        """
```

### Tests to write
```python
def test_chunk_short_text():
    chunker = TextChunker(chunk_size=512)
    chunks = chunker.chunk_text("Short text.", doc_id="test-id")
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].doc_id == "test-id"

def test_chunk_long_text_creates_multiple():
    long_text = "word " * 500   # ~2500 chars
    chunks = chunker.chunk_text(long_text, doc_id="test")
    assert len(chunks) > 1
    assert all(len(c.text) <= 576 for c in chunks)  # chunk_size + overlap

def test_chunk_overlap_present():
    # Last chars of chunk[0] should appear at start of chunk[1]
    ...

def test_chunk_metadata_accurate():
    text = "Hello world. " * 100
    chunks = chunker.chunk_text(text, doc_id="abc")
    for c in chunks:
        assert text[c.char_start:c.char_end].strip() in c.text or c.text in text

def test_chunk_no_empty_chunks():
    chunks = chunker.chunk_text(text, doc_id="test")
    assert all(len(c.text.strip()) >= 10 for c in chunks)

def test_chunk_indices_sequential():
    chunks = chunker.chunk_text(long_text, doc_id="test")
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
```

### Done when
- All 6 tests pass
- No chunk exceeds chunk_size + overlap length
- All chunk_index values are sequential starting from 0

---

## Feature 13 — Embedding Service

### What to build

**`app/processing/embedder.py`**
```python
class EmbeddingService:
    _instance: ClassVar["EmbeddingService | None"] = None
    _model: SentenceTransformer | None = None

    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load_model()
        return cls._instance

    def _load_model(self) -> None:
        self._model = SentenceTransformer(
            settings.EMBEDDING_MODEL,
            cache_folder="./model_cache"
        )

    def encode(
        self,
        texts: list[str],
        batch_size: int = 32
    ) -> np.ndarray:
        # normalize_embeddings=True (enables cosine via dot product)
        # Returns shape: (len(texts), 384)
        # Raise EmbeddingError on failure

    def encode_single(self, text: str) -> list[float]:
        # encode([text])[0].tolist()
        # Returns flat list of 384 floats
```

### Tests to write (mock the model — do not load real model in tests)
```python
@pytest.fixture
def mock_embedding_service(monkeypatch):
    def fake_encode(self, texts, batch_size=32):
        return np.random.rand(len(texts), 384).astype(np.float32)
    monkeypatch.setattr(EmbeddingService, "_load_model", lambda self: None)
    monkeypatch.setattr(EmbeddingService, "encode", fake_encode)

def test_encode_returns_correct_shape(mock_embedding_service):
    svc = EmbeddingService.get_instance()
    result = svc.encode(["text one", "text two"])
    assert result.shape == (2, 384)

def test_encode_single_returns_list(mock_embedding_service):
    svc = EmbeddingService.get_instance()
    result = svc.encode_single("hello")
    assert isinstance(result, list)
    assert len(result) == 384

def test_singleton_returns_same_instance():
    a = EmbeddingService.get_instance()
    b = EmbeddingService.get_instance()
    assert a is b
```

### Done when
- All 3 tests pass (with mocked model)
- `EmbeddingService.get_instance()` always returns same object
- `encode()` output shape is always `(n, 384)`

---

## Feature 14 — ChromaDB Client + Upsert Operations

### What to build

**`app/vector_store/client.py`**
```python
_client: chromadb.ClientAPI | None = None

def get_chroma_client() -> chromadb.ClientAPI:
    # PersistentClient with settings.CHROMA_PERSIST_DIRECTORY
    # Singleton pattern

def get_or_create_collection(user_id: str) -> chromadb.Collection:
    # collection_name = f"user_{user_id.replace('-', '_')}"
    # metadata={"hnsw:space": "cosine"}
```

**`app/vector_store/operations.py`**
```python
def upsert_chunks(
    user_id: str,
    chunks: list[ChunkMetadata],
    embeddings: np.ndarray,
    doc_name: str
) -> None:
    # ids: [f"{chunk.doc_id}_chunk_{chunk.chunk_index}"]
    # metadata per chunk: doc_id, doc_name, chunk_index, user_id, char_start, char_end, created_at
    # Batch upsert in groups of 100

def query_similar(
    user_id: str,
    query_embedding: list[float],
    top_k: int = 5
) -> list[dict]:
    # Returns list of {text, metadata, distance}
    # Filters: distance < settings.RAG_SIMILARITY_THRESHOLD

def delete_by_doc_id(user_id: str, doc_id: str) -> None:
    # collection.delete(where={"doc_id": str(doc_id)})
```

### Tests to write (use chromadb in-memory client for tests)
```python
@pytest.fixture
def chroma_collection():
    client = chromadb.EphemeralClient()
    return client.get_or_create_collection("test_user", metadata={"hnsw:space": "cosine"})

def test_upsert_and_query(monkeypatch, chroma_collection):
    # upsert 3 chunks, query, verify results returned

def test_delete_by_doc_id(monkeypatch, chroma_collection):
    # upsert chunks for doc A and doc B
    # delete doc A
    # verify doc A chunks gone, doc B chunks still present

def test_query_returns_metadata(monkeypatch, chroma_collection):
    # verify returned results include doc_id, doc_name, chunk_index
```

### Done when
- All 3 tests pass
- `delete_by_doc_id` only deletes chunks for that specific doc
- Metadata schema matches spec exactly

---

## Feature 15 — Celery process_document Task

### What to build

**`app/processing/worker.py`**
```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="process_document"
)
def process_document(self, document_id: str) -> dict:
    """
    Full pipeline in this exact order:
    1. Load Document from DB, update status=PROCESSING, job status=RUNNING, progress=0
    2. Parse file → plain text (Feature 11)           → update progress=25
    3. Chunk text (Feature 12)                         → update progress=50
    4. Batch encode chunks (Feature 13, batch_size=32) → update progress=75
    5. Upsert to ChromaDB (Feature 14)                 → update progress=90
    6. Update document.status=READY, chunk_count, job status=DONE, progress=100

    On any exception:
    - Update document.status=FAILED, error_message=str(e)
    - Update job.status=FAILED, error_detail=str(e)
    - Log error with doc_id
    - Retry via self.retry(exc=exc)
    """
```

**`celery_app.py`**
```python
# task_track_started=True
# task_acks_late=True
# worker_prefetch_multiplier=1
# task_reject_on_worker_lost=True
```

### Tests to write (run task synchronously with .apply())
```python
def test_process_document_success(db_session, sample_pdf_path):
    doc = create_test_document(db_session, file_path=sample_pdf_path, mime_type="application/pdf")
    result = process_document.apply(args=[str(doc.id)])
    assert result.successful()
    db_session.refresh(doc)
    assert doc.status == DocumentStatus.READY
    assert doc.chunk_count > 0

def test_process_document_updates_job_status(db_session, sample_pdf_path):
    # verify ProcessingJob.status == JobStatus.DONE after task

def test_process_document_missing_file(db_session):
    doc = create_test_document(db_session, file_path="/nonexistent/file.pdf")
    result = process_document.apply(args=[str(doc.id)])
    db_session.refresh(doc)
    assert doc.status == DocumentStatus.FAILED
    assert doc.error_message is not None

def test_process_document_chunks_in_chromadb(db_session, sample_pdf_path):
    # after task, verify chunks exist in ChromaDB collection
    collection = get_or_create_collection(str(doc.user_id))
    results = collection.get(where={"doc_id": str(doc.id)})
    assert len(results["ids"]) > 0
```

### Done when
- All 4 tests pass
- Task runs all 6 steps in order
- Failed task sets correct status on both Document and ProcessingJob
- Chunks verifiably exist in ChromaDB after success

---

## Feature 16 — GET /documents (List)

**`app/documents/service.py`** — add `list_documents()`
```python
# Paginated, ordered by created_at DESC
# Joins with ProcessingJob for status
# Only returns documents belonging to current_user
```

**Router:**
```python
GET /documents?skip=0&limit=50
  Auth: required
  Response 200: list[DocumentResponse]
```

**Tests:**
```python
async def test_list_documents_success(client, auth_headers, uploaded_doc):
    res = await client.get("/api/v1/documents", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

async def test_list_only_own_documents(client, auth_headers, other_user_doc):
    # Must not see other user's documents
    assert len(res.json()) == 0

async def test_list_empty_returns_empty_array(client, auth_headers):
    assert res.json() == []
```

---

## Feature 17 — GET /documents/{id} (Detail)

**`app/documents/service.py`** — add `get_document()`
```python
# Fetch with ProcessingJob joined
# Enforce user_id ownership → raise DocumentNotFoundError if mismatch
```

**Tests:**
```python
async def test_get_document_success(client, auth_headers, uploaded_doc):
    res = await client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert res.status_code == 200
    assert "processing_job" in res.json()

async def test_get_other_users_document_returns_404(client, auth_headers, other_doc):
    assert res.status_code == 404   # not 403

async def test_get_nonexistent_document_returns_404(client, auth_headers):
    assert res.status_code == 404
```

---

## Feature 18 — GET /documents/{id}/status (Polling)

**Router:**
```python
GET /documents/{document_id}/status
  Auth: required
  Response 200: DocumentStatusResponse {status, progress_pct, chunk_count, error_detail}
```

**Tests:**
```python
async def test_status_pending_document(client, auth_headers, pending_doc):
    res = await client.get(f"/api/v1/documents/{doc_id}/status", headers=auth_headers)
    assert res.json()["status"] == "PENDING"
    assert res.json()["progress_pct"] == 0

async def test_status_ready_document(client, auth_headers, ready_doc):
    assert res.json()["status"] == "READY"
    assert res.json()["chunk_count"] > 0
```

---

## Feature 19 — DELETE /documents/{id}

**`app/documents/service.py`** — add `delete_document()`
```python
# 1. Fetch document, enforce ownership
# 2. Delete ChromaDB chunks: delete_by_doc_id(user_id, doc_id)
# 3. Delete file from storage backend
# 4. Delete ProcessingJob record
# 5. Delete Document record
# All in a single transaction — if any step fails, rollback
```

**Tests:**
```python
async def test_delete_document_success(client, auth_headers, ready_doc):
    res = await client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert res.status_code == 200
    # verify gone from DB
    # verify file deleted from disk
    # verify chunks deleted from ChromaDB

async def test_delete_other_users_document_returns_404(client, auth_headers, other_doc):
    assert res.status_code == 404

async def test_delete_nonexistent_returns_404(client, auth_headers):
    assert res.status_code == 404
```

---

## Phase 3 Complete — Checklist

Before moving to Phase 4, verify all of the following:

- [ ] `pytest tests/` exits with 0 failures
- [ ] Upload a real PDF → verify chunks appear in ChromaDB
- [ ] Document status transitions correctly: PENDING → PROCESSING → READY
- [ ] Deleting a document removes chunks from ChromaDB, file from disk, record from DB
- [ ] Listing documents only returns the current user's documents
- [ ] All ownership checks return 404 (not 403)

Report this summary when done:
```
✅ Phase 3 complete
   Features: 10/10 (cumulative: 19/37)
   Tests: N passed, 0 failed
   Ready for Phase 4: Chat / RAG
```
