"""ChromaDB client singleton"""
from __future__ import annotations

from typing import Optional
import chromadb
from chromadb import ClientAPI, Collection
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

_client: Optional[ClientAPI] = None


def get_chroma_client() -> ClientAPI:
    """Get or create ChromaDB client singleton"""
    global _client
    if _client is None:
        logger.info("chromadb.client.initializing", path=settings.CHROMA_PERSIST_DIRECTORY)
        _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
        logger.info("chromadb.client.initialized")
    return _client


def get_or_create_collection(user_id: str) -> Collection:
    """
    Get or create a ChromaDB collection for a user
    
    Args:
        user_id: User UUID as string
        
    Returns:
        ChromaDB Collection instance
    """
    client = get_chroma_client()
    collection_name = f"user_{user_id.replace('-', '_')}"
    
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}  # Use cosine similarity
    )
    
    logger.info("chromadb.collection.ready", collection=collection_name)
    return collection
