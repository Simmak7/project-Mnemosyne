"""
Settings Feature - Service Layer

Business logic for user preferences management.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

import models

logger = logging.getLogger(__name__)


def get_user_preferences(db: Session, user: models.User) -> models.UserPreferences:
    """
    Get user preferences, creating defaults if they don't exist.

    Args:
        db: Database session
        user: User object

    Returns:
        UserPreferences object
    """
    preferences = db.query(models.UserPreferences).filter(
        models.UserPreferences.user_id == user.id
    ).first()

    if not preferences:
        preferences = create_default_preferences(db, user)

    return preferences


def create_default_preferences(db: Session, user: models.User) -> models.UserPreferences:
    """
    Create default preferences for a user.

    Args:
        db: Database session
        user: User object

    Returns:
        Created UserPreferences object
    """
    preferences = models.UserPreferences(
        user_id=user.id,
        theme="dark",
        accent_color="blue",
        ui_density="comfortable",
        font_size="medium",
        sidebar_collapsed=False,
        default_view="notes"
    )

    db.add(preferences)
    db.commit()
    db.refresh(preferences)

    logger.info(f"Created default preferences for user {user.username}")
    return preferences


def update_user_preferences(
    db: Session,
    user: models.User,
    theme: Optional[str] = None,
    accent_color: Optional[str] = None,
    ui_density: Optional[str] = None,
    font_size: Optional[str] = None,
    sidebar_collapsed: Optional[bool] = None,
    default_view: Optional[str] = None,
    rag_model: Optional[str] = None,
    brain_model: Optional[str] = None,
    nexus_model: Optional[str] = None,
    vision_model: Optional[str] = None,
    cloud_ai_enabled: Optional[bool] = None,
    cloud_ai_provider: Optional[str] = None,
    cloud_rag_model: Optional[str] = None,
    cloud_brain_model: Optional[str] = None,
) -> Tuple[models.UserPreferences, Optional[str]]:
    """
    Update user preferences.

    Args:
        db: Database session
        user: User object
        theme: Theme setting (light/dark)
        accent_color: Accent color
        ui_density: UI density (compact/comfortable/spacious)
        font_size: Font size (small/medium/large)
        sidebar_collapsed: Whether sidebar is collapsed
        default_view: Default view on login
        rag_model: Preferred RAG model (null = use system default)
        brain_model: Preferred Brain model (null = use system default)

    Returns:
        Tuple of (updated preferences, error message if any)
    """
    from core.model_service import validate_model_id

    preferences = get_user_preferences(db, user)

    # Update fields if provided
    if theme is not None:
        preferences.theme = theme

    if accent_color is not None:
        preferences.accent_color = accent_color

    if ui_density is not None:
        preferences.ui_density = ui_density

    if font_size is not None:
        preferences.font_size = font_size

    if sidebar_collapsed is not None:
        preferences.sidebar_collapsed = sidebar_collapsed

    if default_view is not None:
        preferences.default_view = default_view

    # Handle model preferences
    # Empty string = reset to default, valid model ID = set preference
    if rag_model is not None:
        if rag_model == "":
            preferences.rag_model = None
        elif validate_model_id(rag_model):
            preferences.rag_model = rag_model
        else:
            return None, f"Invalid RAG model: {rag_model}"

    if brain_model is not None:
        if brain_model == "":
            preferences.brain_model = None
        elif validate_model_id(brain_model):
            preferences.brain_model = brain_model
        else:
            return None, f"Invalid Brain model: {brain_model}"

    if nexus_model is not None:
        if nexus_model == "":
            preferences.nexus_model = None
        elif validate_model_id(nexus_model):
            preferences.nexus_model = nexus_model
        else:
            return None, f"Invalid NEXUS model: {nexus_model}"

    if vision_model is not None:
        if vision_model == "":
            preferences.vision_model = None
        elif validate_model_id(vision_model):
            preferences.vision_model = vision_model
        else:
            return None, f"Invalid vision model: {vision_model}"

    # Cloud AI preferences
    if cloud_ai_enabled is not None:
        preferences.cloud_ai_enabled = cloud_ai_enabled

    if cloud_ai_provider is not None:
        valid_providers = {"anthropic", "openai", "custom", ""}
        if cloud_ai_provider in valid_providers:
            preferences.cloud_ai_provider = cloud_ai_provider or None
        else:
            return None, f"Invalid cloud provider: {cloud_ai_provider}"

    if cloud_rag_model is not None:
        preferences.cloud_rag_model = cloud_rag_model or None

    if cloud_brain_model is not None:
        preferences.cloud_brain_model = cloud_brain_model or None

    # Update timestamp
    preferences.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(preferences)
        logger.info(f"Updated preferences for user {user.username}")
        return preferences, None
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating preferences for user {user.username}: {e}")
        return None, "Failed to update preferences"


def reset_user_preferences(db: Session, user: models.User) -> models.UserPreferences:
    """
    Reset user preferences to defaults.

    Args:
        db: Database session
        user: User object

    Returns:
        Reset UserPreferences object
    """
    preferences = db.query(models.UserPreferences).filter(
        models.UserPreferences.user_id == user.id
    ).first()

    if preferences:
        preferences.theme = "dark"
        preferences.accent_color = "blue"
        preferences.ui_density = "comfortable"
        preferences.font_size = "medium"
        preferences.sidebar_collapsed = False
        preferences.default_view = "notes"
        preferences.rag_model = None  # Reset to system default
        preferences.brain_model = None  # Reset to system default
        preferences.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(preferences)
        logger.info(f"Reset preferences for user {user.username}")
    else:
        preferences = create_default_preferences(db, user)

    return preferences
