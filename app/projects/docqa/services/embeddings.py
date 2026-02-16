"""
Embeddings Service - Voyage AI API
Zero local RAM usage, production-grade embeddings
"""
from typing import List
import logging
from functools import lru_cache

import voyageai
from fastapi import HTTPException

from ..config import rag_config
from app.middleware.rate_limit import get_global_rate_limiter
from app.middleware.quota_tracker import get_quota_tracker

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate embeddings using Voyage AI API (zero local ML overhead)"""

    def __init__(self):
        if not rag_config.VOYAGE_API_KEY:
            raise ValueError("VOYAGE_API_KEY not configured in environment")

        self.client = voyageai.Client(api_key=rag_config.VOYAGE_API_KEY)
        self.model = rag_config.VOYAGE_MODEL
        self.dimension = rag_config.EMBEDDING_DIMENSION
        logger.info(f"Voyage AI client initialized. Model: {self.model}, Dim: {self.dimension}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents via Voyage AI API"""
        if not texts:
            return []

        # Rate limit check BEFORE calling Voyage AI
        limiter = get_global_rate_limiter()
        if not limiter.check_and_increment("voyage_embeddings"):
            raise HTTPException(
                status_code=429,
                detail="Voyage AI rate limit exceeded. Try again in 1 hour."
            )

        try:
            # Voyage AI batches automatically, no need for manual chunking
            result = self.client.embed(texts, model=self.model, input_type="document")
            logger.info(f"Generated {len(result.embeddings)} embeddings via Voyage AI")

            # Track usage
            tracker = get_quota_tracker()
            estimated_tokens = sum(len(text.split()) * 1.3 for text in texts)
            tracker.record_voyage_usage(int(estimated_tokens))

            return result.embeddings
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Voyage AI embedding error: {e}")
            raise

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query via Voyage AI API"""
        try:
            result = self.client.embed([query], model=self.model, input_type="query")
            return result.embeddings[0]
        except Exception as e:
            logger.error(f"Voyage AI query embedding error: {e}")
            raise

    @lru_cache(maxsize=1000)
    def embed_query_cached(self, query: str) -> tuple:
        """Cached version for repeated queries"""
        return tuple(self.embed_query(query))

    def compute_similarity(self, e1: List[float], e2: List[float]) -> float:
        """Cosine similarity between two embeddings"""
        import numpy as np
        v1, v2 = np.array(e1), np.array(e2)
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Singleton factory for embedding service"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
