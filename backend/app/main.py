"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Elastic APM (optional)
try:
    from elasticapm.contrib.starlette import make_apm_client, ElasticAPM  # type: ignore
    import elasticapm  # type: ignore
except Exception:  # pragma: no cover
    make_apm_client = None  # type: ignore
    ElasticAPM = None  # type: ignore
    elasticapm = None  # type: ignore

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

        # Initialize Elasticsearch (non-blocking in dev)
        try:
            es_service = await get_elasticsearch_service()
            logger.info("Elasticsearch service initialized")
        except Exception as e:
            if settings.APP_ENV.lower() == "production":
                raise
            logger.warning(f"Elasticsearch not available (dev mode): {e}")

        # Initialize Redis (non-blocking in dev)
        try:
            redis_service = await get_redis_service()
            logger.info("Redis service initialized")
        except Exception as e:
            if settings.APP_ENV.lower() == "production":
                raise
            logger.warning(f"Redis not available (dev mode): {e}")

        logger.info("All services initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize critical services: {e}")
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

# Elastic APM middleware (if configured)
try:
    if settings.APM_ENABLED and make_apm_client and ElasticAPM:
        apm_config = {
            "SERVICE_NAME": settings.APM_SERVICE_NAME,
            "SERVER_URL": settings.APM_SERVER_URL,
            "SECRET_TOKEN": settings.APM_SECRET_TOKEN,
            "ENVIRONMENT": settings.APM_ENVIRONMENT,
            "TRANSACTION_SAMPLE_RATE": settings.APM_TRANSACTION_SAMPLE_RATE,
            "CAPTURE_BODY": settings.APM_CAPTURE_BODY,
        }
        if apm_config["SERVER_URL"]:
            apm_client = make_apm_client(apm_config)  # type: ignore
            if elasticapm:
                elasticapm.instrument()  # type: ignore
            app.add_middleware(ElasticAPM, client=apm_client)  # type: ignore
            logger.info("Elastic APM enabled with sample rate %.2f", settings.APM_TRANSACTION_SAMPLE_RATE)
        else:
            logger.info("Elastic APM configured but SERVER_URL is empty; skipping agent init")
except Exception as e:  # pragma: no cover
    logger.error("Elastic APM initialization failed: %s", e)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(search.router, tags=["Search"])  # Remove prefix for WebSocket to work
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

