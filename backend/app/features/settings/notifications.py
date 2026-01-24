"""
Settings Feature - Notification Preferences Service (Phase 5)

Business logic for managing user notification preferences.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models import NotificationPreferences
from features.auth.models import User

logger = logging.getLogger(__name__)


def get_notification_preferences(db: Session, user: User) -> NotificationPreferences:
    """
    Get user's notification preferences.

    Creates default preferences if none exist.

    Args:
        db: Database session
        user: Current user

    Returns:
        NotificationPreferences object
    """
    prefs = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == user.id
    ).first()

    if not prefs:
        prefs = _create_default_preferences(db, user.id)

    return prefs


def _create_default_preferences(db: Session, user_id: int) -> NotificationPreferences:
    """
    Create default notification preferences for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        New NotificationPreferences object with defaults
    """
    prefs = NotificationPreferences(
        user_id=user_id,
        email_security_alerts=True,
        email_weekly_digest=False,
        email_product_updates=True,
        push_enabled=False
    )

    db.add(prefs)
    db.commit()
    db.refresh(prefs)

    logger.info(f"Created default notification preferences for user {user_id}")
    return prefs


def update_notification_preferences(
    db: Session,
    user: User,
    email_security_alerts: bool = None,
    email_weekly_digest: bool = None,
    email_product_updates: bool = None,
    push_enabled: bool = None
) -> tuple[NotificationPreferences, str | None]:
    """
    Update user's notification preferences.

    Only provided fields will be updated.

    Args:
        db: Database session
        user: Current user
        email_security_alerts: Enable security alert emails
        email_weekly_digest: Enable weekly digest emails
        email_product_updates: Enable product update emails
        push_enabled: Enable push notifications

    Returns:
        Tuple of (updated preferences, error message or None)
    """
    prefs = get_notification_preferences(db, user)

    # Track changes for logging
    changes = []

    if email_security_alerts is not None and prefs.email_security_alerts != email_security_alerts:
        prefs.email_security_alerts = email_security_alerts
        changes.append(f"email_security_alerts={email_security_alerts}")

    if email_weekly_digest is not None and prefs.email_weekly_digest != email_weekly_digest:
        prefs.email_weekly_digest = email_weekly_digest
        changes.append(f"email_weekly_digest={email_weekly_digest}")

    if email_product_updates is not None and prefs.email_product_updates != email_product_updates:
        prefs.email_product_updates = email_product_updates
        changes.append(f"email_product_updates={email_product_updates}")

    if push_enabled is not None and prefs.push_enabled != push_enabled:
        prefs.push_enabled = push_enabled
        changes.append(f"push_enabled={push_enabled}")

    if changes:
        prefs.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(prefs)
        logger.info(f"Updated notification preferences for user {user.id}: {', '.join(changes)}")

    return prefs, None


def reset_notification_preferences(db: Session, user: User) -> NotificationPreferences:
    """
    Reset notification preferences to defaults.

    Args:
        db: Database session
        user: Current user

    Returns:
        Reset NotificationPreferences object
    """
    prefs = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == user.id
    ).first()

    if prefs:
        prefs.email_security_alerts = True
        prefs.email_weekly_digest = False
        prefs.email_product_updates = True
        prefs.push_enabled = False
        prefs.updated_at = datetime.now(timezone.utc)
    else:
        prefs = _create_default_preferences(db, user.id)

    db.commit()
    db.refresh(prefs)

    logger.info(f"Reset notification preferences to defaults for user {user.id}")
    return prefs


def should_send_security_alert(db: Session, user_id: int) -> bool:
    """
    Check if security alert emails should be sent to user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        True if security alerts are enabled
    """
    prefs = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == user_id
    ).first()

    # Default to True if no preferences exist
    return prefs.email_security_alerts if prefs else True


def should_send_weekly_digest(db: Session, user_id: int) -> bool:
    """
    Check if weekly digest emails should be sent to user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        True if weekly digest is enabled
    """
    prefs = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == user_id
    ).first()

    return prefs.email_weekly_digest if prefs else False


def should_send_product_updates(db: Session, user_id: int) -> bool:
    """
    Check if product update emails should be sent to user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        True if product updates are enabled
    """
    prefs = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == user_id
    ).first()

    return prefs.email_product_updates if prefs else True
