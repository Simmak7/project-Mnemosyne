"""
Auth Feature Module

Handles user authentication, registration, and authorization.

Phase 1: Core auth, password management, 2FA
Phase 2: Account management (profile, sessions, email change, deletion)
"""

from features.auth.router import router as auth_router
from features.auth.router_account import router as auth_account_router
from features.auth.models import User
from features.auth.schemas import (
    UserBase,
    UserCreate,
    UserResponse,
    Token,
    TokenData,
    UserLogin,
    # Phase 2 schemas
    ProfileResponse,
    ProfileUpdate,
    EmailChangeRequest,
    EmailChangeVerify,
    AccountDeleteRequest,
    AccountDeleteResponse,
    AccountRestoreRequest,
    AccountDeletionStatus,
    SessionInfo,
    SessionListResponse,
    SessionRevokeResponse,
)
from features.auth.service import (
    get_user,
    get_user_by_email,
    get_user_by_username,
    create_user,
    authenticate_user,
)

# Phase 2 modules
from features.auth import profile
from features.auth import sessions
from features.auth import email_change
from features.auth import account

__all__ = [
    # Routers
    "auth_router",
    "auth_account_router",
    # Models
    "User",
    # Schemas
    "UserBase",
    "UserCreate",
    "UserResponse",
    "Token",
    "TokenData",
    "UserLogin",
    # Phase 2 Schemas
    "ProfileResponse",
    "ProfileUpdate",
    "EmailChangeRequest",
    "EmailChangeVerify",
    "AccountDeleteRequest",
    "AccountDeleteResponse",
    "AccountRestoreRequest",
    "AccountDeletionStatus",
    "SessionInfo",
    "SessionListResponse",
    "SessionRevokeResponse",
    # Service
    "get_user",
    "get_user_by_email",
    "get_user_by_username",
    "create_user",
    "authenticate_user",
    # Phase 2 modules
    "profile",
    "sessions",
    "email_change",
    "account",
]
