"""Health check endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter

from app.core.config import settings
from app.models.schemas import HealthResponse, ServiceStatus
from app.services.elasticsearch_service import get_elasticsearch_service
from app.services.redis_service import get_redis_service
from app.services.vertex_ai_service import get_vertex_ai_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Comprehensive health check endpoint.

    Returns status of all services and overall system health.
    """
    services = {}
    overall_status = "healthy"
    is_prod = settings.APP_ENV.lower() == "production"

    # Check Elasticsearch
    try:
        es_service = await get_elasticsearch_service()
        es_health = await es_service.health_check()

        services["elasticsearch"] = ServiceStatus(
            status=es_health.get("status", "down"),
            message=es_health.get("message"),
        )

        if es_health.get("status") != "up" and is_prod:
            overall_status = "degraded"

    except Exception as e:
        logger.error(f"Elasticsearch health check failed: {e}")
        services["elasticsearch"] = ServiceStatus(status="down", message=str(e))
        if is_prod:
            overall_status = "unhealthy"

    # Check Redis
    try:
        redis_service = await get_redis_service()
        redis_health = await redis_service.health_check()

        services["redis"] = ServiceStatus(
            status=redis_health.get("status", "down"),
            message=redis_health.get("message"),
        )

        if redis_health.get("status") != "up" and is_prod:
            overall_status = "degraded"

    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        services["redis"] = ServiceStatus(status="down", message=str(e))
        if is_prod:
            overall_status = "degraded"  # Redis is not critical

    # Check Vertex AI
    try:
        vertex_ai_service = get_vertex_ai_service()
        vertex_health = await vertex_ai_service.health_check()

        services["vertex_ai"] = ServiceStatus(
            status=vertex_health.get("status", "down"),
            message=vertex_health.get("message"),
        )

        if vertex_health.get("status") != "up" and is_prod:
            overall_status = "degraded"

    except Exception as e:
        logger.error(f"Vertex AI health check failed: {e}")
        services["vertex_ai"] = ServiceStatus(status="down", message=str(e))
        if is_prod:
            overall_status = "unhealthy"

    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        environment=settings.APP_ENV,
        services=services,
        timestamp=datetime.now(),
    )

