"""
Business logic for the Albums feature.

Provides:
- Album CRUD operations
- Image management within albums
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional, List
import logging

import models

logger = logging.getLogger(__name__)


class AlbumService:
    """Service class for album operations."""

    @staticmethod
    def create_album(
        db: Session,
        owner_id: int,
        name: str,
        description: Optional[str] = None
    ) -> models.Album:
        """Create a new album."""
        album = models.Album(
            owner_id=owner_id,
            name=name,
            description=description
        )
        db.add(album)

        try:
            db.commit()
            db.refresh(album)
            logger.info(f"Album created: {name} (ID: {album.id})")
            return album
        except Exception as e:
            db.rollback()
            logger.exception(f"Failed to create album {name}: {e}")
            raise ValueError(f"Failed to create album: {str(e)}")

    @staticmethod
    def get_album(
        db: Session,
        album_id: int,
        owner_id: int
    ) -> Optional[models.Album]:
        """Get an album by ID with images loaded."""
        return db.query(models.Album)\
            .options(joinedload(models.Album.images), joinedload(models.Album.cover_image))\
            .filter(
                models.Album.id == album_id,
                models.Album.owner_id == owner_id
            ).first()

    @staticmethod
    def get_albums_by_user(
        db: Session,
        owner_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[models.Album]:
        """Get all albums for a user with image counts."""
        albums = db.query(models.Album)\
            .options(joinedload(models.Album.cover_image))\
            .filter(models.Album.owner_id == owner_id)\
            .order_by(models.Album.updated_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
        return albums

    @staticmethod
    def get_album_image_count(db: Session, album_id: int) -> int:
        """Get the number of images in an album."""
        return db.query(func.count(models.AlbumImage.image_id))\
            .filter(models.AlbumImage.album_id == album_id)\
            .scalar() or 0

    @staticmethod
    def update_album(
        db: Session,
        album_id: int,
        owner_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        cover_image_id: Optional[int] = None
    ) -> Optional[models.Album]:
        """Update an album's details."""
        album = db.query(models.Album).filter(
            models.Album.id == album_id,
            models.Album.owner_id == owner_id
        ).first()

        if not album:
            return None

        if name is not None:
            album.name = name
        if description is not None:
            album.description = description
        if cover_image_id is not None:
            # Verify the image exists and belongs to user
            image = db.query(models.Image).filter(
                models.Image.id == cover_image_id,
                models.Image.owner_id == owner_id
            ).first()
            if image:
                album.cover_image_id = cover_image_id

        try:
            db.commit()
            db.refresh(album)
            logger.info(f"Album {album_id} updated")
            return album
        except Exception as e:
            db.rollback()
            logger.exception(f"Failed to update album {album_id}: {e}")
            raise ValueError(f"Failed to update album: {str(e)}")

    @staticmethod
    def delete_album(
        db: Session,
        album_id: int,
        owner_id: int
    ) -> bool:
        """Delete an album (does not delete the images)."""
        album = db.query(models.Album).filter(
            models.Album.id == album_id,
            models.Album.owner_id == owner_id
        ).first()

        if not album:
            return False

        try:
            db.delete(album)
            db.commit()
            logger.info(f"Album {album_id} deleted")
            return True
        except Exception as e:
            db.rollback()
            logger.exception(f"Failed to delete album {album_id}: {e}")
            raise ValueError(f"Failed to delete album: {str(e)}")

    @staticmethod
    def add_images_to_album(
        db: Session,
        album_id: int,
        owner_id: int,
        image_ids: List[int]
    ) -> int:
        """Add images to an album. Returns count of images added."""
        # Verify album exists and belongs to user
        album = db.query(models.Album).filter(
            models.Album.id == album_id,
            models.Album.owner_id == owner_id
        ).first()

        if not album:
            raise ValueError("Album not found")

        # Get valid image IDs (owned by user and not already in album)
        existing = db.query(models.AlbumImage.image_id)\
            .filter(models.AlbumImage.album_id == album_id)\
            .all()
        existing_ids = {r[0] for r in existing}

        valid_images = db.query(models.Image.id).filter(
            models.Image.id.in_(image_ids),
            models.Image.owner_id == owner_id,
            models.Image.is_trashed == False
        ).all()
        valid_ids = {r[0] for r in valid_images}

        # Filter out already-added images
        new_ids = valid_ids - existing_ids

        if not new_ids:
            return 0

        # Get max position
        max_pos = db.query(func.max(models.AlbumImage.position))\
            .filter(models.AlbumImage.album_id == album_id)\
            .scalar() or 0

        # Add new images
        added = 0
        for img_id in new_ids:
            max_pos += 1
            album_image = models.AlbumImage(
                album_id=album_id,
                image_id=img_id,
                position=max_pos
            )
            db.add(album_image)
            added += 1

        # Set cover image if album doesn't have one
        if album.cover_image_id is None and new_ids:
            album.cover_image_id = next(iter(new_ids))

        try:
            db.commit()
            logger.info(f"Added {added} images to album {album_id}")
            return added
        except Exception as e:
            db.rollback()
            logger.exception(f"Failed to add images to album {album_id}: {e}")
            raise ValueError(f"Failed to add images: {str(e)}")

    @staticmethod
    def remove_images_from_album(
        db: Session,
        album_id: int,
        owner_id: int,
        image_ids: List[int]
    ) -> int:
        """Remove images from an album. Returns count of images removed."""
        # Verify album exists and belongs to user
        album = db.query(models.Album).filter(
            models.Album.id == album_id,
            models.Album.owner_id == owner_id
        ).first()

        if not album:
            raise ValueError("Album not found")

        # Remove images
        deleted = db.query(models.AlbumImage).filter(
            models.AlbumImage.album_id == album_id,
            models.AlbumImage.image_id.in_(image_ids)
        ).delete(synchronize_session=False)

        # Update cover image if it was removed
        if album.cover_image_id in image_ids:
            # Get first remaining image
            first_image = db.query(models.AlbumImage.image_id)\
                .filter(models.AlbumImage.album_id == album_id)\
                .order_by(models.AlbumImage.position)\
                .first()
            album.cover_image_id = first_image[0] if first_image else None

        try:
            db.commit()
            logger.info(f"Removed {deleted} images from album {album_id}")
            return deleted
        except Exception as e:
            db.rollback()
            logger.exception(f"Failed to remove images from album {album_id}: {e}")
            raise ValueError(f"Failed to remove images: {str(e)}")

    @staticmethod
    def get_album_images(
        db: Session,
        album_id: int,
        owner_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[models.Image]:
        """Get images in an album ordered by position."""
        # Verify album belongs to user
        album = db.query(models.Album).filter(
            models.Album.id == album_id,
            models.Album.owner_id == owner_id
        ).first()

        if not album:
            return []

        # Get images with tags loaded
        images = db.query(models.Image)\
            .join(models.AlbumImage)\
            .options(joinedload(models.Image.tags))\
            .filter(
                models.AlbumImage.album_id == album_id,
                models.Image.is_trashed == False
            )\
            .order_by(models.AlbumImage.position)\
            .offset(skip)\
            .limit(limit)\
            .all()

        return images
