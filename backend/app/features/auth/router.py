"""
Auth Feature - API Router

FastAPI endpoints for authentication, password management, and 2FA.
Combines sub-routers: auth, password, 2fa.
"""

from fastapi import APIRouter

# Import sub-routers
from features.auth.router_auth import router as auth_router
from features.auth.router_password import router as password_router
from features.auth.router_2fa import router as tfa_router


def get_auth_router() -> APIRouter:
    """Get the combined auth router with all endpoints."""
    combined = APIRouter()

    # Include all sub-routers (they share the "Authentication" tag)
    combined.include_router(auth_router)
    combined.include_router(password_router)
    combined.include_router(tfa_router)

    return combined


# Default export for backward compatibility
router = get_auth_router()
