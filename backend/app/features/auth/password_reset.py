"""
Auth Feature - Password Reset Service

Handles password reset token generation, validation, and email sending.
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from core import config
from core.auth import get_password_hash
from core.password import validate_password
from core.email import email_service
import models

logger = logging.getLogger(__name__)


def generate_reset_token() -> str:
    """Generate a secure random token for password reset."""
    return secrets.token_urlsafe(32)


async def request_password_reset(db: Session, email: str) -> Tuple[bool, str]:
    """
    Request a password reset for an email address.

    Args:
        db: Database session
        email: Email address to send reset link to

    Returns:
        Tuple of (success, message)
    """
    # Find user by email
    user = db.query(models.User).filter(models.User.email == email).first()

    # Always return success message to prevent email enumeration
    success_message = "If an account exists with this email, a reset link has been sent."

    if not user:
        logger.info(f"Password reset requested for non-existent email: {email}")
        return True, success_message

    if not user.is_active:
        logger.info(f"Password reset requested for inactive user: {user.username}")
        return True, success_message

    # Invalidate any existing tokens for this user
    db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == user.id,
        models.PasswordResetToken.used == False
    ).update({"used": True})

    # Generate new token
    token = generate_reset_token()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=config.PASSWORD_RESET_EXPIRE_MINUTES
    )

    # Store token
    reset_token = models.PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    db.add(reset_token)
    db.commit()

    # Send email
    email_sent = await email_service.send_password_reset_email(
        to=user.email,
        username=user.username,
        reset_token=token
    )

    if not email_sent:
        logger.error(f"Failed to send password reset email to {email}")
        # Still return success to prevent enumeration
        # In production, you might want to queue a retry

    logger.info(f"Password reset token generated for user: {user.username}")
    return True, success_message


def verify_reset_token(db: Session, token: str) -> Tuple[bool, Optional[models.User], Optional[str]]:
    """
    Verify a password reset token.

    Args:
        db: Database session
        token: Reset token to verify

    Returns:
        Tuple of (is_valid, user, error_message)
    """
    reset_token = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == token
    ).first()

    if not reset_token:
        return False, None, "Invalid or expired reset token"

    if reset_token.used:
        return False, None, "This reset token has already been used"

    if reset_token.expires_at <= datetime.now(timezone.utc):
        return False, None, "This reset token has expired"

    user = db.query(models.User).filter(
        models.User.id == reset_token.user_id
    ).first()

    if not user:
        return False, None, "User not found"

    if not user.is_active:
        return False, None, "Account is not active"

    return True, user, None


def complete_password_reset(
    db: Session,
    token: str,
    new_password: str
) -> Tuple[bool, Optional[str]]:
    """
    Complete the password reset process.

    Args:
        db: Database session
        token: Reset token
        new_password: New password to set

    Returns:
        Tuple of (success, error_message)
    """
    # Verify token
    is_valid, user, error = verify_reset_token(db, token)
    if not is_valid:
        return False, error

    # Validate new password
    is_valid_password, errors = validate_password(new_password)
    if not is_valid_password:
        return False, "; ".join(errors)

    # Update password
    user.hashed_password = get_password_hash(new_password)
    user.password_changed_at = datetime.now(timezone.utc)

    # Reset any lockout
    user.is_locked = False
    user.locked_until = None
    user.failed_login_attempts = 0

    # Mark token as used
    reset_token = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == token
    ).first()
    reset_token.used = True

    db.commit()

    logger.info(f"Password reset completed for user: {user.username}")

    # Send security alert email (async, don't wait)
    # This would be better as a Celery task in production

    return True, None


def get_masked_email(email: str) -> str:
    """
    Mask an email address for display.

    Args:
        email: Full email address

    Returns:
        Masked email (e.g., j***@gmail.com)
    """
    if "@" not in email:
        return "***"

    local, domain = email.rsplit("@", 1)

    if len(local) <= 2:
        masked_local = local[0] + "*" * (len(local) - 1)
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]

    return f"{masked_local}@{domain}"


def cleanup_expired_tokens(db: Session) -> int:
    """
    Remove expired password reset tokens.

    Args:
        db: Database session

    Returns:
        Number of tokens deleted
    """
    result = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.expires_at < datetime.now(timezone.utc)
    ).delete()
    db.commit()
    return result
