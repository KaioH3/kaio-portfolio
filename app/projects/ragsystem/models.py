"""
Pydantic models for RAG system API
Request/Response validation and serialization
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    """Response after document upload"""
    document_id: str
    filename: str
    size_bytes: int
    chunks_created: int
    status: DocumentStatus
    processing_time_ms: float
    message: str


class DocumentMetadata(BaseModel):
    """Metadata stored with each chunk"""
    document_id: str
    filename: str
    chunk_index: int
    total_chunks: int
    page_number: Optional[int] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class RetrievedChunk(BaseModel):
    """Retrieved document chunk with score"""
    text: str
    metadata: DocumentMetadata
    score: float
    rerank_score: Optional[float] = None


class VerificationStep(BaseModel):
    """Single step in Chain-of-Verification"""
    step: str
    passed: bool
    confidence: float
    details: str


class QueryRequest(BaseModel):
    """RAG query request"""
    question: str = Field(..., min_length=3, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    enable_verification: bool = Field(default=True)
    
    @validator('question')
    def question_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Question cannot be empty')
        return v.strip()


class QueryResponse(BaseModel):
    """RAG query response with CoVe"""
    answer: str
    sources: List[RetrievedChunk]
    verification_steps: List[VerificationStep]
    confidence_score: float = Field(ge=0.0, le=1.0)
    processing_time_ms: float
    tokens_used: Dict[str, int]  # prompt, completion, total
    metadata: Dict[str, Any] = {}


class HealthCheck(BaseModel):
    """RAG system health status"""
    status: str
    embedding_model_loaded: bool
    vector_store_connected: bool
    llm_provider: str
    llm_available: bool
    total_documents: int
    total_chunks: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Standardized error response"""
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
