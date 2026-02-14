"""
Vector Store Service
Qdrant embedded mode (no separate server needed)
"""
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue, SearchParams
)
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import uuid

from ..config import rag_config
from ..models import DocumentMetadata, RetrievedChunk

logger = logging.getLogger(__name__)


class VectorStore:
    """Qdrant vector store for document chunks"""
    
    def __init__(self):
        self.collection_name = rag_config.QDRANT_COLLECTION
        self.dimension = rag_config.EMBEDDING_DIMENSION
        self._client = None
    
    @property
    def client(self) -> QdrantClient:
        """Lazy load Qdrant client"""
        if self._client is None:
            # Create data directory if not exists
            Path(rag_config.QDRANT_PATH).mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Initializing Qdrant at {rag_config.QDRANT_PATH}")
            self._client = QdrantClient(path=rag_config.QDRANT_PATH)
            
            # Create collection if not exists
            self._ensure_collection()
        
        return self._client
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        collections = self.client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if self.collection_name not in collection_names:
            logger.info(f"Creating collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.dimension,
                    distance=Distance.COSINE
                )
            )
            logger.info("Collection created successfully")
    
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[DocumentMetadata]
    ) -> List[str]:
        """
        Add documents to vector store
        
        Args:
            texts: Document texts
            embeddings: Embedding vectors
            metadatas: Document metadata
            
        Returns:
            List of assigned point IDs
        """
        if not texts or not embeddings or not metadatas:
            raise ValueError("texts, embeddings, and metadatas must be non-empty")
        
        if not (len(texts) == len(embeddings) == len(metadatas)):
            raise ValueError("texts, embeddings, and metadatas must have same length")
        
        # Create points
        points = []
        point_ids = []
        
        for text, embedding, metadata in zip(texts, embeddings, metadatas):
            point_id = str(uuid.uuid4())
            point_ids.append(point_id)
            
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "text": text,
                        "document_id": metadata.document_id,
                        "filename": metadata.filename,
                        "chunk_index": metadata.chunk_index,
                        "total_chunks": metadata.total_chunks,
                        "page_number": metadata.page_number,
                        "uploaded_at": metadata.uploaded_at.isoformat()
                    }
                )
            )
        
        # Upsert to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        logger.info(f"Added {len(points)} points to vector store")
        return point_ids
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        score_threshold: Optional[float] = None,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedChunk]:
        """
        Search vector store for similar documents
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            filter_dict: Optional metadata filters
            
        Returns:
            List of retrieved chunks with scores
        """
        # Build filter if provided
        search_filter = None
        if filter_dict:
            conditions = []
            for key, value in filter_dict.items():
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            search_filter = Filter(must=conditions)
        
        # Search
        search_params = SearchParams(
            hnsw_ef=128,  # Quality vs speed tradeoff
            exact=False
        )
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=search_filter,
            search_params=search_params,
            score_threshold=score_threshold
        )
        
        # Convert to RetrievedChunk objects
        chunks = []
        for result in results:
            payload = result.payload
            
            metadata = DocumentMetadata(
                document_id=payload["document_id"],
                filename=payload["filename"],
                chunk_index=payload["chunk_index"],
                total_chunks=payload["total_chunks"],
                page_number=payload.get("page_number")
            )
            
            chunks.append(
                RetrievedChunk(
                    text=payload["text"],
                    metadata=metadata,
                    score=result.score
                )
            )
        
        logger.info(f"Retrieved {len(chunks)} chunks (top_k={top_k})")
        return chunks
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "total_points": collection_info.points_count,
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "status": collection_info.status
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def delete_document(self, document_id: str) -> int:
        """Delete all chunks of a document"""
        # Delete by document_id filter
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )
        logger.info(f"Deleted document: {document_id}")
        return 1  # TODO: Return actual count deleted


# Global singleton
_vector_store = None

def get_vector_store() -> VectorStore:
    """Get or create global vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
