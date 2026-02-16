"""
Vector Store Service - Qdrant Cloud
"""
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue, SearchParams,
    PayloadSchemaType, TextIndexParams,
)
from typing import List, Dict, Any, Optional
import logging
import uuid

from fastapi import HTTPException

from ..config import rag_config
from ..models import DocumentMetadata, RetrievedChunk
from app.middleware.rate_limit import get_global_rate_limiter
from app.middleware.quota_tracker import get_quota_tracker

logger = logging.getLogger(__name__)


class VectorStore:
    MAX_PAYLOAD_TEXT = 10000

    def __init__(self):
        self.collection_name = rag_config.QDRANT_COLLECTION
        self.dimension = rag_config.EMBEDDING_DIMENSION
        self._client = None

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            if not rag_config.QDRANT_URL or not rag_config.QDRANT_API_KEY:
                raise ValueError("QDRANT_URL and QDRANT_API_KEY must be configured")

            logger.info(f"Connecting to Qdrant Cloud: {rag_config.QDRANT_URL}")
            self._client = QdrantClient(
                url=rag_config.QDRANT_URL,
                api_key=rag_config.QDRANT_API_KEY,
            )
            self._ensure_collection()
            logger.info("Qdrant Cloud client initialized successfully")
        return self._client

    def _ensure_collection(self):
        collections = self._client.get_collections().collections
        names = [c.name for c in collections]
        if self.collection_name not in names:
            logger.info(f"Creating collection: {self.collection_name}")
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
            )

            # Create payload index for document_id (required for filtering)
            logger.info("Creating payload index for document_id")
            self._client.create_payload_index(
                collection_name=self.collection_name,
                field_name="document_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )

    def document_exists(self, document_id: str) -> bool:
        """Check if a document is already indexed."""
        result = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(must=[
                FieldCondition(key="document_id", match=MatchValue(value=document_id))
            ]),
            limit=1,
        )
        return len(result[0]) > 0

    def add_documents(
        self, texts: List[str], embeddings: List[List[float]], metadatas: List[DocumentMetadata]
    ) -> List[str]:
        if not texts or not embeddings or not metadatas:
            raise ValueError("texts, embeddings, and metadatas must be non-empty")
        if not (len(texts) == len(embeddings) == len(metadatas)):
            raise ValueError("texts, embeddings, and metadatas must have same length")

        # Rate limit check BEFORE writing to Qdrant
        limiter = get_global_rate_limiter()
        if not limiter.check_and_increment("qdrant_writes"):
            raise HTTPException(
                status_code=429,
                detail="Qdrant write rate limit exceeded. Try again in 1 hour."
            )

        points = []
        point_ids = []
        for text, embedding, metadata in zip(texts, embeddings, metadatas):
            pid = str(uuid.uuid4())
            point_ids.append(pid)
            safe_text = text[:self.MAX_PAYLOAD_TEXT]
            points.append(PointStruct(
                id=pid, vector=embedding,
                payload={
                    "text": safe_text,
                    "document_id": metadata.document_id,
                    "filename": metadata.filename,
                    "chunk_index": metadata.chunk_index,
                    "total_chunks": metadata.total_chunks,
                    "page_number": metadata.page_number,
                    "uploaded_at": metadata.uploaded_at.isoformat(),
                },
            ))
        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info(f"Added {len(points)} points to vector store")

        # Track usage
        tracker = get_quota_tracker()
        tracker.record_qdrant_documents(len(texts))

        return point_ids

    def search(
        self, query_embedding: List[float], top_k: int = 5,
        score_threshold: Optional[float] = None, filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedChunk]:
        search_filter = None
        if filter_dict:
            conditions = [FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filter_dict.items()]
            search_filter = Filter(must=conditions)

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=top_k,
            query_filter=search_filter,
            search_params=SearchParams(hnsw_ef=128, exact=False),
            score_threshold=score_threshold,
        )
        results = response.points
        chunks = []
        for r in results:
            p = r.payload
            meta = DocumentMetadata(
                document_id=p["document_id"], filename=p["filename"],
                chunk_index=p["chunk_index"], total_chunks=p["total_chunks"],
                page_number=p.get("page_number"),
            )
            chunks.append(RetrievedChunk(text=p["text"], metadata=meta, score=r.score))
        logger.info(f"Retrieved {len(chunks)} chunks (top_k={top_k})")
        return chunks

    def get_stats(self) -> Dict[str, Any]:
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "total_points": info.points_count,
                "vectors_count": info.vectors_count,
                "status": str(info.status),
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {}

    def delete_document(self, document_id: str) -> int:
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]),
        )
        logger.info(f"Deleted document: {document_id}")
        return 1


_vector_store = None

def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
