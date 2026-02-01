"""
Configuration management with Pydantic Settings
Environment-driven configuration for development/production
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # App metadata
    APP_NAME: str = "Kaio Portfolio - ML Engineer"
    ENV: str = "development"  # development | production
    BASE_URL: str = "http://localhost:8000"
    VERSION: str = "1.0.0"
    
    # Server config
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Security
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:8000",
        "https://kaio.ia.br",
        "https://www.kaio.ia.br"
    ]
    
    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG | INFO | WARNING | ERROR
    LOG_FORMAT: str = "json"  # json | text
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    
    # Projects (for future expansion)
    RAG_ENABLED: bool = False
    CREDIT_ENABLED: bool = False


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance (avoid repeated file reads)"""
    return Settings()


settings = get_settings()
