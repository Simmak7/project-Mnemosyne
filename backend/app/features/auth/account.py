"""
Auth Feature - Account Management Service (Phase 2)

Handles account deletion with soft delete and restoration.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from core.auth import verify_password
import models

logger = logging.getLogger(__name__)

# Grace period for account restoration (30 days)
ACCOUNT_DELETION_GRACE_DAYS = 30


def request_account_deletion(
    db: Session,
    user: models.User,
    password: str
) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    Request account deletion (soft delete with grace period).

    Args:
        db: Database session
        user: User object
        password: Current password for verification

    Returns:
        Tuple of (success, deletion_info, error_message)
    """
    # Re-fetch user in this session
    db_user = db.query(models.User).filter(models.User.id == user.id).first()
    if not db_user:
        return False, None, "User not found"

    # Check if already scheduled for deletion
    if db_user.deleted_at is not None:
        return False, None, "Account is already scheduled for deletion"

    # Verify password
    if not verify_password(password, db_user.hashed_password):
        return False, None, "Incorrect password"

    # Set deletion timestamps
    now = datetime.now(timezone.utc)
    scheduled_deletion = now + timedelta(days=ACCOUNT_DELETION_GRACE_DAYS)

    db_user.deleted_at = now
    db_user.scheduled_deletion_at = scheduled_deletion
    db_user.is_active = False

    # Revoke all sessions
    db.query(models.UserSession).filter(
        models.UserSession.user_id == db_user.id
    ).update({"is_revoked": True})

    db.commit()

    # Send confirmation email
    try:
        from core.email import send_account_deletion_confirmation
        send_account_deletion_confirmation(
            to_email=db_user.email,
            username=db_user.username,
            deletion_date=scheduled_deletion
        )
    except ImportError:
        logger.warning("Email service not configured")
    except Exception as e:
        logger.error(f"Failed to send deletion confirmation email: {e}")

    logger.info(f"Account deletion scheduled for user {db_user.username} on {scheduled_deletion}")

    return True, {
        "deletion_scheduled_at": now,
        "can_restore_until": scheduled_deletion
    }, None


def restore_account(
    db: Session,
    username: str,
    password: str
) -> Tuple[bool, Optional[str]]:
    """
    Restore a soft-deleted account within the grace period.

    Args:
        db: Database session
        username: Username of account to restore
        password: Password for verification

    Returns:
        Tuple of (success, error_message)
    """
    user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if not user:
        return False, "Account not found"

    if user.deleted_at is None:
        return False, "Account is not scheduled for deletion"

    if user.scheduled_deletion_at and user.scheduled_deletion_at < datetime.now(timezone.utc):
        return False, "Grace period has expired, account cannot be restored"

    # Verify password
    if not verify_password(password, user.hashed_password):
        return False, "Incorrect password"

    # Restore account
    user.deleted_at = None
    user.scheduled_deletion_at = None
    user.is_active = True

    db.commit()

    logger.info(f"Account restored for user {user.username}")
    return True, None


def get_deletion_status(
    db: Session,
    user: models.User
) -> Optional[dict]:
    """
    Get account deletion status.

    Args:
        db: Database session
        user: User object

    Returns:
        Deletion status info or None if not scheduled
    """
    db_user = db.query(models.User).filter(models.User.id == user.id).first()

    if not db_user or db_user.deleted_at is None:
        return None

    now = datetime.now(timezone.utc)
    days_remaining = 0

    if db_user.scheduled_deletion_at:
        delta = db_user.scheduled_deletion_at - now
        days_remaining = max(0, delta.days)

    return {
        "scheduled_at": db_user.deleted_at,
        "permanent_deletion_at": db_user.scheduled_deletion_at,
        "days_remaining": days_remaining,
        "can_restore": days_remaining > 0
    }


def cancel_deletion(
    db: Session,
    user: models.User
) -> Tuple[bool, Optional[str]]:
    """
    Cancel a scheduled account deletion.

    Args:
        db: Database session
        user: User object

    Returns:
        Tuple of (success, error_message)
    """
    db_user = db.query(models.User).filter(models.User.id == user.id).first()

    if not db_user:
        return False, "User not found"

    if db_user.deleted_at is None:
        return False, "Account is not scheduled for deletion"

    if db_user.scheduled_deletion_at and db_user.scheduled_deletion_at < datetime.now(timezone.utc):
        return False, "Grace period has expired"

    # Cancel deletion
    db_user.deleted_at = None
    db_user.scheduled_deletion_at = None
    db_user.is_active = True

    db.commit()

    logger.info(f"Account deletion cancelled for user {db_user.username}")
    return True, None


def permanently_delete_account(db: Session, user_id: int) -> bool:
    """
    Permanently delete a user account and all associated data.
    This should be called by a background task after grace period.

    Args:
        db: Database session
        user_id: User ID to delete

    Returns:
        Success status
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        return False

    username = user.username

    # Delete all user data (cascades handle related records)
    # Note: Due to ON DELETE CASCADE, related records will be deleted automatically
    db.delete(user)
    db.commit()

    logger.info(f"Account permanently deleted: {username} (ID: {user_id})")
    return True
