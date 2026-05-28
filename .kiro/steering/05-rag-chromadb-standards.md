# RAG Pipeline & ChromaDB Standards

## ChromaDB Collection Design
- One collection per user: `f"user_{user_id}"` (replace hyphens: `user_id.replace("-", "_")`)
- Collection is created automatically on first document upload — never pre-create
- Each stored chunk has this exact structure:
```python
{
    "id": f"{doc_id}_chunk_{chunk_index}",
    "embedding": list[float],           # 384-dim from all-MiniLM-L6-v2
    "document": chunk_text,             # raw chunk text
    "metadata": {
        "doc_id": str(doc_id),
        "doc_name": document.name,
        "chunk_index": chunk_index,
        "user_id": str(user_id),
        "char_start": int,
        "char_end": int,
        "created_at": iso_timestamp_str
    }
}
```
**Never deviate from this metadata schema** — filters, deletions, and source attribution all depend on it.

## ChromaDB Client (Singleton)
```python
# vector_store/client.py
import chromadb

_client: chromadb.ClientAPI | None = None

def get_chroma_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
    return _client

def get_or_create_collection(user_id: str) -> chromadb.Collection:
    client = get_chroma_client()
    collection_name = f"user_{user_id.replace('-', '_')}"
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}   # cosine similarity, always
    )
```
- Always use `cosine` distance — embeddings are normalized, dot product = cosine
- Always use `get_or_create_collection` — never `create_collection` (would fail on restart)

## Chunking Rules
- Default chunk size: **512 characters** (not tokens — simpler, consistent)
- Overlap: **64 characters**
- Split hierarchy: `"\n\n"` → `"\n"` → `". "` → `" "` → `""`
- Minimum chunk size: **100 characters** — merge smaller fragments with next chunk
- Maximum chunk size: **600 characters** — hard cap, split at word boundary
- Always preserve `char_start` and `char_end` in metadata for source highlighting

## Embedding Service Rules
- Model loaded once at app startup — singleton pattern, cached in memory
- Model path: `sentence-transformers/all-MiniLM-L6-v2`
- Cache directory: `./model_cache` (volume-mounted in Docker)
- Always call `normalize_embeddings=True` — enables cosine via dot product
- Batch size for bulk encoding: **32** (safe for CPU and low-memory envs)
- Single query encoding: pass as `[query_text]`, take `[0]` from result

```python
# WRONG — encode returns array, not single vector
embedding = embedding_service.encode(query_text)

# RIGHT
embedding = embedding_service.encode([query_text])[0].tolist()
```

## RAG Query Rules
- Default top_k: **5 chunks**
- Similarity threshold: **0.8** (ChromaDB cosine distance — lower = more similar)
- Filter retrieved chunks: `distance < settings.RAG_SIMILARITY_THRESHOLD`
- If zero chunks pass threshold: respond "I don't have information about that in your documents"
- Never hallucinate — if context is empty or irrelevant, say so
- Deduplicate: if 2+ chunks from same doc_id, keep only the highest-scoring one
- Chat history in prompt: last **6 messages** max (3 turns) — beyond that is noise

## Prompt Template (Exact Format)
```python
SYSTEM_PROMPT = """You are a helpful assistant that answers questions strictly based on the provided context documents.

Rules:
- Only answer from the context below. If the answer isn't there, say: "I don't have enough information in the provided documents to answer that."
- Be concise and direct.
- When referencing information, you may mention which document it comes from.
- Do not make up facts or use outside knowledge."""

def build_rag_prompt(context_chunks: list[dict], chat_history: list[dict], user_query: str) -> list[dict]:
    context_text = "\n\n---\n\n".join([
        f"[Source: {c['metadata']['doc_name']}]\n{c['document']}"
        for c in context_chunks
    ])
    
    messages = []
    # Add history (already formatted as role/content dicts)
    messages.extend(chat_history[-6:])
    # Add current query with context
    messages.append({
        "role": "user",
        "content": f"Context:\n{context_text}\n\nQuestion: {user_query}"
    })
    return messages
```

## Document Deletion (ChromaDB side)
```python
# When a document is deleted, remove all its chunks:
def delete_document_chunks(user_id: str, doc_id: str) -> None:
    collection = get_or_create_collection(user_id)
    collection.delete(where={"doc_id": str(doc_id)})
```
This is why `doc_id` in metadata is mandatory — it enables selective deletion without nuking the whole collection.

## ChromaDB Backup
- `CHROMA_PERSIST_DIRECTORY` must be a Docker volume — never ephemeral container storage
- Treat it like a database — include in backup strategy
