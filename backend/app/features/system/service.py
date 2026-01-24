"""
System Feature - Business Logic / Service Layer

Health check functions and system status utilities.
"""

import os
import logging
import requests
from typing import Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from core import config
from core.database import SessionLocal

logger = logging.getLogger(__name__)


def check_ollama_health() -> Tuple[str, str]:
    """
    Check Ollama AI service health.

    Returns:
        Tuple of (status, log_level) where status is one of:
        - 'connected': Service is healthy
        - 'disconnected': Service is not responding
        - 'timeout': Service timed out
    """
    try:
        response = requests.get(
            f"{config.OLLAMA_HOST}/api/tags",
            timeout=2
        )
        if response.status_code == 200:
            logger.debug("Ollama service health check: OK")
            return "connected", "debug"
        else:
            logger.warning(f"Ollama service returned status {response.status_code}")
            return "disconnected", "warning"
    except requests.exceptions.Timeout:
        logger.warning("Ollama service health check timeout")
        return "timeout", "warning"
    except Exception as e:
        logger.error(f"Ollama health check failed: {str(e)}")
        return "disconnected", "error"


def check_database_health(db: Session = None) -> Tuple[str, str]:
    """
    Check database connectivity.

    Args:
        db: Optional database session. If not provided, creates a new one.

    Returns:
        Tuple of (status, log_level) where status is one of:
        - 'connected': Database is healthy
        - 'disconnected': Database is not responding
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        db.execute(text("SELECT 1"))
        logger.debug("Database health check: OK")
        return "connected", "debug"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}", exc_info=True)
        return "disconnected", "error"
    finally:
        if close_db:
            db.close()


def check_upload_directory() -> Tuple[str, str]:
    """
    Check if upload directory exists and is accessible.

    Returns:
        Tuple of (status, log_level) where status is one of:
        - 'ok': Directory exists and is writable
        - 'missing': Directory does not exist
    """
    if os.path.exists(config.UPLOAD_DIR):
        # Also check if it's writable
        if os.access(config.UPLOAD_DIR, os.W_OK):
            return "ok", "debug"
        else:
            logger.warning(f"Upload directory exists but is not writable: {config.UPLOAD_DIR}")
            return "read_only", "warning"
    else:
        logger.error("Upload directory is missing!")
        return "missing", "error"


def check_redis_health() -> Tuple[str, str]:
    """
    Check Redis connectivity (used by Celery).

    Returns:
        Tuple of (status, log_level)
    """
    try:
        import redis
        r = redis.Redis.from_url(config.REDIS_URL)
        r.ping()
        logger.debug("Redis health check: OK")
        return "connected", "debug"
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return "disconnected", "error"


def get_system_status() -> Dict[str, any]:
    """
    Get comprehensive system status.

    Returns:
        Dictionary with overall status and component statuses.
    """
    status = "healthy"
    components = {}

    # Check Ollama
    ollama_status, _ = check_ollama_health()
    components["ollama"] = ollama_status
    if ollama_status != "connected":
        status = "degraded"

    # Check database
    db_status, _ = check_database_health()
    components["database"] = db_status
    if db_status != "connected":
        status = "unhealthy"

    # Check upload directory
    upload_status, _ = check_upload_directory()
    components["upload_dir"] = upload_status
    if upload_status == "missing":
        status = "unhealthy"
    elif upload_status == "read_only":
        status = "degraded" if status == "healthy" else status

    # Check Redis (optional, don't fail if unavailable)
    try:
        redis_status, _ = check_redis_health()
        components["redis"] = redis_status
        if redis_status != "connected" and status == "healthy":
            status = "degraded"
    except ImportError:
        components["redis"] = "not_configured"

    return {
        "status": status,
        "components": components
    }
