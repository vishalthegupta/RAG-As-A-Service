# RAG-as-a-Service — Low Level Design (LLD)

## 1. Backend Module Breakdown

### 1.1 Project Layout
```
backend/
├── app/
│   ├── main.py                  # FastAPI app factory, middleware registration
│   ├── config.py                # Pydantic Settings (env-based config)
│   ├── dependencies.py          # Shared FastAPI Depends (db session, current user)
│   │
│   ├── auth/
│   │   ├── router.py            # POST /auth/register, /auth/login, /auth/refresh
│   │   ├── service.py           # register_user(), login_user(), refresh_token()
│   │   ├── schemas.py           # RegisterRequest, LoginRequest, TokenResponse
│   │   ├── models.py            # SQLAlchemy User model
│   │   └── utils.py             # hash_password(), verify_password(), create_jwt()
│   │
│   ├── documents/
│   │   ├── router.py            # POST /documents, GET /documents, GET /documents/{id}, DELETE /documents/{id}
│   │   ├── service.py           # upload_document(), get_documents(), delete_document()
│   │   ├── schemas.py           # DocumentUploadResponse, DocumentStatus, DocumentList
│   │   ├── models.py            # SQLAlchemy Document, ProcessingJob models
│   │   └── storage.py           # StorageBackend ABC + LocalFileStorage implementation
│   │
│   ├── chat/
│   │   ├── router.py            # POST /chat/sessions, GET /chat/sessions, POST /chat/{session_id}/message, GET /chat/{session_id}/history
│   │   ├── service.py           # create_session(), send_message(), get_history()
│   │   ├── schemas.py           # ChatRequest, ChatResponse, SessionCreate
│   │   ├── models.py            # SQLAlchemy ChatSession, ChatMessage models
│   │   └── rag_pipeline.py      # retrieve_context(), build_prompt(), stream_response()
│   │
│   ├── processing/
│   │   ├── worker.py            # Celery app instance + task: process_document()
│   │   ├── parser.py            # DocumentParser: parse_pdf(), parse_docx(), parse_txt()
│   │   ├── chunker.py           # TextChunker: chunk_text() with overlap
│   │   └── embedder.py          # EmbeddingService: singleton model loader + encode()
│   │
│   ├── vector_store/
│   │   ├── client.py            # ChromaDB client singleton
│   │   ├── operations.py        # upsert_chunks(), query_similar(), delete_by_doc_id()
│   │   └── schemas.py           # ChunkMetadata dataclass
│   │
│   └── llm/
│       ├── base.py              # LLMProvider ABC with stream_chat() method
│       ├── groq_provider.py     # GroqProvider implementation
│       ├── huggingface_provider.py  # HuggingFaceProvider implementation
│       └── factory.py           # get_llm_provider() — reads config, returns provider
│
├── celery_app.py                # Celery configuration (broker=Redis, backend=Redis)
├── alembic/                     # DB migrations
│   ├── env.py
│   └── versions/
├── tests/
│   ├── unit/
│   └── integration/
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## 2. Data Models (SQLAlchemy)

### 2.1 User
```python
class User(Base):
    __tablename__ = "users"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: str = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password: str = Column(String(255), nullable=False)
    full_name: str = Column(String(255), nullable=True)
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    documents: List["Document"] = relationship("Document", back_populates="owner")
    chat_sessions: List["ChatSession"] = relationship("ChatSession", back_populates="user")
```

### 2.2 Document
```python
class Document(Base):
    __tablename__ = "documents"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: UUID = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: str = Column(String(255), nullable=False)           # user-given display name
    description: str = Column(Text, nullable=True)            # user-given description
    original_filename: str = Column(String(500), nullable=False)
    file_path: str = Column(String(1000), nullable=False)     # storage path
    file_size_bytes: int = Column(BigInteger, nullable=False)
    mime_type: str = Column(String(100), nullable=False)
    status: str = Column(                                     # ENUM via String + CHECK
        String(20),
        nullable=False,
        default="PENDING"                                     # PENDING|PROCESSING|READY|FAILED
    )
    chunk_count: int = Column(Integer, nullable=True)         # filled after processing
    error_message: str = Column(Text, nullable=True)          # filled on FAILED
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now())

    owner: "User" = relationship("User", back_populates="documents")
    processing_job: "ProcessingJob" = relationship("ProcessingJob", back_populates="document", uselist=False)
```

### 2.3 ProcessingJob
```python
class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: UUID = Column(UUID(as_uuid=True), ForeignKey("documents.id"), unique=True)
    celery_task_id: str = Column(String(255), nullable=True)  # Celery task UUID
    status: str = Column(String(20), nullable=False, default="QUEUED")  # QUEUED|RUNNING|DONE|FAILED
    progress_pct: int = Column(Integer, default=0)            # 0-100
    started_at: datetime = Column(DateTime(timezone=True), nullable=True)
    completed_at: datetime = Column(DateTime(timezone=True), nullable=True)
    error_detail: str = Column(Text, nullable=True)

    document: "Document" = relationship("Document", back_populates="processing_job")
