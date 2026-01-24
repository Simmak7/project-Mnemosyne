"""
DEPRECATED: This module is a backward compatibility shim.

All database functionality has moved to core.database.
Import from core.database directly in new code.
"""

# Re-export everything from core.database for backward compatibility
from core.database import (
    engine,
    SessionLocal,
    Base,
    get_db,
)

__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
]
