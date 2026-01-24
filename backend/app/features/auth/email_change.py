"""
Auth Feature - Email Change Service (Phase 2)

Handles email change requests with verification.
"""

import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from core import config
from core.auth import verify_password
import models

logger = logging.getLogger(__name__)

# Token expiry time (1 hour)
EMAIL_CHANGE_TOKEN_EXPIRE_MINUTES = 60


def request_email_change(
    db: Session,
    user: models.User,
    new_email: str,
    password: str
) -> Tuple[bool, str]:
    """
    Request an email change. Sends verification to new email.

    Args:
        db: Database session
        user: Current user
        new_email: New email address
        password: Current password for verification

    Returns:
        Tuple of (success, message)
    """
    # Re-fetch user in this session
    db_user = db.query(models.User).filter(models.User.id == user.id).first()
    if not db_user:
        return False, "User not found"

    # Verify password
    if not verify_password(password, db_user.hashed_password):
        return False, "Incorrect password"

    # Check if new email is same as current
    if new_email.lower() == db_user.email.lower():
        return False, "New email is same as current email"

    # Check if new email is already in use
    existing = db.query(models.User).filter(
        models.User.email == new_email.lower()
    ).first()
    if existing:
        return False, "Email address is already in use"

    # Invalidate any existing email change tokens for this user
    db.query(models.EmailChangeToken).filter(
        models.EmailChangeToken.user_id == db_user.id,
        models.EmailChangeToken.used == False
    ).update({"used": True})

    # Generate token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=EMAIL_CHANGE_TOKEN_EXPIRE_MINUTES
    )

    # Create token record
    email_token = models.EmailChangeToken(
        user_id=db_user.id,
        new_email=new_email.lower(),
        token=token,
        expires_at=expires_at
    )
    db.add(email_token)
    db.commit()

    # Send verification email
    try:
        from core.email import send_email_change_verification
        send_email_change_verification(
            to_email=new_email,
            username=db_user.username,
            token=token
        )
        logger.info(f"Email change verification sent to {new_email} for user {db_user.username}")
    except ImportError:
        logger.warning("Email service not configured, skipping verification email")
    except Exception as e:
        logger.error(f"Failed to send email change verification: {e}")
        # Don't fail the request - token is still valid

    return True, "Verification email sent to your new email address"


def verify_email_change(
    db: Session,
    token: str
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Verify email change token and update user's email.

    Args:
        db: Database session
        token: Verification token

    Returns:
        Tuple of (success, old_email, error_message)
    """
    # Find token
    email_token = db.query(models.EmailChangeToken).filter(
        models.EmailChangeToken.token == token
    ).first()

    if not email_token:
        return False, None, "Invalid verification token"

    if email_token.used:
        return False, None, "Token has already been used"

    if email_token.expires_at < datetime.now(timezone.utc):
        return False, None, "Token has expired"

    # Get user
    user = db.query(models.User).filter(
        models.User.id == email_token.user_id
    ).first()

    if not user:
        return False, None, "User not found"

    # Check if new email is still available
    existing = db.query(models.User).filter(
        models.User.email == email_token.new_email,
        models.User.id != user.id
    ).first()
    if existing:
        return False, None, "Email address is no longer available"

    # Store old email for notification
    old_email = user.email

    # Update email
    user.email = email_token.new_email
    email_token.used = True

    db.commit()

    # Notify old email about the change
    try:
        from core.email import send_email_changed_notification
        send_email_changed_notification(
            to_email=old_email,
            username=user.username,
            new_email=email_token.new_email
        )
    except ImportError:
        logger.warning("Email service not configured")
    except Exception as e:
        logger.error(f"Failed to send email change notification: {e}")

    logger.info(f"Email changed for user {user.username}: {old_email} -> {email_token.new_email}")
    return True, old_email, None


def get_masked_email(email: str) -> str:
    """
    Mask an email address for privacy.

    Example: john.doe@example.com -> j***e@e***e.com
    """
    try:
        local, domain = email.split('@')
        domain_name, domain_ext = domain.rsplit('.', 1)

        masked_local = local[0] + '***' + local[-1] if len(local) > 2 else local[0] + '***'
        masked_domain = domain_name[0] + '***' + domain_name[-1] if len(domain_name) > 2 else domain_name[0] + '***'

        return f"{masked_local}@{masked_domain}.{domain_ext}"
    except Exception:
        return "***@***.***"
