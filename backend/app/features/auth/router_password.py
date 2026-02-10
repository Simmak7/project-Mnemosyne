"""
Auth Feature - Password Management Endpoints

Change password, password reset flow, and requirements.
"""

import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_active_user
from core import exceptions
from core.password import get_password_strength, get_password_requirements

from features.auth import schemas
from features.auth import service
from features.auth import security
from features.auth import password_reset
from features.auth.models import User

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Authentication"])


@router.post("/change-password")
@limiter.limit("5/hour")
async def change_password(
    request: Request,
    password_data: schemas.PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change the current user's password. Rate limited to 5/hour."""
    logger.info(f"Password change attempt for user: {current_user.username}")

    success, error = await security.change_password(
        db=db,
        user=current_user,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )

    if not success:
        raise exceptions.ValidationException(error)

    return {"message": "Password changed successfully"}


@router.get("/password-requirements", response_model=schemas.PasswordRequirements)
async def get_password_requirements_endpoint():
    """Get the current password requirements."""
    return get_password_requirements()


@router.post("/check-password-strength", response_model=schemas.PasswordStrength)
async def check_password_strength(password_data: dict):
    """Check the strength of a password without storing it."""
    password = password_data.get("password", "")
    return get_password_strength(password)


@router.get("/account-lock-status", response_model=schemas.AccountLockStatus)
async def get_account_lock_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the current account lock status."""
    return security.get_account_lock_status(db, current_user)


@router.post("/forgot-password")
@limiter.limit("3/hour")
async def forgot_password(request: Request, data: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    """Request a password reset email. Rate limited to 3/hour."""
    logger.info(f"Password reset requested for email: {data.email}")
    success, message = await password_reset.request_password_reset(db, data.email)
    return {"message": message}


@router.get("/verify-reset-token/{token}")
async def verify_reset_token_endpoint(token: str, db: Session = Depends(get_db)):
    """Verify a password reset token is valid."""
    is_valid, user, error = password_reset.verify_reset_token(db, token)

    if not is_valid:
        return {"valid": False, "email": None, "error": error}

    return {"valid": True, "email": password_reset.get_masked_email(user.email), "error": None}


@router.post("/reset-password")
@limiter.limit("5/hour")
async def reset_password(request: Request, data: schemas.PasswordReset, db: Session = Depends(get_db)):
    """Complete password reset with token. Rate limited to 5/hour."""
    logger.info("Password reset attempt")

    success, error = await password_reset.complete_password_reset(
        db=db, token=data.token, new_password=data.new_password
    )

    if not success:
        raise exceptions.ValidationException(error)

    return {"message": "Password reset successfully. You can now login with your new password."}
