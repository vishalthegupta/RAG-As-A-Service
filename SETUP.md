# Setup Guide

Complete guide to set up the RAG-as-a-Service development environment.

## Prerequisites

### Required
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download](https://git-scm.com/downloads)

### Optional (for local development)
- **Node.js 20+** - For frontend development
- **PostgreSQL 15** - If running without Docker
- **Redis 7** - If running without Docker

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd RAG-As-A-Service
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your preferred editor
# Required changes:
# - JWT_SECRET_KEY: Generate with `openssl rand -hex 32`
# - GROQ_API_KEY: Get from https://console.groq.com
# - HUGGINGFACE_API_KEY: (Optional) Get from https://huggingface.co
```

### 3. Choose Your Setup Method

#### Option A: Docker Compose (Recommended)

**Pros:** Complete environment, no local dependencies, production-like
**Cons:** Slower startup, requires Docker

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f api

# Stop services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v
```

Access:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Flower (Celery monitoring): http://localhost:5555 (with `--profile monitoring`)

#### Option B: Local Development (Windows)

**Pros:** Fast iteration, easier debugging
**Cons:** Requires local Python setup

```bash
# Run the setup script
run_local.bat

# Or manually:
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python test_setup.py
uvicorn app.main:app --reload
```

#### Option C: Local Development (Linux/Mac)

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify setup
python test_setup.py

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Verify Installation

Run the environment verification:

```bash
cd backend
python test_setup.py
```

Expected output:
```
[1/5] Testing configuration... ✓
[2/5] Testing logging... ✓
[3/5] Testing custom exceptions... ✓
[4/5] Testing embedding service... ✓
[5/5] Testing ChromaDB client... ✓
[6/6] Testing FastAPI app... ✓
```

### 5. Verify RAG Skeleton

Run the end-to-end RAG verification:

```bash
cd backend
python verify_rag_skeleton.py
```

This will:
- Load the embedding model (~80MB download on first run)
- Test embedding generation
- Initialize ChromaDB
- Store and retrieve test vectors
- Simulate a complete RAG query flow

Expected output:
```
[1/6] Loading configuration... ✓
[2/6] Initializing embedding service... ✓
[3/6] Testing embedding generation... ✓
[4/6] Initializing ChromaDB... ✓
[5/6] Testing vector storage and retrieval... ✓
[6/6] Testing RAG pipeline components... ✓
```

## Troubleshooting

### Python Version Issues

```bash
# Check Python version
python --version  # Should be 3.11+

# If wrong version, use specific version
python3.11 -m venv venv
```

### Model Download Fails

The embedding model downloads automatically on first run. If it fails:

```bash
# Manually download
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder='./model_cache')"
```

### Docker Issues

```bash
# Check Docker is running
docker --version
docker compose version

# Reset everything
docker compose down -v
docker system prune -a

# Rebuild from scratch
docker compose build --no-cache
docker compose up -d
```

### Port Already in Use

If port 8000 is already in use:

```bash
# Find process using port 8000 (Windows)
netstat -ano | findstr :8000

# Kill process (Windows)
taskkill /PID <PID> /F

# Or change port in .env
# API_PORT=8001
```

### ChromaDB Errors

```bash
# Clear ChromaDB data
rm -rf chroma_data/  # Linux/Mac
rmdir /s /q chroma_data  # Windows

# Restart services
docker compose restart api worker
```

### Import Errors

```bash
# Ensure you're in the virtual environment
# You should see (venv) in your prompt

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

## Development Workflow

### Running Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_embedder.py -v

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v
```

### Code Quality

```bash
# Format code
black app/

# Lint code
ruff check app/

# Type check
mypy app/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Celery Worker

```bash
# Start worker locally
celery -A celery_app worker --loglevel=info

# Start with auto-reload (development)
watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A celery_app worker --loglevel=info
```

## Next Steps

Once setup is complete:

1. **Read the documentation**
   - [HLD.md](./HLD.md) - High-level architecture
   - [LLD.md](./LLD.md) - Low-level design
   - [README.md](./README.md) - Project overview

2. **Review steering rules**
   - `.kiro/steering/` - Development guidelines and standards

3. **Start feature development**
   - Follow the feature workflow in `.kiro/steering/feature_development_workflow.md`
   - Begin with Phase 1: Foundation (database models, migrations)

4. **Join the development**
   - Check `CHANGELOG.md` for current status
   - See open issues for tasks
   - Follow conventional commits

## Getting Help

- **Documentation**: See `HLD.md` and `LLD.md`
- **API Docs**: http://localhost:8000/docs (when running)
- **Issues**: Open a GitHub issue
- **Logs**: `docker compose logs -f api` or check console output

## Quick Reference

```bash
# Start everything
docker compose up -d

# View logs
docker compose logs -f api

# Run tests
cd backend && pytest

# Format code
cd backend && black app/

# Start local dev
cd backend && uvicorn app.main:app --reload

# Verify setup
cd backend && python test_setup.py

# Verify RAG
cd backend && python verify_rag_skeleton.py
```

---

**Ready to build!** 🚀
