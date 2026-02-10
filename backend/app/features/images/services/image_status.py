"""
Image Status Operations Service.

Handles favorites, trash, and rename operations for images.
"""

from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from datetime import datetime
import logging
import os

import models

logger = logging.getLogger(__name__)


class ImageStatusService:
    """Service class for image status operations."""

    @staticmethod
    def toggle_favorite(db: Session, image_id: int, owner_id: int) -> Optional[models.Image]:
        """Toggle the favorite status of an image."""
        image = db.query(models.Image).filter(
            models.Image.id == image_id,
            models.Image.owner_id == owner_id
        ).first()

        if not image:
            return None

        image.is_favorite = not image.is_favorite

        try:
            db.commit()
            db.refresh(image)
            logger.info(f"Image {image_id} favorite toggled to {image.is_favorite}")
            return image
        except Exception as e:
            db.rollback()
            logger.exception(f"Error toggling favorite for image {image_id}: {e}")
            raise ValueError(f"Failed to toggle favorite: {str(e)}")

    @staticmethod
    def get_favorites(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[models.Image]:
        """Get all favorited images for a user."""
        return db.query(models.Image)\
            .options(joinedload(models.Image.tags), joinedload(models.Image.notes))\
            .filter(
                models.Image.owner_id == owner_id,
                models.Image.is_favorite == True,
                models.Image.is_trashed == False
            )\
            .order_by(models.Image.id.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def move_to_trash(db: Session, image_id: int, owner_id: int) -> Optional[models.Image]:
        """Move an image to trash."""
        image = db.query(models.Image).filter(
            models.Image.id == image_id,
            models.Image.owner_id == owner_id
        ).first()

        if not image:
            return None

        image.is_trashed = True
        image.trashed_at = datetime.utcnow()

        try:
            db.commit()
            db.refresh(image)
            logger.info(f"Image {image_id} moved to trash")
            return image
        except Exception as e:
            db.rollback()
            logger.exception(f"Error moving image {image_id} to trash: {e}")
            raise ValueError(f"Failed to move to trash: {str(e)}")

    @staticmethod
    def restore_from_trash(db: Session, image_id: int, owner_id: int) -> Optional[models.Image]:
        """Restore an image from trash."""
        image = db.query(models.Image).filter(
            models.Image.id == image_id,
            models.Image.owner_id == owner_id,
            models.Image.is_trashed == True
        ).first()

        if not image:
            return None

        image.is_trashed = False
        image.trashed_at = None

        try:
            db.commit()
            db.refresh(image)
            logger.info(f"Image {image_id} restored from trash")
            return image
        except Exception as e:
            db.rollback()
            logger.exception(f"Error restoring image {image_id} from trash: {e}")
            raise ValueError(f"Failed to restore from trash: {str(e)}")

    @staticmethod
    def get_trashed(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[models.Image]:
        """Get all trashed images for a user."""
        return db.query(models.Image)\
            .options(joinedload(models.Image.tags), joinedload(models.Image.notes))\
            .filter(
                models.Image.owner_id == owner_id,
                models.Image.is_trashed == True
            )\
            .order_by(models.Image.trashed_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def permanent_delete(db: Session, image_id: int, owner_id: int) -> bool:
        """Permanently delete an image from trash."""
        image = db.query(models.Image).filter(
            models.Image.id == image_id,
            models.Image.owner_id == owner_id,
            models.Image.is_trashed == True
        ).first()

        if not image:
            return False

        filepath = image.filepath

        try:
            db.delete(image)
            db.commit()
            logger.info(f"Image {image_id} permanently deleted from database")

            if filepath and os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Image file deleted: {filepath}")

            return True

        except Exception as e:
            db.rollback()
            logger.exception(f"Failed to permanently delete image {image_id}: {e}")
            raise ValueError(f"Failed to permanently delete image: {str(e)}")

    @staticmethod
    def rename_image(db: Session, image_id: int, owner_id: int, display_name: str) -> Optional[models.Image]:
        """Rename an image by setting its display name."""
        image = db.query(models.Image).filter(
            models.Image.id == image_id,
            models.Image.owner_id == owner_id
        ).first()

        if not image:
            return None

        display_name = display_name.strip()
        image.display_name = display_name

        try:
            db.commit()
            db.refresh(image)
            logger.info(f"Image {image_id} renamed to '{display_name}'")
            return image
        except Exception as e:
            db.rollback()
            logger.exception(f"Error renaming image {image_id}: {e}")
            raise ValueError(f"Failed to rename image: {str(e)}")
