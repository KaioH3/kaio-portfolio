"""
Embeddings Service
Local sentence-transformers embeddings (no API costs)
"""
from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
import logging
from functools import lru_cache

from ..config import rag_config

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate embeddings using local sentence-transformers model"""
    
    def __init__(self):
        self.model_name = rag_config.EMBEDDING_MODEL
        self.dimension = rag_config.EMBEDDING_DIMENSION
        self.batch_size = rag_config.EMBEDDING_BATCH_SIZE
        self._model = None
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load embedding model"""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Model loaded successfully. Dimension: {self.dimension}")
        return self._model
    
    def embed_documents(self, texts: List[str]) -> List[np.ndarray]:
        """
        Embed multiple documents in batches
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        try:
            # Generate embeddings in batches
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=len(texts) > 100,
                convert_to_numpy=True,
                normalize_embeddings=True  # L2 normalization for cosine similarity
            )
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a single query (optimized for search)
        
        Args:
            query: Query string
            
        Returns:
            Embedding vector
        """
        try:
            embedding = self.model.encode(
                query,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error embedding query: {str(e)}")
            raise
    
    @lru_cache(maxsize=1000)
    def embed_query_cached(self, query: str) -> tuple:
        """Cached version of embed_query for repeated queries"""
        embedding = self.embed_query(query)
        return tuple(embedding)  # Convert to tuple for hashability
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1)
        """
        # Assuming embeddings are already normalized
        similarity = np.dot(embedding1, embedding2)
        return float(similarity)


# Global singleton instance
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """Get or create global embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
