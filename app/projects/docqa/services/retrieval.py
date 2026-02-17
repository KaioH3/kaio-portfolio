"""Retrieval Service - Hybrid search (semantic + BM25)"""
from typing import List, Dict, Any, Optional
import logging
from rank_bm25 import BM25Okapi

from ..config import rag_config
from ..models import RetrievedChunk
from .embeddings import get_embedding_service
from .vector_store import get_vector_store

logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(self):
        self.embeddings = get_embedding_service()
        self.vector_store = get_vector_store()
        self.top_k = rag_config.TOP_K_RETRIEVAL
        self.alpha = rag_config.HYBRID_ALPHA

    async def retrieve(
        self, query: str, top_k: Optional[int] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedChunk]:
        k = top_k or self.top_k
        query_embedding = self.embeddings.embed_query(query)
        # When filtering by a specific document, skip score_threshold so we
        # always return chunks from that document even for vague questions.
        threshold = None if filter_dict else rag_config.MIN_SIMILARITY_SCORE
        chunks = self.vector_store.search(
            query_embedding=query_embedding, top_k=k,
            score_threshold=threshold,
            filter_dict=filter_dict,
        )
        if len(chunks) > 1:
            chunks = self._rerank_bm25(query, chunks)
        return chunks[:rag_config.TOP_K_RERANK]

    def _rerank_bm25(self, query: str, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        tokenized = [c.text.lower().split() for c in chunks]
        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(query.lower().split())
        for i, chunk in enumerate(chunks):
            bm25_norm = scores[i] / (max(scores) + 1e-6)
            chunk.rerank_score = self.alpha * chunk.score + (1 - self.alpha) * bm25_norm
        chunks.sort(key=lambda c: c.rerank_score or 0, reverse=True)
        return chunks


_retrieval_service = None

def get_retrieval_service() -> RetrievalService:
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