```

### 2.4 ChatSession
```python
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: UUID = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: str = Column(String(255), nullable=True)           # auto-generated from first message
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now())

    user: "User" = relationship("User", back_populates="chat_sessions")
    messages: List["ChatMessage"] = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.created_at")
```

### 2.5 ChatMessage
```python
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: UUID = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    role: str = Column(String(20), nullable=False)            # "user" | "assistant"
    content: str = Column(Text, nullable=False)
    sources: JSON = Column(JSON, nullable=True)               # [{doc_name, chunk_text, score}]
    tokens_used: int = Column(Integer, nullable=True)
    latency_ms: int = Column(Integer, nullable=True)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())

    session: "ChatSession" = relationship("ChatSession", back_populates="messages")
```

---

## 3. Core Algorithms

### 3.1 Text Chunking (chunker.py)
```python
class TextChunker:
    def __init__(
        self,
        chunk_size: int = 512,         # tokens / chars
        chunk_overlap: int = 64,
        separators: list = ["\n\n", "\n", ". ", " ", ""]
    ):
        pass

    def chunk_text(self, text: str, doc_id: str) -> List[ChunkMetadata]:
        """
        Algorithm:
        1. Try splitting by "\n\n" (paragraphs) first
        2. If chunk > chunk_size, split by "\n", then ". ", then " "
        3. Merge small adjacent chunks until chunk_size is reached
        4. Add overlap by appending last `overlap` chars of previous chunk
        5. Return List[ChunkMetadata] with doc_id, chunk_index, text, char_start, char_end
        """
```

### 3.2 Document Processing Pipeline (worker.py Celery task)
```python
@celery_app.task(bind=True, max_retries=3)
def process_document(self, document_id: str):
    """
    Step 1: Load document record from DB, update status=PROCESSING
    Step 2: Read file from storage path
    Step 3: Parse to plain text using DocumentParser
    Step 4: Chunk text using TextChunker → List[ChunkMetadata]
    Step 5: Batch encode chunks using EmbeddingService (batch_size=32)
    Step 6: Upsert to ChromaDB collection (collection_name = f"user_{user_id}")
            Each doc in ChromaDB: {
                id: f"{doc_id}_chunk_{i}",
                embedding: [...],
                document: chunk.text,
                metadata: {
                    "doc_id": doc_id,
                    "doc_name": document.name,
                    "chunk_index": i,
                    "user_id": user_id
                }
            }
    Step 7: Update document.chunk_count, document.status=READY
    Step 8: Update processing_job.status=DONE, progress=100

    On error: document.status=FAILED, job.error_detail=str(e), retry with backoff
    """
```

### 3.3 RAG Query Pipeline (rag_pipeline.py)
```python
async def rag_query(
    user_id: str,
    session_id: str,
    user_query: str,
    chat_history: List[dict],   # last 6 messages for context window
    top_k: int = 5
) -> AsyncGenerator[str, None]:
    """
    Step 1: Embed user_query using EmbeddingService.encode(user_query)
    Step 2: ChromaDB query on collection f"user_{user_id}"
            → returns top_k chunks with distances
    Step 3: Filter chunks with distance < SIMILARITY_THRESHOLD (0.8)
    Step 4: Deduplicate by doc_id (keep best chunk per doc if same doc appears multiple times)
    Step 5: Build prompt:
            SYSTEM: "You are a helpful assistant. Answer questions using ONLY the context below.
                     If the answer is not in the context, say you don't know."
            CONTEXT: "\n\n---\n\n".join([chunk.text for chunk in retrieved])
            HISTORY: last 6 messages formatted as "User: ...\nAssistant: ..."
            USER: user_query
    Step 6: Call LLMProvider.stream_chat(prompt) → AsyncGenerator[str]
    Step 7: Yield chunks to SSE stream
    Step 8: After stream complete: save full response + sources to chat_messages
    """
```

---

## 4. API Endpoint Specifications

### Auth Routes (`/api/v1/auth`)
```
POST /register
  Body: { email, password, full_name? }
  Response 201: { user_id, email, full_name, created_at }
  Response 400: { detail: "Email already registered" }

POST /login
  Body: { email, password }
  Response 200: { access_token, refresh_token, token_type: "bearer", expires_in: 86400 }
  Response 401: { detail: "Invalid credentials" }

POST /refresh
  Body: { refresh_token }
  Response 200: { access_token, expires_in }

GET /me
  Header: Authorization: Bearer <token>
  Response 200: { user_id, email, full_name, created_at }
