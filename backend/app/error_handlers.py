"""
DEPRECATED: This module is a backward compatibility shim.

Error handlers have moved to core.error_handlers.
Import from core.error_handlers directly in new code.
"""

# Re-export everything from core.error_handlers for backward compatibility
from core.error_handlers import (
    app_exception_handler,
    validation_exception_handler,
    database_exception_handler,
    generic_exception_handler,
    register_exception_handlers,
)

__all__ = [
    "app_exception_handler",
    "validation_exception_handler",
    "database_exception_handler",
    "generic_exception_handler",
    "register_exception_handlers",
]
