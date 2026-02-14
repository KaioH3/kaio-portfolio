"""
Retrieval Service
Hybrid search (semantic + keyword) with reranking
"""
from typing import List
from rank_bm25 import BM25Okapi
import numpy as np
import logging

from ..config import rag_config
from ..models import RetrievedChunk
from .embeddings import get_embedding_service
from .vector_store import get_vector_store

logger = logging.getLogger(__name__)


class RetrievalService:
    """Hybrid retrieval with semantic + keyword search"""
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()
        self.alpha = rag_config.HYBRID_ALPHA  # Weight for semantic vs keyword
    
    def retrieve(
        self,
        query: str,
        top_k: int = None
    ) -> List[RetrievedChunk]:
        """
        Hybrid retrieval: semantic search + keyword matching + reranking
        
        Args:
            query: User query
            top_k: Number of final results (default: config.TOP_K_RERANK)
            
        Returns:
            List of retrieved and reranked chunks
        """
        if top_k is None:
            top_k = rag_config.TOP_K_RERANK
        
        # Step 1: Semantic search (retrieve more for reranking)
        initial_k = rag_config.TOP_K_RETRIEVAL
        query_embedding = self.embedding_service.embed_query(query)
        
        semantic_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=initial_k,
            score_threshold=rag_config.MIN_SIMILARITY_SCORE
        )
        
        if not semantic_results:
            logger.warning("No results found with semantic search")
            return []
        
        # Step 2: Keyword matching (BM25) on retrieved results
        bm25_scores = self._compute_bm25_scores(query, semantic_results)
        
        # Step 3: Hybrid scoring (combine semantic + BM25)
        hybrid_results = self._combine_scores(
            semantic_results,
            bm25_scores,
            alpha=self.alpha
        )
        
        # Step 4: Reranking by hybrid score
        reranked = sorted(
            hybrid_results,
            key=lambda x: x.rerank_score,
            reverse=True
        )[:top_k]
        
        logger.info(f"Retrieved {len(reranked)} chunks after reranking")
        return reranked
    
    def _compute_bm25_scores(
        self,
        query: str,
        chunks: List[RetrievedChunk]
    ) -> List[float]:
        """
        Compute BM25 keyword scores
        
        Args:
            query: User query
            chunks: Retrieved chunks
            
        Returns:
            List of BM25 scores (normalized 0-1)
        """
        # Tokenize documents
        corpus = [chunk.text.lower().split() for chunk in chunks]
        
        # Build BM25 index
        bm25 = BM25Okapi(corpus)
        
        # Score query
        query_tokens = query.lower().split()
        scores = bm25.get_scores(query_tokens)
        
        # Normalize to 0-1
        max_score = max(scores) if max(scores) > 0 else 1.0
        normalized = [score / max_score for score in scores]
        
        return normalized
    
    def _combine_scores(
        self,
        chunks: List[RetrievedChunk],
        bm25_scores: List[float],
        alpha: float
    ) -> List[RetrievedChunk]:
        """
        Combine semantic and keyword scores
        
        Args:
            chunks: Retrieved chunks with semantic scores
            bm25_scores: BM25 keyword scores
            alpha: Weight for semantic (1-alpha for keyword)
            
        Returns:
            Chunks with combined rerank_score
        """
        for chunk, bm25_score in zip(chunks, bm25_scores):
            # Hybrid score: alpha * semantic + (1-alpha) * keyword
            chunk.rerank_score = (
                alpha * chunk.score +
                (1 - alpha) * bm25_score
            )
        
        return chunks


# Global singleton
_retrieval_service = None

def get_retrieval_service() -> RetrievalService:
    """Get or create global retrieval service instance"""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
