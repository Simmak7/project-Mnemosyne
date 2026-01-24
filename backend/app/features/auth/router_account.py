"""
Auth Feature - Account Management Router (Phase 2)

FastAPI endpoints for account management:
- GET/PUT /profile - Profile management
- GET/DELETE /sessions - Session management
- POST /email/change - Email change
- POST /account/delete - Account deletion
"""

import logging

from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_active_user
from core import exceptions

from features.auth import schemas
from features.auth import profile
from features.auth import sessions
from features.auth import email_change
from features.auth import account
from features.auth.models import User

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Account Management"])


# ============================================
# Profile Management Endpoints
# ============================================

@router.get("/profile", response_model=schemas.ProfileResponse)
async def get_profile_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile.

    Returns:
        User profile with all details
    """
    user = profile.get_profile(db, current_user)
    return user


@router.put("/profile", response_model=schemas.ProfileResponse)
async def update_profile_endpoint(
    data: schemas.ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.

    Args:
        data: Profile update data (display_name, avatar_url)

    Returns:
        Updated user profile
    """
    user, error = profile.update_profile(
        db=db,
        user=current_user,
        display_name=data.display_name,
        avatar_url=data.avatar_url
    )

    if error:
        raise exceptions.ValidationException(error)

    return user


# ============================================
# Session Management Endpoints
# ============================================

@router.get("/sessions", response_model=schemas.SessionListResponse)
async def get_sessions_endpoint(
    authorization: str = Header(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all active sessions for current user.

    Returns:
        List of active sessions with current session marked
    """
    current_token = None
    if authorization and authorization.startswith("Bearer "):
        current_token = authorization[7:]

    session_list = sessions.get_user_sessions(db, current_user, current_token)

    return {
        "sessions": session_list,
        "total": len(session_list)
    }


@router.delete("/sessions/{session_id}")
async def revoke_session_endpoint(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Revoke a specific session.

    Args:
        session_id: ID of the session to revoke

    Returns:
        Success message
    """
    success, error = sessions.revoke_session(db, current_user, session_id)

    if not success:
        raise exceptions.ValidationException(error)

    return {"message": "Session revoked successfully"}


@router.post("/sessions/revoke-all", response_model=schemas.SessionRevokeResponse)
async def revoke_all_sessions_endpoint(
    authorization: str = Header(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Revoke all sessions except the current one.

    Returns:
        Number of sessions revoked
    """
    current_token = None
    if authorization and authorization.startswith("Bearer "):
        current_token = authorization[7:]

    count = sessions.revoke_all_sessions(db, current_user, current_token)

    return {
        "message": f"Revoked {count} session(s)",
        "revoked_count": count
    }


# ============================================
# Email Change Endpoints
# ============================================

@router.post("/email/change")
@limiter.limit("3/hour")
async def request_email_change_endpoint(
    request: Request,
    data: schemas.EmailChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Request an email address change.

    Sends verification to the new email address.
    Rate limited to 3 requests per hour.

    Args:
        data: New email and current password

    Returns:
        Success message
    """
    success, message = email_change.request_email_change(
        db=db,
        user=current_user,
        new_email=data.new_email,
        password=data.password
    )

    if not success:
        raise exceptions.ValidationException(message)

    return {"message": message}


@router.post("/email/change/verify")
async def verify_email_change_endpoint(
    data: schemas.EmailChangeVerify,
    db: Session = Depends(get_db)
):
    """
    Verify email change with token.

    Args:
        data: Verification token

    Returns:
        Success message
    """
    success, old_email, error = email_change.verify_email_change(db, data.token)

    if not success:
        raise exceptions.ValidationException(error)

    return {"message": "Email address updated successfully"}


# ============================================
# Account Deletion Endpoints
# ============================================

@router.post("/account/delete", response_model=schemas.AccountDeleteResponse)
@limiter.limit("3/hour")
async def delete_account_endpoint(
    request: Request,
    data: schemas.AccountDeleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Request account deletion (soft delete).

    Account will be scheduled for permanent deletion after 30 days.
    Can be restored within the grace period.

    Args:
        data: Password and confirmation text

    Returns:
        Deletion schedule information
    """
    success, info, error = account.request_account_deletion(
        db=db,
        user=current_user,
        password=data.password
    )

    if not success:
        raise exceptions.ValidationException(error)

    return {
        "message": "Account scheduled for deletion",
        "deletion_scheduled_at": info["deletion_scheduled_at"],
        "can_restore_until": info["can_restore_until"]
    }


@router.post("/account/restore")
async def restore_account_endpoint(
    data: schemas.AccountRestoreRequest,
    db: Session = Depends(get_db)
):
    """
    Restore a soft-deleted account within grace period.

    Does not require authentication since account is deactivated.

    Args:
        data: Username and password

    Returns:
        Success message
    """
    success, error = account.restore_account(
        db=db,
        username=data.username,
        password=data.password
    )

    if not success:
        raise exceptions.ValidationException(error)

    return {"message": "Account restored successfully. You can now login."}


@router.get("/account/deletion-status", response_model=schemas.AccountDeletionStatus)
async def get_deletion_status_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get account deletion status.

    Returns:
        Deletion schedule and remaining days if scheduled
    """
    status = account.get_deletion_status(db, current_user)

    if not status:
        raise exceptions.NotFoundException("Account is not scheduled for deletion")

    return status


@router.post("/account/cancel-deletion")
async def cancel_deletion_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a scheduled account deletion.

    Returns:
        Success message
    """
    success, error = account.cancel_deletion(db, current_user)

    if not success:
        raise exceptions.ValidationException(error)

    return {"message": "Account deletion cancelled"}
