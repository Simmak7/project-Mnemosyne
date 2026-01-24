"""
DEPRECATED: This module is a backward compatibility shim.

All auth functionality has moved to core.auth.
Import from core.auth directly in new code.
"""

# Re-export everything from core.auth for backward compatibility
from core.auth import (
    pwd_context,
    oauth2_scheme,
    oauth2_scheme_optional,
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    get_db,
    get_current_user,
    get_current_active_user,
    get_current_user_optional,
)

__all__ = [
    "pwd_context",
    "oauth2_scheme",
    "oauth2_scheme_optional",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "verify_token",
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "get_current_user_optional",
]
