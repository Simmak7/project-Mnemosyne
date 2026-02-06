"""
Image CRUD Operations Service.

Handles create, read, update, delete operations for images.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Tuple
import logging
import os
from io import BytesIO

from PIL import Image as PILImage
import blurhash
import numpy as np

import models
from core import config

logger = logging.getLogger(__name__)


class ImageCRUDService:
    """Service class for image CRUD operations."""

    @staticmethod
    def generate_blur_hash(image_bytes: bytes) -> Tuple[Optional[str], Optional[int], Optional[int]]:
        """
        Generate a blur hash from image bytes for instant placeholder loading.

        Returns:
            Tuple of (blur_hash, width, height) or (None, None, None) on error
        """
        try:
            img = PILImage.open(BytesIO(image_bytes))
            width, height = img.size

            # Resize for faster blur hash computation (max 100px on longest side)
            max_size = 100
            if width > max_size or height > max_size:
                ratio = min(max_size / width, max_size / height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, PILImage.Resampling.LANCZOS)

            # Convert to RGB if necessary (blurhash requires RGB)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Generate blur hash with 4x3 components
            img_array = np.array(img)
            hash_str = blurhash.encode(img_array, components_x=4, components_y=3)

            logger.debug(f"Generated blur hash: {hash_str} for image {width}x{height}")
            return hash_str, width, height

        except Exception as e:
            logger.warning(f"Failed to generate blur hash: {str(e)}")
            return None, None, None

    @staticmethod
    def create_image(
        db: Session,
        filename: str,
        filepath: str,
        prompt: Optional[str] = None,
        owner_id: Optional[int] = None,
        blur_hash: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        file_size: Optional[int] = None
    ) -> models.Image:
        """Create a new image record in the database."""
        db_image = models.Image(
            filename=filename,
            filepath=filepath,
            prompt=prompt,
            owner_id=owner_id,
            ai_analysis_status="queued",
            blur_hash=blur_hash,
            width=width,
            height=height,
            file_size=file_size
        )
        db.add(db_image)

        try:
            db.commit()
            db.refresh(db_image)
            logger.info(f"Image created: {filename} (ID: {db_image.id})")
            return db_image
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error creating image {filename}: {e}")
            raise ValueError(f"Image with filename {filename} already exists")
        except Exception as e:
            db.rollback()
            logger.exception(f"Unexpected error creating image {filename}: {e}")
            raise ValueError(f"Failed to create image: {str(e)}")

    @staticmethod
    def get_image(db: Session, image_id: int) -> Optional[models.Image]:
        """Get an image by ID."""
        return db.query(models.Image).filter(models.Image.id == image_id).first()

    @staticmethod
    def get_image_by_owner(db: Session, image_id: int, owner_id: int) -> Optional[models.Image]:
        """Get an image by ID, filtered by owner."""
        return db.query(models.Image).filter(
            models.Image.id == image_id,
            models.Image.owner_id == owner_id
        ).first()

    @staticmethod
    def get_images_by_user(
        db: Session,
        owner_id: int,
        skip: int = 0,
        limit: int = 100,
        include_trashed: bool = False
    ) -> List[models.Image]:
        """Get all images for a user with tags and notes eagerly loaded."""
        query = db.query(models.Image)\
            .options(joinedload(models.Image.tags), joinedload(models.Image.notes))\
            .filter(models.Image.owner_id == owner_id)

        if not include_trashed:
            query = query.filter(models.Image.is_trashed == False)

        return query.order_by(models.Image.id.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def update_analysis_status(
        db: Session,
        image_id: int,
        status: str,
        result: Optional[str] = None
    ) -> Optional[models.Image]:
        """Update the AI analysis status and result for an image."""
        db_image = db.query(models.Image).filter(models.Image.id == image_id).first()

        if db_image:
            db_image.ai_analysis_status = status
            if result is not None:
                db_image.ai_analysis_result = result

            try:
                db.commit()
                db.refresh(db_image)
                logger.debug(f"Image {image_id} status updated to {status}")
            except Exception as e:
                db.rollback()
                logger.exception(f"Error updating image {image_id} analysis result: {e}")
                raise ValueError(f"Failed to update image analysis: {str(e)}")

        return db_image

    @staticmethod
    def delete_image(db: Session, image_id: int, owner_id: int, delete_file: bool = True) -> bool:
        """Delete an image and optionally its file."""
        image = db.query(models.Image).filter(
            models.Image.id == image_id,
            models.Image.owner_id == owner_id
        ).first()

        if not image:
            return False

        filepath = image.filepath

        try:
            db.delete(image)
            db.commit()
            logger.info(f"Image {image_id} deleted from database")

            if delete_file and filepath and os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Image file deleted: {filepath}")

            return True

        except Exception as e:
            db.rollback()
            logger.exception(f"Failed to delete image {image_id}: {e}")
            raise ValueError(f"Failed to delete image: {str(e)}")

    @staticmethod
    def validate_file(content_type: Optional[str], file_size: int, filename: Optional[str]) -> tuple[bool, Optional[str]]:
        """Validate an uploaded file."""
        if not content_type:
            return False, "File type could not be determined"

        if content_type not in config.ALLOWED_FILE_TYPES:
            return False, f"File type {content_type} not allowed. Allowed types: {', '.join(config.ALLOWED_FILE_TYPES)}"

        if file_size > config.MAX_UPLOAD_SIZE_BYTES:
            size_mb = file_size / 1024 / 1024
            return False, f"File size ({size_mb:.2f}MB) exceeds maximum ({config.MAX_UPLOAD_SIZE_MB}MB)"

        if file_size == 0:
            return False, "Uploaded file is empty"

        if not filename:
            return False, "Filename is required"

        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        file_extension = os.path.splitext(filename)[1].lower()

        if file_extension not in allowed_extensions:
            return False, f"File extension {file_extension} not allowed. Allowed: {', '.join(allowed_extensions)}"

        return True, None

    @staticmethod
    def save_file(contents: bytes, filename: str) -> str:
        """Save file contents to the upload directory."""
        file_path = os.path.join(config.UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            buffer.write(contents)

        logger.debug(f"File saved to: {file_path}")
        return file_path

    @staticmethod
    def file_exists(filepath: str) -> bool:
        """Check if an image file exists on disk."""
        return os.path.exists(filepath)
