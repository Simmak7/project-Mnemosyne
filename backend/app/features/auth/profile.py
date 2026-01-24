"""
Auth Feature - Profile Service (Phase 2)

Handles user profile management including display name and avatar.
"""

import logging
from typing import Optional, Tuple

from sqlalchemy.orm import Session

import models

logger = logging.getLogger(__name__)


def get_profile(db: Session, user: models.User) -> models.User:
    """
    Get user profile with full details.

    Args:
        db: Database session
        user: User object (may be from different session)

    Returns:
        Fresh user object from this session
    """
    # Re-fetch to ensure we have the latest data
    return db.query(models.User).filter(models.User.id == user.id).first()


def update_profile(
    db: Session,
    user: models.User,
    display_name: Optional[str] = None,
    avatar_url: Optional[str] = None
) -> Tuple[models.User, Optional[str]]:
    """
    Update user profile fields.

    Args:
        db: Database session
        user: User object
        display_name: New display name (optional)
        avatar_url: New avatar URL (optional)

    Returns:
        Tuple of (updated user, error message if any)
    """
    # Re-fetch user in this session
    db_user = db.query(models.User).filter(models.User.id == user.id).first()
    if not db_user:
        return None, "User not found"

    # Update fields if provided
    if display_name is not None:
        db_user.display_name = display_name.strip() if display_name else None

    if avatar_url is not None:
        # Validate URL format if provided
        if avatar_url and not avatar_url.startswith(('http://', 'https://', '/')):
            return None, "Invalid avatar URL format"
        db_user.avatar_url = avatar_url if avatar_url else None

    try:
        db.commit()
        db.refresh(db_user)
        logger.info(f"Profile updated for user {db_user.username}")
        return db_user, None
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating profile for user {db_user.username}: {e}")
        return None, "Failed to update profile"
