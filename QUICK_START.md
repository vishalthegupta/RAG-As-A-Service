# Quick Start Guide

## Starting the Backend Server

### Option 1: Using the Start Script (Recommended)

```powershell
# Navigate to backend folder
cd backend

# Run the start script
.\start_server.bat
```

### Option 2: Manual Start

```powershell
# Navigate to backend folder
cd backend

# Activate virtual environment
.\venv\Scripts\activate

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Direct Python Command

```powershell
# From the backend folder
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Accessing the API

Once the server is running, you can access:

- **API Root**: http://localhost:8000
- **Interactive API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## First Time Setup

If you haven't installed dependencies yet:

```powershell
cd backend

# Create virtual environment (if not exists)
python -m venv venv

# Activate it
.\venv\Scripts\activate

# Install minimal dependencies (faster)
pip install -r requirements-minimal.txt

# Or install all dependencies (takes longer)
pip install -r requirements.txt
```

## Troubleshooting

### "uvicorn is not recognized"

Make sure you've activated the virtual environment:
```powershell
.\venv\Scripts\activate
```

### Port 8000 already in use

Change the port:
```powershell
uvicorn app.main:app --reload --port 8001
```

### Dependencies not installed

Install them:
```powershell
.\venv\Scripts\activate
pip install -r requirements-minimal.txt
```

## Testing the Setup

### 1. Check if server is running

Open your browser and go to: http://localhost:8000

You should see:
```json
{
  "app": "RAG-as-a-Service",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### 2. Check API documentation

Go to: http://localhost:8000/docs

You should see the interactive Swagger UI.

### 3. Test health endpoint

Go to: http://localhost:8000/health

You should see:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## Next Steps

1. **Configure environment**: Edit `.env` file with your API keys
2. **Test embedding service**: Run `python test_setup.py`
3. **Test RAG pipeline**: Run `python verify_rag_skeleton.py`
4. **Start development**: Begin implementing database models

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.
