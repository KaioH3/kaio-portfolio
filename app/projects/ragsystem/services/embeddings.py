"""
Embeddings Service - FastEmbed
CPU-only, no torch, ~50MB RAM, ONNX Runtime
"""
from typing import List
import numpy as np
import logging
from functools import lru_cache

from fastembed import TextEmbedding
from ..config import rag_config

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate embeddings using FastEmbed (lightweight, CPU-first)"""

    def __init__(self):
        self.model_name = rag_config.EMBEDDING_MODEL
        self.dimension = rag_config.EMBEDDING_DIMENSION
        self.batch_size = rag_config.EMBEDDING_BATCH_SIZE
        self._model = None

    @property
    def model(self) -> TextEmbedding:
        """Lazy load FastEmbed model"""
        if self._model is None:
            logger.info(f"Loading FastEmbed model: {self.model_name}")
            self._model = TextEmbedding(model_name=self.model_name)
            logger.info(f"FastEmbed loaded (~50MB RAM). Dim: {self.dimension}")
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents"""
        if not texts:
            return []
        try:
            embeddings = list(self.model.embed(texts, batch_size=self.batch_size))
            logger.info(f"Generated {len(embeddings)} embeddings")
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query"""
        try:
            embeddings = list(self.model.embed([query]))
            return embeddings[0].tolist()
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise

    @lru_cache(maxsize=1000)
    def embed_query_cached(self, query: str) -> tuple:
        """Cached version for repeated queries"""
        return tuple(self.embed_query(query))

    def compute_similarity(self, e1: List[float], e2: List[float]) -> float:
        """Cosine similarity between two embeddings"""
        v1, v2 = np.array(e1), np.array(e2)
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
