"""
Health check and metrics endpoints
"""
from fastapi import APIRouter
from datetime import datetime
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    Used by Podman healthcheck and load balancers
    """
    return {
        "status": "healthy",
        "environment": settings.ENV,
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness probe - checks if app can serve traffic
    """
    # Add checks here (database, external services)
    return {
        "status": "ready",
        "services": {
            "api": "operational"
        }
    }
