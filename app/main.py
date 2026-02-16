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
from app.routers import home, health, admin
from app.projects.docqa import routes as docqa_routes
from app.projects.creditrisk import routes as creditrisk_routes
from app.projects.landing import routes as landing_routes
from app.middleware.security import setup_security_middleware

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

# Security middleware (OWASP Top 10 protection)
setup_security_middleware(
    app,
    environment=settings.ENV,
    allowed_hosts=["localhost", "127.0.0.1", "kaio.ia.br", "*.kaio.ia.br"]
)

# CORS middleware (after security, before business logic)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# GZip compression (last middleware for performance)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(home.router, tags=["Home"])
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(admin.router, tags=["Admin"])
app.include_router(docqa_routes.router, tags=["Doc QA"])
app.include_router(creditrisk_routes.router, tags=["Credit Risk"])
app.include_router(landing_routes.router, tags=["Landing Page"])

# Prometheus metrics (only in production)
if settings.PROMETHEUS_ENABLED:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info(f" Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Base URL: {settings.BASE_URL}")
    if settings.ENV == "development":
        logger.info(f"Docs: {settings.BASE_URL}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("Shutting down application")
