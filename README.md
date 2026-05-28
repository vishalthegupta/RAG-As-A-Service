# RAG-as-a-Service

A production-ready, no-code RAG (Retrieval-Augmented Generation) platform that lets users upload documents and get a fully functional AI chatbot in minutes.

## 🎯 Overview

Upload your documents (PDF, DOCX, TXT) and chat with them using state-of-the-art AI. No ML knowledge required.

**Key Features:**
- 📄 Multi-format document support (PDF, DOCX, TXT)
- 🤖 Streaming AI responses via SSE
- 🔐 JWT-based authentication
- 📊 Real-time processing status
- 🎨 Modern React frontend
- 🐳 Fully containerized with Docker

## 🏗️ Architecture

```
Frontend (React) → FastAPI → PostgreSQL
                          → ChromaDB (Vector Store)
                          → Celery Workers → Redis
                          → LLM (Groq/HuggingFace)
```

See [HLD.md](./HLD.md) and [LLD.md](./LLD.md) for detailed architecture documentation.

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 20+ (for frontend development)

### 1. Clone and Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys:
# - JWT_SECRET_KEY (generate with: openssl rand -hex 32)
# - GROQ_API_KEY (get from https://console.groq.com)
# - HUGGINGFACE_API_KEY (optional, for fallback)
```

### 2. Start with Docker Compose

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f api
```

### 3. Access the Application

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000 (when implemented)
- **Flower (Celery monitoring)**: http://localhost:5555 (with `--profile monitoring`)

## 📦 Local Development Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy .env
cp ../.env.example ../.env

# Run test setup
python test_setup.py

# Start development server
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=app --cov-report=html
```

### Frontend (Coming Soon)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test
```

## 🧪 Testing the Setup

Run the environment verification script:

```bash
cd backend
python test_setup.py
```

This will verify:
- ✓ Configuration loading
- ✓ Logging setup
- ✓ Custom exceptions
- ✓ Embedding service (downloads model on first run)
- ✓ ChromaDB client
- ✓ FastAPI app

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

```
POST   /api/v1/auth/register      - Register new user
POST   /api/v1/auth/login         - Login and get JWT
GET    /api/v1/auth/me            - Get current user

POST   /api/v1/documents          - Upload document
GET    /api/v1/documents          - List user's documents
GET    /api/v1/documents/{id}     - Get document details
DELETE /api/v1/documents/{id}     - Delete document

POST   /api/v1/chat/sessions      - Create chat session
POST   /api/v1/chat/sessions/{id}/messages  - Send message (SSE stream)
GET    /api/v1/chat/sessions/{id}/messages  - Get chat history
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python 3.11 |
| Database | PostgreSQL 15 |
| Vector Store | ChromaDB |
| Task Queue | Celery + Redis |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| LLM | Groq API (primary), HuggingFace (fallback) |
| Frontend | React 18 + Vite + Tailwind CSS |
| Container | Docker + Docker Compose |

## 📁 Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── auth/           # Authentication module
│   │   ├── documents/      # Document management
│   │   ├── chat/           # Chat & RAG pipeline
│   │   ├── processing/     # Celery workers & processing
│   │   ├── vector_store/   # ChromaDB operations
│   │   ├── llm/            # LLM provider abstraction
│   │   ├── main.py         # FastAPI app
│   │   └── config.py       # Configuration
│   ├── tests/              # Test suite
│   ├── alembic/            # Database migrations
│   └── requirements.txt
├── frontend/               # React application
├── docker-compose.yml      # Production compose
├── docker-compose.override.yml  # Dev overrides
├── .env.example            # Environment template
├── HLD.md                  # High-level design
└── LLD.md                  # Low-level design
```

## 🔧 Configuration

All configuration is via environment variables in `.env`:

```bash
# Security
JWT_SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ragdb

# LLM
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key

# RAG Settings
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.8
CHUNK_SIZE=512
CHUNK_OVERLAP=64
```

See `.env.example` for all available options.

## 🧩 Development Workflow

This project follows a strict feature-by-feature development workflow:

1. **Implement** the feature
2. **Write tests** for it
3. **Run tests** until all pass
4. **Confirm** and summarize
5. **Move** to next feature

See [.kiro/steering/feature_development_workflow.md](.kiro/steering/feature_development_workflow.md) for details.

## 🐛 Troubleshooting

### Model Download Issues

The embedding model (~80MB) downloads on first run. If it fails:

```bash
# Manually download
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker compose ps db

# View database logs
docker compose logs db

# Reset database
docker compose down -v
docker compose up -d
```

### ChromaDB Issues

```bash
# Clear ChromaDB data
rm -rf chroma_data/

# Restart services
docker compose restart api worker
```

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Follow the coding standards in `.kiro/steering/`
2. Write tests for all new features
3. Ensure all tests pass before committing
4. Use conventional commits: `feat:`, `fix:`, `docs:`, etc.

## 📞 Support

- Documentation: See `HLD.md` and `LLD.md`
- Issues: Open a GitHub issue
- API Docs: http://localhost:8000/docs

---

Built with ❤️ using FastAPI, ChromaDB, and modern AI technologies.
