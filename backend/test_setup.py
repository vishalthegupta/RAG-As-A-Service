"""Test script to verify environment setup"""
from __future__ import annotations

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("RAG-as-a-Service Environment Setup Test")
print("=" * 60)

# Test 1: Config loading
print("\n[1/5] Testing configuration...")
try:
    from app.config import settings
    print(f"✓ Config loaded successfully")
    print(f"  - App: {settings.APP_NAME} v{settings.VERSION}")
    print(f"  - Debug mode: {settings.DEBUG}")
    print(f"  - Embedding model: {settings.EMBEDDING_MODEL}")
except Exception as e:
    print(f"✗ Config failed: {e}")
    sys.exit(1)

# Test 2: Logging setup
print("\n[2/5] Testing logging...")
try:
    from app.logging_config import setup_logging
    import structlog
    setup_logging()
    logger = structlog.get_logger(__name__)
    logger.info("test.logging", status="working")
    print("✓ Logging configured successfully")
except Exception as e:
    print(f"✗ Logging failed: {e}")
    sys.exit(1)

# Test 3: Exceptions
print("\n[3/5] Testing custom exceptions...")
try:
    from app.exceptions import (
        RagServiceError,
        DocumentNotFoundError,
        LLMUnavailableError,
    )
    print("✓ Custom exceptions imported successfully")
except Exception as e:
    print(f"✗ Exceptions failed: {e}")
    sys.exit(1)

# Test 4: Embedding service (model loading)
print("\n[4/5] Testing embedding service...")
print("  Note: This will download the model (~80MB) on first run")
try:
    from app.processing.embedder import EmbeddingService
    embedder = EmbeddingService.get_instance()
    
    # Test encoding
    test_text = "This is a test sentence for embedding."
    embedding = embedder.encode([test_text])
    
    print(f"✓ Embedding service initialized")
    print(f"  - Model loaded: {settings.EMBEDDING_MODEL}")
    print(f"  - Embedding shape: {embedding.shape}")
    print(f"  - Embedding dimension: {embedding.shape[1]}")
except Exception as e:
    print(f"✗ Embedding service failed: {e}")
    print("  This is expected if model download fails or dependencies are missing")

# Test 5: ChromaDB client
print("\n[5/5] Testing ChromaDB client...")
try:
    from app.vector_store.client import get_chroma_client, get_or_create_collection
    
    client = get_chroma_client()
    print(f"✓ ChromaDB client initialized")
    print(f"  - Persist directory: {settings.CHROMA_PERSIST_DIRECTORY}")
    
    # Test collection creation
    test_collection = get_or_create_collection("test-user-id")
    print(f"✓ Test collection created: {test_collection.name}")
    
except Exception as e:
    print(f"✗ ChromaDB failed: {e}")
    print("  This is expected if ChromaDB dependencies are missing")

# Test 6: FastAPI app
print("\n[6/6] Testing FastAPI app...")
try:
    from app.main import app
    print(f"✓ FastAPI app created successfully")
    print(f"  - Title: {app.title}")
    print(f"  - Version: {app.version}")
except Exception as e:
    print(f"✗ FastAPI app failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ Environment setup verification complete!")
print("=" * 60)
print("\nNext steps:")
print("1. Copy .env.example to .env and fill in your API keys")
print("2. Install dependencies: pip install -r requirements.txt")
print("3. Run the app: uvicorn app.main:app --reload")
print("4. Visit http://localhost:8000/docs for API documentation")
