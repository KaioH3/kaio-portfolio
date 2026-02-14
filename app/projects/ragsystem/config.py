"""
RAG System Configuration
Centralized settings for embeddings, vector store, LLM APIs
"""
from pydantic_settings import BaseSettings
from typing import Literal
import os


class RAGConfig(BaseSettings):
    """RAG system configuration with multiple provider support"""
    
    # Embedding Model
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"  # 384 dims, fast
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BATCH_SIZE: int = 32
    
    # Vector Store (Qdrant)
    QDRANT_PATH: str = "./data/qdrant"  # Embedded mode (no server needed)
    QDRANT_COLLECTION: str = "documents"
    VECTOR_STORE_CACHE_SIZE: int = 10000
    
    # Document Processing
    CHUNK_SIZE: int = 512  # tokens per chunk
    CHUNK_OVERLAP: int = 50
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: set = {".pdf", ".txt", ".md"}
    
    # Retrieval
    TOP_K_RETRIEVAL: int = 10  # Initial retrieval
    TOP_K_RERANK: int = 5      # After reranking
    HYBRID_ALPHA: float = 0.7  # 0.7 semantic + 0.3 keyword
    MIN_SIMILARITY_SCORE: float = 0.5
    
    # LLM Generation
    LLM_PROVIDER: Literal["openai", "perplexity", "ollama"] = "perplexity"
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 1000
    
    # Perplexity (seu uso principal)
    PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "")
    PERPLEXITY_MODEL: str = "llama-3.1-sonar-small-128k-online"  # Barato e bom
    PERPLEXITY_MAX_TOKENS: int = 1000
    
    # Ollama (alternativa gratuita local)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"  # 2GB RAM, rápido
    OLLAMA_TIMEOUT: int = 60
    
    # Chain-of-Verification
    COVE_ENABLED: bool = True
    COVE_VERIFICATION_STEPS: int = 3
    COVE_CONFIDENCE_THRESHOLD: float = 0.7
    
    # Performance
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    ENABLE_CACHING: bool = True
    CACHE_TTL: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        case_sensitive = False


rag_config = RAGConfig()
