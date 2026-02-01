"""
FastAPI Application Entry Point
Production-ready configuration with monitoring, CORS, and static files
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.routers import home, health

# Initialize logging
logger = setup_logging()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Portfolio profissional de Machine Learning Engineer",
    version=settings.VERSION,
    docs_url="/docs" if settings.ENV == "development" else None,
    redoc_url="/redoc" if settings.ENV == "development" else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(home.router, tags=["Home"])
app.include_router(health.router, prefix="/api", tags=["Health"])

# Prometheus metrics (only in production)
if settings.PROMETHEUS_ENABLED:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Base URL: {settings.BASE_URL}")
    if settings.ENV == "development":
        logger.info(f"Docs: {settings.BASE_URL}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("⏹️  Shutting down application")
