"""
DEPRECATED: This module is a backward compatibility shim.

Logging configuration has moved to core.logging_config.
Import from core.logging_config directly in new code.
"""

# Re-export everything from core.logging_config for backward compatibility
from core.logging_config import (
    setup_logging,
    get_logger,
)

__all__ = [
    "setup_logging",
    "get_logger",
]
