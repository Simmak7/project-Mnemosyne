"""
DEPRECATED: This module is a backward compatibility shim.

Celery app has moved to core.celery_app.
Import from core.celery_app directly in new code.
"""

# Re-export celery_app from core for backward compatibility
from core.celery_app import celery_app

__all__ = ["celery_app"]
