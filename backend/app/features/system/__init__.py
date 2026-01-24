"""
System Feature Module

Handles system-level endpoints: health checks, status, and root endpoint.
This feature has no models or database dependencies - it's purely operational.
"""

from features.system.router import router as system_router
from features.system.service import (
    check_ollama_health,
    check_database_health,
    check_upload_directory,
    get_system_status,
)

__all__ = [
    # Router
    "system_router",
    # Service
    "check_ollama_health",
    "check_database_health",
    "check_upload_directory",
    "get_system_status",
]
