"""
System Feature - API Router

FastAPI endpoints for system operations:
- GET / - Root endpoint (API info)
- GET /health - Health check for all services
"""

import logging
from fastapi import APIRouter

from core import config
from features.system import service
from features.system import schemas

logger = logging.getLogger(__name__)

router = APIRouter(tags=["System"])


@router.get("/", response_model=schemas.RootResponse)
async def read_root():
    """
    Root endpoint - API information.

    Returns basic API information including version and status.
    No authentication required.
    """
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to AI Notes Notetaker Backend!",
        "version": config.API_VERSION,
        "status": "running"
    }


@router.get("/health", response_model=schemas.HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Checks the health of all system components:
    - Ollama AI service
    - PostgreSQL database
    - Upload directory
    - Redis (Celery backend)

    Returns:
        - status: 'healthy', 'degraded', or 'unhealthy'
        - components: Dictionary of component statuses

    Status definitions:
        - healthy: All critical components operational
        - degraded: Non-critical components unavailable (e.g., Ollama)
        - unhealthy: Critical components unavailable (e.g., database)

    No authentication required - used for container health checks.
    """
    system_status = service.get_system_status()

    logger.info(f"Health check: {system_status['status']}")
    return system_status
