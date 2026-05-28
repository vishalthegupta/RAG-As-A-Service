# Project Overview & Tech Stack

## What We're Building
RAG-as-a-Service — a no-code platform where users upload documents and get a production-ready RAG chatbot. Users register, upload docs, wait for processing, then chat with their data.

## Tech Stack (Non-Negotiable)
| Layer | Technology | Version |
|---|---|---|
| Backend | FastAPI + Python | 3.11+ |
| Task Queue | Celery + Redis | Latest stable |
| Primary DB | PostgreSQL | 15+ |
| Vector DB | ChromaDB (persistent) | Latest stable |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | via sentence-transformers lib |
| LLM | Groq API (primary) / HuggingFace (fallback) | Free tier |
| Frontend | React 18 + Vite + Tailwind CSS | Latest stable |
| Auth | JWT (PyJWT) + bcrypt | — |
| Containerization | Docker + Docker Compose | — |

## Monorepo Structure
```
project-root/
├── backend/          ← FastAPI app + Celery worker
├── frontend/         ← React SPA
├── docker-compose.yml
├── .env.example
└── docs/             ← Architecture docs (HLD, LLD, schema)
```

## Key Domain Concepts (Use These Names Consistently)
- **Document** — a file uploaded by a user for grounding
- **ProcessingJob** — the async task that parses, chunks, and embeds a document
- **ChatSession** — a conversation thread tied to a user
- **ChatMessage** — a single user or assistant turn
- **Chunk** — a piece of text from a document stored in ChromaDB
- **Collection** — a ChromaDB collection, one per user (`user_{user_id}`)
- **RAG Pipeline** — the full flow: embed query → vector search → prompt build → LLM stream

## Document Status States
PENDING → PROCESSING → READY | FAILED
Never skip states. Always transition through this machine.

## Principle: Extensibility Over Cleverness
Every design decision must ask: "Will adding multi-doc support, doc deletion, or a new LLM provider require touching this code?" If yes, add an abstraction layer.
