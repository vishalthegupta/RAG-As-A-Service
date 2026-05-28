# RAG-as-a-Service — High Level Design (HLD)

## 1. Product Vision

A **No-Code RAG Platform** that lets any user upload their documents and get a fully functional RAG chatbot in minutes — no ML knowledge required. Built for extensibility so new features (multi-doc, delete, re-index, sharing) integrate with zero rework.

---

## 2. System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                               │
│                    React SPA (Vite + Tailwind)                       │
│   Auth Pages │ Dashboard │ Upload Wizard │ Chat Interface           │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTPS / REST + SSE
┌───────────────────────────▼─────────────────────────────────────────┐
│                         API GATEWAY LAYER                            │
│                    FastAPI (Python 3.11+)                            │
│       /auth  │  /documents  │  /chat  │  /health                    │
│              JWT Middleware + Rate Limiter                           │
└──────┬──────────────────┬───────────────────────┬────────────────────┘
       │                  │                       │
┌──────▼──────┐  ┌────────▼────────┐  ┌──────────▼──────────┐
│  Auth       │  │  Document       │  │   Chat / RAG         │
│  Service    │  │  Service        │  │   Service            │
│             │  │                 │  │                      │
│ Register    │  │ Upload          │  │ Query Embedding      │
│ Login       │  │ Parse           │  │ Vector Search        │
│ JWT Issue   │  │ Chunk           │  │ Context Assembly     │
│             │  │ Embed           │  │ LLM Inference        │
└──────┬──────┘  └────────┬────────┘  └──────────┬───────────┘
       │                  │                       │
┌──────▼──────────────────▼───────────────────────▼───────────────────┐
│                       DATA LAYER                                     │
│                                                                      │
│  ┌─────────────────────┐      ┌──────────────────────────────────┐  │
│  │   PostgreSQL         │      │           ChromaDB               │  │
│  │                     │      │                                  │  │
│  │  users              │      │  Collection per user             │  │
│  │  documents          │      │  (user_{user_id})                │  │
│  │  chat_sessions      │      │                                  │  │
│  │  chat_messages      │      │  Stores: chunk text + metadata   │  │
│  │  processing_jobs    │      │  Indexed by: sentence-transformers│  │
│  └─────────────────────┘      └──────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│                    ASYNC WORKER LAYER                                 │
│                  Celery + Redis (Task Queue)                          │
│                                                                      │
│   Task: process_document(doc_id)                                     │
│     → Parse file (PDF/DOCX/TXT)                                      │
│     → Chunk text (RecursiveCharacterTextSplitter)                    │
│     → Generate embeddings (SentenceTransformer)                      │
│     → Upsert to ChromaDB                                             │
│     → Update job status in PostgreSQL                                │
└──────────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│                     EXTERNAL SERVICES                                 │
│                                                                      │
│   Free LLM: Groq API (llama3-8b-8192) — primary                     │
│   Fallback: HuggingFace Inference API (mistral-7b)                   │
│   File Storage: Local filesystem (./uploads/) — S3-ready interface   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core User Flows

### 3.1 Registration & Onboarding
```
User → Register (email + password) → Email verified → Dashboard
```

### 3.2 Document Upload & Processing
```
User → Upload Doc + (name, description) → API saves file
  → Celery task queued → Status: PROCESSING
  → Parse → Chunk → Embed → Store in ChromaDB
  → Status: READY → User notified (polling/SSE)
  → RAG Chatbot activated for user
```

### 3.3 Chat (RAG Query)
```
User types query → API embeds query (SentenceTransformer)
  → ChromaDB similarity search (top-k=5)
  → Retrieve chunks + metadata
  → Build prompt (system + context + history + query)
  → Groq API → Stream response back via SSE
  → Message saved to chat_messages table
```

---

## 4. Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | React 18 + Vite + Tailwind CSS | Fast build, great DX |
| Backend | FastAPI (Python 3.11) | Async-native, auto OpenAPI docs |
| Task Queue | Celery + Redis | Reliable async processing |
| Primary DB | PostgreSQL 15 | ACID, relational metadata |
| Vector DB | ChromaDB (persistent) | Local, no infra cost, easy API |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Free, fast, 384-dim, good quality |
| LLM | Groq API (free tier) | Fast inference, free quota |
| LLM Fallback | HuggingFace Inference API | Free tier backup |
| Auth | JWT (PyJWT) + bcrypt | Stateless, standard |
| File Parse | PyMuPDF (PDF), python-docx (DOCX), built-in (TXT) | Comprehensive coverage |
| Containerization | Docker + Docker Compose | One-command startup |

---

## 5. Key Design Principles

### 5.1 Extensibility-First
- **Storage abstraction**: `StorageBackend` interface — swap local FS for S3 by changing one config value
- **LLM abstraction**: `LLMProvider` interface — add new models without touching chat logic  
- **Per-user ChromaDB collections**: Adding multi-doc support = just upsert more chunks to same collection
- **Document states machine**: `PENDING → PROCESSING → READY | FAILED` — adding re-index = reset to PENDING

### 5.2 Stateless API
- All state in DB/Redis — any API instance is interchangeable
- JWT tokens carry user identity — no server-side sessions

### 5.3 Async Processing
- Document processing is CPU/IO heavy — always off the request thread
- Job status exposed via polling endpoint (later: WebSocket upgrade)

---

## 6. Security Considerations

- Passwords hashed with bcrypt (cost factor 12)
- JWT expiry: 24h access token, 7d refresh token
- All document/chat endpoints require valid JWT
- Users can ONLY access their own documents/chats (enforced at service layer)
- File uploads: MIME type validation + file size limit (50MB default)
- Rate limiting: 60 req/min per user on chat endpoint

---

## 7. Scalability Path

| Current (MVP) | Future Scale |
|---|---|
| Single FastAPI process | Multiple workers behind nginx |
| Local ChromaDB | ChromaDB Cloud or Qdrant/Weaviate |
| Local file storage | AWS S3 |
| Single Celery worker | Worker pool + priority queues |
| Groq free tier | OpenAI / Anthropic paid tier |
| Single Postgres | Read replicas |

---

## 8. Component Responsibility Matrix

| Component | Owns | Does NOT own |
|---|---|---|
| Auth Service | User identity, tokens | Business logic |
| Document Service | File lifecycle, job status | Embedding logic |
| RAG Worker (Celery) | Parsing, chunking, embedding | HTTP concerns |
| Chat Service | Query flow, history | Embedding model loading |
| Embedding Module | Model loading, encode() | Storage |
| ChromaDB Module | Vector CRUD | Business logic |
| LLM Module | Provider abstraction, streaming | Context assembly |

---

## 9. Future Features (Pre-Designed Hooks)

| Feature | Hook Already In Design |
|---|---|
| Multi-document upload | `documents` table has `user_id`; ChromaDB collection is per-user, chunk metadata has `doc_id` |
| Delete document | `DELETE /documents/{id}` → delete chunks by `doc_id` metadata filter in ChromaDB |
| Re-index document | Reset status → re-queue Celery task |
| Document sharing | Add `shared_with` table; `GET /chat/{share_token}` public endpoint |
| Usage analytics | `chat_messages` table tracks all queries; analytics service reads it |
| Webhook on ready | `processing_jobs` has `webhook_url` column (nullable) |
| API key access | Add `api_keys` table; alternate auth middleware |