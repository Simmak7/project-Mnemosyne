"""
Core module - Shared infrastructure for the application.

This module contains foundational components used across all features:
- Configuration management
- Database connection and session handling
- Authentication and authorization
- Celery task queue setup
- Custom exception classes
- Logging configuration
- Error handlers

Import from submodules directly for specific needs:
    from core.config import SECRET_KEY
    from core.database import get_db
    from core.auth import get_current_user
"""

# Note: We don't import everything at the package level to avoid
# circular imports and allow selective importing from submodules.
# Import from specific submodules as needed:
#
#   from core import config
#   from core import database
#   from core import auth
#   from core import exceptions
#   from core.logging_config import setup_logging, get_logger
#   from core.error_handlers import register_exception_handlers
#   from core.celery_app import celery_app
