"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api import citations, conversations, health, search
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.database import init_db
from app.services.elasticsearch_service import get_elasticsearch_service
from app.services.redis_service import get_redis_service

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger.info("Starting MedSearch AI Backend...")

    try:
        # Initialize SQLite database
        init_db()
        logger.info("SQLite database initialized")

        # Initialize Elasticsearch
        es_service = await get_elasticsearch_service()
        logger.info("Elasticsearch service initialized")

        # Initialize Redis
        redis_service = await get_redis_service()
        logger.info("Redis service initialized")

        logger.info("All services initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    yield

    logger.info("Shutting down MedSearch AI Backend...")

    try:
        # Cleanup Elasticsearch
        if 'es_service' in locals():
            await es_service.disconnect()

        # Cleanup Redis
        if 'redis_service' in locals():
            await redis_service.disconnect()

        logger.info("All services shut down successfully")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title="MedSearch AI API",
    description="Multi-agent medical research assistant API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(citations.router, prefix="/api/v1", tags=["Citations"])
app.include_router(conversations.router, prefix="/api/v1", tags=["Conversations"])


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "MedSearch AI API",
        "version": "1.0.0",
        "docs": "/docs",
    }

