"""
Business logic for the Images feature.

Provides:
- Image CRUD operations
- File management
- Analysis status updates
- Blur hash generation for instant loading
- Favorites, trash, and rename operations
- Text and semantic search

This module consolidates all image services into a single ImageService class
for backward compatibility.
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Tuple

import models

# Import from sub-services
from features.images.services.image_crud import ImageCRUDService
from features.images.services.image_status import ImageStatusService
from features.images.services.image_search import ImageSearchService


class ImageService:
    """
    Service class for image operations.

    Consolidates CRUD, status, and search operations.
    """

    # =========================================================================
    # CRUD Operations (delegated to ImageCRUDService)
    # =========================================================================

    @staticmethod
    def generate_blur_hash(image_bytes: bytes) -> Tuple[Optional[str], Optional[int], Optional[int]]:
        """Generate a blur hash from image bytes for instant placeholder loading."""
        return ImageCRUDService.generate_blur_hash(image_bytes)

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
        return ImageCRUDService.create_image(
            db, filename, filepath, prompt, owner_id, blur_hash, width, height, file_size
        )

    @staticmethod
    def get_image(db: Session, image_id: int) -> Optional[models.Image]:
        """Get an image by ID."""
        return ImageCRUDService.get_image(db, image_id)

    @staticmethod
    def get_image_by_owner(db: Session, image_id: int, owner_id: int) -> Optional[models.Image]:
        """Get an image by ID, filtered by owner."""
        return ImageCRUDService.get_image_by_owner(db, image_id, owner_id)

    @staticmethod
    def get_images_by_user(
        db: Session,
        owner_id: int,
        skip: int = 0,
        limit: int = 100,
        include_trashed: bool = False
    ) -> List[models.Image]:
        """Get all images for a user with tags and notes eagerly loaded."""
        return ImageCRUDService.get_images_by_user(db, owner_id, skip, limit, include_trashed)

    @staticmethod
    def update_analysis_status(
        db: Session,
        image_id: int,
        status: str,
        result: Optional[str] = None
    ) -> Optional[models.Image]:
        """Update the AI analysis status and result for an image."""
        return ImageCRUDService.update_analysis_status(db, image_id, status, result)

    @staticmethod
    def delete_image(
        db: Session,
        image_id: int,
        owner_id: int,
        delete_file: bool = True
    ) -> bool:
        """Delete an image and optionally its file."""
        return ImageCRUDService.delete_image(db, image_id, owner_id, delete_file)

    @staticmethod
    def validate_file(
        content_type: Optional[str],
        file_size: int,
        filename: Optional[str]
    ) -> tuple[bool, Optional[str]]:
        """Validate an uploaded file."""
        return ImageCRUDService.validate_file(content_type, file_size, filename)

    @staticmethod
    def save_file(contents: bytes, filename: str) -> str:
        """Save file contents to the upload directory."""
        return ImageCRUDService.save_file(contents, filename)

    @staticmethod
    def file_exists(filepath: str) -> bool:
        """Check if an image file exists on disk."""
        return ImageCRUDService.file_exists(filepath)

    # =========================================================================
    # Status Operations (delegated to ImageStatusService)
    # =========================================================================

    @staticmethod
    def toggle_favorite(db: Session, image_id: int, owner_id: int) -> Optional[models.Image]:
        """Toggle the favorite status of an image."""
        return ImageStatusService.toggle_favorite(db, image_id, owner_id)

    @staticmethod
    def get_favorites(
        db: Session,
        owner_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[models.Image]:
        """Get all favorited images for a user."""
        return ImageStatusService.get_favorites(db, owner_id, skip, limit)

    @staticmethod
    def move_to_trash(db: Session, image_id: int, owner_id: int) -> Optional[models.Image]:
        """Move an image to trash."""
        return ImageStatusService.move_to_trash(db, image_id, owner_id)

    @staticmethod
    def restore_from_trash(db: Session, image_id: int, owner_id: int) -> Optional[models.Image]:
        """Restore an image from trash."""
        return ImageStatusService.restore_from_trash(db, image_id, owner_id)

    @staticmethod
    def get_trashed(
        db: Session,
        owner_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[models.Image]:
        """Get all trashed images for a user."""
        return ImageStatusService.get_trashed(db, owner_id, skip, limit)

    @staticmethod
    def permanent_delete(db: Session, image_id: int, owner_id: int) -> bool:
        """Permanently delete an image from trash."""
        return ImageStatusService.permanent_delete(db, image_id, owner_id)

    @staticmethod
    def rename_image(
        db: Session,
        image_id: int,
        owner_id: int,
        display_name: str
    ) -> Optional[models.Image]:
        """Rename an image by setting its display name."""
        return ImageStatusService.rename_image(db, image_id, owner_id, display_name)

    # =========================================================================
    # Search Operations (delegated to ImageSearchService)
    # =========================================================================

    @staticmethod
    def search_images_text(
        db: Session,
        owner_id: int,
        query: str,
        limit: int = 50
    ) -> List[models.Image]:
        """Full-text search on images using PostgreSQL tsvector."""
        return ImageSearchService.search_images_text(db, owner_id, query, limit)

    @staticmethod
    def search_images_smart(
        db: Session,
        owner_id: int,
        query: str,
        limit: int = 50,
        threshold: float = 0.3
    ) -> List[models.Image]:
        """Semantic search on images using pgvector embeddings."""
        return ImageSearchService.search_images_smart(db, owner_id, query, limit, threshold)
