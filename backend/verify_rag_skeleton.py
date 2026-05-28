"""End-to-end verification of RAG skeleton setup"""
from __future__ import annotations

import sys
import os
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("RAG SKELETON VERIFICATION")
print("=" * 70)

# Step 1: Load configuration
print("\n[1/6] Loading configuration...")
try:
    from app.config import settings
    print(f"✓ Configuration loaded")
    print(f"  - Embedding model: {settings.EMBEDDING_MODEL}")
    print(f"  - Chunk size: {settings.CHUNK_SIZE}")
    print(f"  - Chunk overlap: {settings.CHUNK_OVERLAP}")
    print(f"  - RAG top-k: {settings.RAG_TOP_K}")
    print(f"  - Similarity threshold: {settings.RAG_SIMILARITY_THRESHOLD}")
except Exception as e:
    print(f"✗ Configuration failed: {e}")
    sys.exit(1)

# Step 2: Initialize embedding service
print("\n[2/6] Initializing embedding service...")
print("  (This will download ~80MB model on first run)")
try:
    from app.processing.embedder import EmbeddingService
    embedder = EmbeddingService.get_instance()
    print(f"✓ Embedding service ready")
except Exception as e:
    print(f"✗ Embedding service failed: {e}")
    sys.exit(1)

# Step 3: Test embedding generation
print("\n[3/6] Testing embedding generation...")
try:
    test_texts = [
        "Machine learning is a subset of artificial intelligence.",
        "Python is a popular programming language for data science.",
        "FastAPI is a modern web framework for building APIs."
    ]
    
    embeddings = embedder.encode(test_texts)
    print(f"✓ Generated embeddings")
    print(f"  - Input texts: {len(test_texts)}")
    print(f"  - Embedding shape: {embeddings.shape}")
    print(f"  - Embedding dimension: {embeddings.shape[1]}")
    
    # Verify normalization (for cosine similarity)
    norms = np.linalg.norm(embeddings, axis=1)
    print(f"  - Embeddings normalized: {np.allclose(norms, 1.0)}")
    
except Exception as e:
    print(f"✗ Embedding generation failed: {e}")
    sys.exit(1)

# Step 4: Initialize ChromaDB
print("\n[4/6] Initializing ChromaDB...")
try:
    from app.vector_store.client import get_chroma_client, get_or_create_collection
    
    client = get_chroma_client()
    print(f"✓ ChromaDB client initialized")
    print(f"  - Persist directory: {settings.CHROMA_PERSIST_DIRECTORY}")
    
    # Create test collection
    test_user_id = "test-user-12345"
    collection = get_or_create_collection(test_user_id)
    print(f"✓ Test collection created: {collection.name}")
    
except Exception as e:
    print(f"✗ ChromaDB initialization failed: {e}")
    sys.exit(1)

# Step 5: Test vector storage and retrieval
print("\n[5/6] Testing vector storage and retrieval...")
try:
    # Store test documents
    doc_id = "test-doc-001"
    chunks = [
        "FastAPI is a modern, fast web framework for building APIs with Python 3.7+.",
        "It is based on standard Python type hints and provides automatic API documentation.",
        "FastAPI has excellent performance, comparable to NodeJS and Go."
    ]
    
    # Generate embeddings
    chunk_embeddings = embedder.encode(chunks)
    
    # Store in ChromaDB
    collection.add(
        ids=[f"{doc_id}_chunk_{i}" for i in range(len(chunks))],
        embeddings=chunk_embeddings.tolist(),
        documents=chunks,
        metadatas=[
            {
                "doc_id": doc_id,
                "doc_name": "FastAPI Guide",
                "chunk_index": i,
                "user_id": test_user_id
            }
            for i in range(len(chunks))
        ]
    )
    print(f"✓ Stored {len(chunks)} chunks in ChromaDB")
    
    # Test retrieval
    query = "What is FastAPI?"
    query_embedding = embedder.encode([query])[0].tolist()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=2,
        include=["documents", "metadatas", "distances"]
    )
    
    print(f"✓ Retrieved {len(results['documents'][0])} relevant chunks")
    print(f"\n  Query: '{query}'")
    print(f"  Top result: '{results['documents'][0][0][:80]}...'")
    print(f"  Distance: {results['distances'][0][0]:.4f}")
    
    # Verify similarity threshold
    if results['distances'][0][0] < settings.RAG_SIMILARITY_THRESHOLD:
        print(f"  ✓ Result passes similarity threshold ({settings.RAG_SIMILARITY_THRESHOLD})")
    else:
        print(f"  ⚠ Result below similarity threshold")
    
except Exception as e:
    print(f"✗ Vector storage/retrieval failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 6: Test RAG pipeline components
print("\n[6/6] Testing RAG pipeline components...")
try:
    # Simulate RAG query flow
    user_query = "How fast is FastAPI?"
    
    # 1. Embed query
    query_emb = embedder.encode([user_query])[0].tolist()
    print(f"✓ Query embedded")
    
    # 2. Retrieve context
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=settings.RAG_TOP_K,
        include=["documents", "metadatas", "distances"]
    )
    
    # 3. Filter by similarity threshold
    relevant_chunks = [
        {
            "text": doc,
            "metadata": meta,
            "distance": dist
        }
        for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )
        if dist < settings.RAG_SIMILARITY_THRESHOLD
    ]
    
    print(f"✓ Retrieved {len(relevant_chunks)} relevant chunks")
    
    # 4. Build context
    if relevant_chunks:
        context = "\n\n---\n\n".join([
            f"[Source: {chunk['metadata']['doc_name']}]\n{chunk['text']}"
            for chunk in relevant_chunks
        ])
        print(f"✓ Context assembled ({len(context)} chars)")
        
        # 5. Simulate prompt building
        system_prompt = "You are a helpful assistant. Answer based on the context."
        user_prompt = f"Context:\n{context}\n\nQuestion: {user_query}"
        
        print(f"✓ Prompt built")
        print(f"\n  System: {system_prompt[:60]}...")
        print(f"  Context length: {len(context)} chars")
        print(f"  Query: {user_query}")
    else:
        print(f"⚠ No relevant chunks found (would respond: 'I don't have information')")
    
except Exception as e:
    print(f"✗ RAG pipeline test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Cleanup
print("\n[Cleanup] Removing test collection...")
try:
    client.delete_collection(collection.name)
    print(f"✓ Test collection removed")
except Exception as e:
    print(f"⚠ Cleanup warning: {e}")

print("\n" + "=" * 70)
print("✓ RAG SKELETON VERIFICATION COMPLETE!")
print("=" * 70)
print("\nAll core components are working:")
print("  ✓ Configuration management")
print("  ✓ Embedding generation (sentence-transformers)")
print("  ✓ Vector storage (ChromaDB)")
print("  ✓ Similarity search")
print("  ✓ RAG pipeline flow")
print("\nNext steps:")
print("  1. Implement database models and migrations")
print("  2. Build authentication system")
print("  3. Create document upload and processing")
print("  4. Implement LLM integration")
print("  5. Build chat endpoints with SSE streaming")
print("\nReady for feature development! 🚀")
