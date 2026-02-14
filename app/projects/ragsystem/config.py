"""
RAG System Configuration
Lightweight: FastEmbed (CPU) + Groq FREE API
"""
import os
from pydantic_settings import BaseSettings
from typing import Literal


class RAGConfig(BaseSettings):
    # === Embedding: FastEmbed (CPU, no torch, ~220MB) ===
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BATCH_SIZE: int = 32

    # === Vector Store: Qdrant embedded ===
    QDRANT_PATH: str = "./data/qdrant"
    QDRANT_COLLECTION: str = "documents"

    # === Document Processing ===
    CHUNK_SIZE: int = 400
    CHUNK_OVERLAP: int = 50
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: set = {".pdf", ".txt", ".md"}

    # === Retrieval ===
    TOP_K_RETRIEVAL: int = 5
    TOP_K_RERANK: int = 3
    HYBRID_ALPHA: float = 0.7
    MIN_SIMILARITY_SCORE: float = 0.3

    # === LLM Provider ===
    LLM_PROVIDER: Literal["groq", "openai", "perplexity"] = "groq"

    # === Groq FREE TIER (primary) ===
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_MAX_TOKENS: int = 1000

    # === OpenAI (backup) ===
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 1000

    # === Perplexity (backup) ===
    PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "")
    PERPLEXITY_MODEL: str = "llama-3.1-sonar-small-128k-online"
    PERPLEXITY_MAX_TOKENS: int = 1000

    # === Rate Limiting ===
    RATE_LIMIT_MONTHLY: int = 15

    # === General ===
    REQUEST_TIMEOUT: float = 60.0
    MAX_RETRIES: int = 3
    COVE_ENABLED: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


rag_config = RAGConfig()
