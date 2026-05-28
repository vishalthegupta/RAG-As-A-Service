"""Embedding service using sentence-transformers (singleton pattern)"""
from __future__ import annotations

from typing import Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import structlog

from app.config import settings
from app.exceptions import EmbeddingError

logger = structlog.get_logger(__name__)


class EmbeddingService:
    """Singleton service for generating embeddings"""
    
    _instance: Optional[EmbeddingService] = None
    _model: Optional[SentenceTransformer] = None

    def __init__(self):
        """Private constructor - use get_instance() instead"""
        if EmbeddingService._instance is not None:
            raise RuntimeError("Use EmbeddingService.get_instance() instead")

    @classmethod
    def get_instance(cls) -> EmbeddingService:
        """Get or create the singleton instance"""
        if cls._instance is None:
            logger.info("embedding.model.loading", model=settings.EMBEDDING_MODEL)
            cls._instance = cls.__new__(cls)
            try:
                cls._instance._model = SentenceTransformer(
                    settings.EMBEDDING_MODEL,
                    cache_folder="./model_cache"
                )
                logger.info("embedding.model.loaded", model=settings.EMBEDDING_MODEL)
            except Exception as e:
                logger.error("embedding.model.load.failed", error=str(e))
                raise EmbeddingError(f"Failed to load embedding model: {e}")
        return cls._instance

    def encode(
        self,
        texts: Union[str, list[str]],
        batch_size: int | None = None,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Encode text(s) into embeddings
        
        Args:
            texts: Single text or list of texts
            batch_size: Batch size for encoding (default from settings)
            show_progress: Show progress bar
            
        Returns:
            numpy array of embeddings (shape: [n_texts, embedding_dim])
        """
        if self._model is None:
            raise EmbeddingError("Model not loaded")
        
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return np.array([])
        
        batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
        
        try:
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=True  # Enable cosine similarity via dot product
            )
            return embeddings
        except Exception as e:
            logger.error("embedding.encode.failed", error=str(e), text_count=len(texts))
            raise EmbeddingError(f"Failed to encode texts: {e}")
