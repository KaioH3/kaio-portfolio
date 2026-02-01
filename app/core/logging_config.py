"""
Structured logging configuration
JSON format for production, human-readable for development
"""
import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configure application logging"""
    
    # Create logger
    logger = logging.getLogger("kaio_portfolio")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Create formatter
    if settings.LOG_FORMAT == "json":
        formatter = logging.Formatter(
            '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s"}'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance for specific module"""
    return logging.getLogger(f"kaio_portfolio.{name}")