```

### Document Routes (`/api/v1/documents`)
```
POST /
  Header: Authorization: Bearer <token>
  Body: multipart/form-data { file, name, description? }
  Response 201: { document_id, name, status: "PENDING", created_at }
  
  Validation:
  - file size ≤ 50MB
  - mime_type in [application/pdf, text/plain, application/vnd.openxmlformats...]
  - User must not have document with same name (warn, not block)

GET /
  Header: Authorization: Bearer <token>
  Response 200: [{ document_id, name, status, chunk_count, created_at, processing_job }]

GET /{document_id}
  Header: Authorization: Bearer <token>
  Response 200: { ...document fields, processing_job: { status, progress_pct, error_detail } }
  Response 404: if not found OR belongs to different user

DELETE /{document_id}
  Header: Authorization: Bearer <token>
  Response 200: { message: "Document deleted successfully" }
  Side effects: delete file from storage, delete ChromaDB chunks by doc_id filter

GET /{document_id}/status   ← Polling endpoint
  Header: Authorization: Bearer <token>
  Response 200: { status, progress_pct, chunk_count, error_detail }
```

### Chat Routes (`/api/v1/chat`)
```
POST /sessions
  Header: Authorization: Bearer <token>
  Body: { title? }
  Response 201: { session_id, title, created_at }
  Validation: User must have at least one READY document

GET /sessions
  Header: Authorization: Bearer <token>
  Response 200: [{ session_id, title, created_at, message_count }]

POST /sessions/{session_id}/messages
  Header: Authorization: Bearer <token>
  Body: { message: string }
  Response 200: SSE stream
    event: token     data: {"token": "Hello"}
    event: token     data: {"token": " there"}
    event: sources   data: {"sources": [{doc_name, chunk_text, score}]}
    event: done      data: {"message_id": "...", "latency_ms": 340}
    event: error     data: {"detail": "LLM unavailable, please retry"}

GET /sessions/{session_id}/messages
  Header: Authorization: Bearer <token>
  Response 200: [{ message_id, role, content, sources, created_at }]

DELETE /sessions/{session_id}
  Header: Authorization: Bearer <token>
  Response 200: { message: "Session deleted" }
```

### Health Routes
```
GET /health
  Response 200: { status: "ok", version: "1.0.0" }

GET /health/detailed
  Response 200: {
    api: "ok",
    database: "ok" | "error",
    redis: "ok" | "error",
    chromadb: "ok" | "error",
    embedding_model: "loaded" | "loading" | "error"
  }
```

---

## 5. ChromaDB Collection Design

```
Collection name: user_{user_id}    (one per user, created on first document upload)

Document (chunk) structure:
{
    id: "{doc_id}_chunk_{index}",
    embedding: [float * 384],          # all-MiniLM-L6-v2 output
    document: "chunk text here...",
    metadata: {
        "doc_id": "uuid",
        "doc_name": "My Document",
        "chunk_index": 3,
        "user_id": "uuid",
        "char_start": 1024,
        "char_end": 1536,
        "created_at": "2024-01-01T00:00:00Z"
    }
}

Query example:
collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
    where={"doc_id": {"$in": active_doc_ids}},   # optional filter by specific docs
    include=["documents", "metadatas", "distances"]
)

Delete by doc_id (on document delete):
collection.delete(where={"doc_id": doc_id})
```

---

## 6. Embedding Service (Singleton Pattern)

```python
# processing/embedder.py

class EmbeddingService:
    _instance: Optional["EmbeddingService"] = None
    _model: Optional[SentenceTransformer] = None

    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2",
                cache_folder="./model_cache"
            )
        return cls._instance

    def encode(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        return self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True    # cosine similarity via dot product
        )
```

---

## 7. LLM Provider Abstraction

```python
# llm/base.py
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def stream_chat(
        self,
        system_prompt: str,
        messages: List[dict],         # [{"role": "user/assistant", "content": "..."}]
        max_tokens: int = 1024,
        temperature: float = 0.1
    ) -> AsyncGenerator[str, None]:
        """Yields token strings one at a time"""
        pass

# llm/groq_provider.py
class GroqProvider(LLMProvider):
    MODEL = "llama3-8b-8192"
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    async def stream_chat(self, system_prompt, messages, max_tokens=1024, temperature=0.1):
        payload = {
            "model": self.MODEL,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.BASE_URL, json=payload, headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}"
            }) as resp:
                async for line in resp.content:
                    # parse SSE delta and yield token
                    ...

# llm/factory.py
def get_llm_provider() -> LLMProvider:
    provider = settings.LLM_PROVIDER   # "groq" | "huggingface"
    if provider == "groq":
        return GroqProvider()
    elif provider == "huggingface":
        return HuggingFaceProvider()
    raise ValueError(f"Unknown LLM provider: {provider}")
