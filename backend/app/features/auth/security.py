"""
Auth Feature - Security Service

Handles account lockout, login tracking, and password management.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_

from core import config
from core.auth import verify_password, get_password_hash
from core.password import validate_password_with_breach_check
import models

logger = logging.getLogger(__name__)


# ============================================
# Account Lockout Functions
# ============================================

def check_account_lockout(db: Session, user: models.User) -> Tuple[bool, Optional[datetime]]:
    """
    Check if a user account is locked.

    Args:
        db: Database session
        user: User object

    Returns:
        Tuple of (is_locked, locked_until)
    """
    if not user.is_locked:
        return False, None

    if user.locked_until and user.locked_until <= datetime.now(timezone.utc):
        # Lock has expired, unlock the account
        user.is_locked = False
        user.locked_until = None
        user.failed_login_attempts = 0
        db.commit()
        return False, None

    return True, user.locked_until


def record_login_attempt(
    db: Session,
    user: Optional[models.User],
    username: str,
    ip_address: Optional[str],
    user_agent: Optional[str],
    success: bool,
    failure_reason: Optional[str] = None
) -> models.LoginAttempt:
    """
    Record a login attempt.

    Args:
        db: Database session
        user: User object (if found)
        username: Attempted username
        ip_address: Client IP address
        user_agent: Client user agent
        success: Whether login was successful
        failure_reason: Reason for failure (if applicable)

    Returns:
        Created LoginAttempt record
    """
    attempt = models.LoginAttempt(
        user_id=user.id if user else None,
        username=username,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        failure_reason=failure_reason
    )
    db.add(attempt)
    db.commit()
    return attempt


def handle_failed_login(db: Session, user: models.User) -> Tuple[bool, Optional[datetime]]:
    """
    Handle a failed login attempt - increment counter and potentially lock account.

    Args:
        db: Database session
        user: User object

    Returns:
        Tuple of (is_now_locked, locked_until)
    """
    user.failed_login_attempts += 1

    if user.failed_login_attempts >= config.MAX_LOGIN_ATTEMPTS:
        # Lock the account
        user.is_locked = True
        user.locked_until = datetime.now(timezone.utc) + timedelta(
            minutes=config.LOCKOUT_DURATION_MINUTES
        )
        db.commit()
        logger.warning(
            f"Account locked for user {user.username} after "
            f"{user.failed_login_attempts} failed attempts"
        )
        return True, user.locked_until

    db.commit()
    return False, None


def handle_successful_login(db: Session, user: models.User) -> None:
    """
    Handle a successful login - reset counters and update last_login.

    Args:
        db: Database session
        user: User object
    """
    user.failed_login_attempts = 0
    user.is_locked = False
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)
    db.commit()


def get_recent_failed_attempts(
    db: Session,
    user: models.User,
    minutes: int = None
) -> int:
    """
    Get count of recent failed login attempts for a user.

    Args:
        db: Database session
        user: User object
        minutes: Time window (defaults to config.ATTEMPT_WINDOW_MINUTES)

    Returns:
        Count of failed attempts in the window
    """
    if minutes is None:
        minutes = config.ATTEMPT_WINDOW_MINUTES

    window_start = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    return db.query(models.LoginAttempt).filter(
        and_(
            models.LoginAttempt.user_id == user.id,
            models.LoginAttempt.success == False,
            models.LoginAttempt.created_at >= window_start
        )
    ).count()


# ============================================
# Password Change Functions
# ============================================

async def change_password(
    db: Session,
    user: models.User,
    current_password: str,
    new_password: str
) -> Tuple[bool, Optional[str]]:
    """
    Change a user's password.

    Args:
        db: Database session
        user: User object (may be from a different session)
        current_password: Current password for verification
        new_password: New password to set

    Returns:
        Tuple of (success, error_message)
    """
    # Verify current password
    if not verify_password(current_password, user.hashed_password):
        return False, "Current password is incorrect"

    # Check if new password is same as current
    if verify_password(new_password, user.hashed_password):
        return False, "New password must be different from current password"

    # Validate new password meets requirements including breach check
    is_valid, errors = await validate_password_with_breach_check(new_password)
    if not is_valid:
        return False, "; ".join(errors)

    # Re-fetch user in this session to ensure changes are tracked
    # (The passed user object may be from a different session)
    db_user = db.query(models.User).filter(models.User.id == user.id).first()
    if not db_user:
        return False, "User not found"

    # Update password
    db_user.hashed_password = get_password_hash(new_password)
    db_user.password_changed_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(f"Password changed successfully for user {db_user.username}")
    return True, None


# ============================================
# Account Status Functions
# ============================================

def get_account_lock_status(db: Session, user: models.User) -> dict:
    """
    Get the current lock status of an account.

    Args:
        db: Database session
        user: User object

    Returns:
        Dictionary with lock status details
    """
    is_locked, locked_until = check_account_lockout(db, user)

    return {
        "is_locked": is_locked,
        "locked_until": locked_until,
        "failed_attempts": user.failed_login_attempts,
        "max_attempts": config.MAX_LOGIN_ATTEMPTS
    }


def unlock_account(db: Session, user: models.User) -> bool:
    """
    Manually unlock a user account (admin function).

    Args:
        db: Database session
        user: User object

    Returns:
        True if account was unlocked
    """
    user.is_locked = False
    user.locked_until = None
    user.failed_login_attempts = 0
    db.commit()
    logger.info(f"Account manually unlocked for user {user.username}")
    return True