```

---

## 8. Frontend Module Breakdown

```
frontend/
├── src/
│   ├── main.jsx                    # React entry, Router setup
│   ├── App.jsx                     # Route definitions (React Router v6)
│   │
│   ├── api/
│   │   ├── client.js               # Axios instance with JWT interceptors + refresh logic
│   │   ├── auth.js                 # register(), login(), getMe()
│   │   ├── documents.js            # uploadDocument(), listDocuments(), deleteDocument(), pollStatus()
│   │   └── chat.js                 # createSession(), sendMessage() (SSE), getHistory()
│   │
│   ├── store/
│   │   ├── authStore.js            # Zustand: user, token, login(), logout()
│   │   ├── documentStore.js        # Zustand: documents[], uploadProgress, pollingTimers
│   │   └── chatStore.js            # Zustand: sessions[], activeSession, messages[]
│   │
│   ├── pages/
│   │   ├── LoginPage.jsx           # Login form
│   │   ├── RegisterPage.jsx        # Register form
│   │   ├── DashboardPage.jsx       # Overview: doc status cards + quick chat entry
│   │   ├── UploadPage.jsx          # Upload wizard (3 steps)
│   │   └── ChatPage.jsx            # Full chat interface
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppShell.jsx        # Sidebar + top nav wrapper
│   │   │   ├── Sidebar.jsx         # Navigation links
│   │   │   └── ProtectedRoute.jsx  # Auth guard
│   │   ├── documents/
│   │   │   ├── DocumentCard.jsx    # Status badge, name, actions
│   │   │   ├── UploadWizard.jsx    # Multi-step upload form
│   │   │   └── ProcessingStatus.jsx # Real-time progress display
│   │   └── chat/
│   │       ├── ChatWindow.jsx      # Message list + input
│   │       ├── MessageBubble.jsx   # User/assistant message with sources
│   │       ├── SourceAccordion.jsx # Expandable retrieved chunks display
│   │       └── StreamingMessage.jsx # Token-by-token rendering
│   │
│   └── hooks/
│       ├── useSSE.js               # SSE connection hook for streaming
│       ├── useDocumentPolling.js   # Poll document status until READY/FAILED
│       └── useAuth.js              # Auth state helpers
│
├── index.html
├── vite.config.js
├── tailwind.config.js
└── package.json
```

---

## 9. Configuration (config.py)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "RAG-as-a-Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    # Auth
    JWT_SECRET_KEY: str                         # REQUIRED
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440     # 24h
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str                           # postgresql+asyncpg://user:pass@host/db

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # ChromaDB
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_data"

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_MIME_TYPES: list = [
        "application/pdf",
        "text/plain",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]

    # Embedding
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_BATCH_SIZE: int = 32

    # LLM
    LLM_PROVIDER: str = "groq"                 # "groq" | "huggingface"
    GROQ_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""
    HUGGINGFACE_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.2"

    # RAG
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.8
    RAG_MAX_HISTORY_MESSAGES: int = 6
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64

    # Rate Limiting
    CHAT_RATE_LIMIT: str = "60/minute"

    class Config:
        env_file = ".env"
```

---

## 10. Error Handling Strategy

```python
# All service layer errors are custom exceptions:
class RagServiceError(Exception): pass
class DocumentNotFoundError(RagServiceError): pass
class DocumentNotReadyError(RagServiceError): pass   # raised if chat attempted before READY
class StorageError(RagServiceError): pass
class LLMUnavailableError(RagServiceError): pass
class EmbeddingError(RagServiceError): pass

# FastAPI exception handlers map these to HTTP responses:
@app.exception_handler(DocumentNotFoundError)
async def document_not_found_handler(req, exc):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(DocumentNotReadyError)
async def document_not_ready_handler(req, exc):
    return JSONResponse(status_code=409, content={"detail": "No documents ready for chat. Please wait for processing to complete."})
```

---

## 11. Docker Compose Services

```yaml
services:
  api:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql+asyncpg://raguser:ragpass@db:5432/ragdb
      - REDIS_URL=redis://redis:6379/0
      - CHROMA_PERSIST_DIRECTORY=/app/chroma_data
      - UPLOAD_DIR=/app/uploads
    volumes:
      - chroma_data:/app/chroma_data
      - upload_data:/app/uploads
      - model_cache:/app/model_cache
    depends_on: [db, redis]

  worker:
    build: ./backend
    command: celery -A celery_app worker --loglevel=info --concurrency=2
    environment: *api-env         # same env as api
    volumes: *api-volumes
    depends_on: [db, redis]

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: raguser
      POSTGRES_PASSWORD: ragpass
      POSTGRES_DB: ragdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - VITE_API_URL=http://localhost:8000

volumes:
  postgres_data:
  chroma_data:
  upload_data:
  model_cache:
```