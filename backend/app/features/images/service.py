"""
Business logic for the Images feature.

Provides:
- Image CRUD operations
- File management
- Analysis status updates
- Blur hash generation for instant loading
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Tuple
from datetime import datetime
import logging
import os
from io import BytesIO

from PIL import Image as PILImage
import blurhash

import models
from core import config

logger = logging.getLogger(__name__)


class ImageService:
    """Service class for image operations."""

    @staticmethod
    def generate_blur_hash(image_bytes: bytes) -> Tuple[Optional[str], Optional[int], Optional[int]]:
        """
        Generate a blur hash from image bytes for instant placeholder loading.

        Args:
            image_bytes: Raw image bytes

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

            # Generate blur hash with 4x3 components (good balance of detail)
            # Note: blurhash library uses components_x and components_y
            import numpy as np
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
        height: Optional[int] = None
    ) -> models.Image:
        """
        Create a new image record in the database.

        Args:
            db: Database session
            filename: Name of the uploaded file
            filepath: Path where the file is stored
            prompt: Optional AI analysis prompt
            owner_id: ID of the owning user
            blur_hash: BlurHash string for instant placeholder (Phase 3)
            width: Original image width in pixels
            height: Original image height in pixels

        Returns:
            Created Image model instance

        Raises:
            ValueError: If creation fails
        """
        db_image = models.Image(
            filename=filename,
            filepath=filepath,
            prompt=prompt,
            owner_id=owner_id,
            ai_analysis_status="queued",
            blur_hash=blur_hash,
            width=width,
            height=height
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
    def get_image_by_owner(
        db: Session,
        image_id: int,
        owner_id: int
    ) -> Optional[models.Image]:
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
        """
        Get all images for a user with tags and notes eagerly loaded.

        Args:
            db: Database session
            owner_id: User ID to filter by
            skip: Number of records to skip
            limit: Maximum records to return
            include_trashed: If False (default), excludes trashed images

        Returns:
            List of Image models
        """
        query = db.query(models.Image)\
            .options(joinedload(models.Image.tags), joinedload(models.Image.notes))\
            .filter(models.Image.owner_id == owner_id)

        # Exclude trashed images by default (Phase 4)
        if not include_trashed:
            query = query.filter(models.Image.is_trashed == False)

        return query.order_by(models.Image.id.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def update_analysis_status(
        db: Session,
        image_id: int,
        status: str,
        result: Optional[str] = None
    ) -> Optional[models.Image]:
        """
        Update the AI analysis status and result for an image.

        Args:
            db: Database session
            image_id: Image ID to update
            status: New status (queued, processing, completed, failed)
            result: Analysis result text (optional)

        Returns:
            Updated Image model or None if not found
        """
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
    def delete_image(
        db: Session,
        image_id: int,
        owner_id: int,
        delete_file: bool = True
    ) -> bool:
        """
        Delete an image and optionally its file.

        Args:
            db: Database session
            image_id: Image ID to delete
            owner_id: Owner ID for authorization check
            delete_file: Whether to delete the file from disk

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If deletion fails
        """
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

            # Delete file from disk if requested and exists
            if delete_file and filepath and os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Image file deleted: {filepath}")

            return True

        except Exception as e:
            db.rollback()
            logger.exception(f"Failed to delete image {image_id}: {e}")
            raise ValueError(f"Failed to delete image: {str(e)}")

    @staticmethod
    def validate_file(
        content_type: Optional[str],
        file_size: int,
        filename: Optional[str]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate an uploaded file.

        Args:
            content_type: MIME type of the file
            file_size: Size in bytes
            filename: Original filename

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate content type
        if not content_type:
            return False, "File type could not be determined"

        if content_type not in config.ALLOWED_FILE_TYPES:
            return False, f"File type {content_type} not allowed. Allowed types: {', '.join(config.ALLOWED_FILE_TYPES)}"

        # Validate file size
        if file_size > config.MAX_UPLOAD_SIZE_BYTES:
            size_mb = file_size / 1024 / 1024
            return False, f"File size ({size_mb:.2f}MB) exceeds maximum ({config.MAX_UPLOAD_SIZE_MB}MB)"

        if file_size == 0:
            return False, "Uploaded file is empty"

        # Validate filename
        if not filename:
            return False, "Filename is required"

        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        file_extension = os.path.splitext(filename)[1].lower()

        if file_extension not in allowed_extensions:
            return False, f"File extension {file_extension} not allowed. Allowed: {', '.join(allowed_extensions)}"

        return True, None

    @staticmethod
    def save_file(contents: bytes, filename: str) -> str:
        """
        Save file contents to the upload directory.

        Args:
            contents: File bytes
            filename: Unique filename to save as

        Returns:
            Full path to the saved file

        Raises:
            OSError: If file cannot be saved
        """
        file_path = os.path.join(config.UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            buffer.write(contents)

        logger.debug(f"File saved to: {file_path}")
        return file_path

    @staticmethod
    def file_exists(filepath: str) -> bool:
        """Check if an image file exists on disk."""
        return os.path.exists(filepath)

    # =========================================================================
    # Favorites & Trash Operations (Phase 4)
    # =========================================================================

    @staticmethod
    def toggle_favorite(
        db: Session,
        image_id: int,
        owner_id: int
    ) -> Optional[models.Image]:
        """
        Toggle the favorite status of an image.

        Args:
            db: Database session
            image_id: Image ID to toggle
            owner_id: Owner ID for authorization check

        Returns:
            Updated Image model or None if not found
        """
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
    def get_favorites(
        db: Session,
        owner_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[models.Image]:
        """
        Get all favorited images for a user.

        Args:
            db: Database session
            owner_id: User ID to filter by
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of favorited Image models
        """
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
    def move_to_trash(
        db: Session,
        image_id: int,
        owner_id: int
    ) -> Optional[models.Image]:
        """
        Move an image to trash.

        Args:
            db: Database session
            image_id: Image ID to trash
            owner_id: Owner ID for authorization check

        Returns:
            Updated Image model or None if not found
        """
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
    def restore_from_trash(
        db: Session,
        image_id: int,
        owner_id: int
    ) -> Optional[models.Image]:
        """
        Restore an image from trash.

        Args:
            db: Database session
            image_id: Image ID to restore
            owner_id: Owner ID for authorization check

        Returns:
            Updated Image model or None if not found
        """
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
    def get_trashed(
        db: Session,
        owner_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[models.Image]:
        """
        Get all trashed images for a user.

        Args:
            db: Database session
            owner_id: User ID to filter by
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of trashed Image models
        """
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
    def permanent_delete(
        db: Session,
        image_id: int,
        owner_id: int
    ) -> bool:
        """
        Permanently delete an image from trash.

        Args:
            db: Database session
            image_id: Image ID to delete
            owner_id: Owner ID for authorization check

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If deletion fails
        """
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

            # Delete file from disk if exists
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Image file deleted: {filepath}")

            return True

        except Exception as e:
            db.rollback()
            logger.exception(f"Failed to permanently delete image {image_id}: {e}")
            raise ValueError(f"Failed to permanently delete image: {str(e)}")

    # =========================================================================
    # Rename Operations
    # =========================================================================

    @staticmethod
    def rename_image(
        db: Session,
        image_id: int,
        owner_id: int,
        display_name: str
    ) -> Optional[models.Image]:
        """
        Rename an image by setting its display name.

        Args:
            db: Database session
            image_id: Image ID to rename
            owner_id: Owner ID for authorization check
            display_name: New display name for the image

        Returns:
            Updated Image model or None if not found
        """
        image = db.query(models.Image).filter(
            models.Image.id == image_id,
            models.Image.owner_id == owner_id
        ).first()

        if not image:
            return None

        # Clean up the display name
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

    # =========================================================================
    # Search Operations
    # =========================================================================

    @staticmethod
    def search_images_text(
        db: Session,
        owner_id: int,
        query: str,
        limit: int = 50
    ) -> List[models.Image]:
        """
        Full-text search on images using PostgreSQL tsvector.
        Searches filename, display_name, prompt, and AI analysis result.

        Args:
            db: Database session
            owner_id: User ID to filter by
            query: Search query string
            limit: Maximum results to return

        Returns:
            List of matching Image models with tags eagerly loaded
        """
        from sqlalchemy import text, func

        if not query or not query.strip():
            return []

        # Parse query for tsquery (simple AND between words)
        words = query.strip().split()
        tsquery = " & ".join(word.replace("'", "''") for word in words)

        # Use raw SQL for full-text search with ranking
        sql = text("""
            SELECT i.id,
                   ts_rank(i.search_vector, to_tsquery('english', :tsquery)) as score
            FROM images i
            WHERE i.owner_id = :owner_id
              AND i.is_trashed = false
              AND i.search_vector @@ to_tsquery('english', :tsquery)
            ORDER BY score DESC
            LIMIT :limit
        """)

        result = db.execute(sql, {
            "tsquery": tsquery,
            "owner_id": owner_id,
            "limit": limit
        })

        # Get the image IDs from the search results
        image_ids = [row.id for row in result]

        if not image_ids:
            return []

        # Fetch full image objects with relationships
        images = db.query(models.Image)\
            .options(joinedload(models.Image.tags), joinedload(models.Image.notes))\
            .filter(models.Image.id.in_(image_ids))\
            .all()

        # Sort by the original search order
        id_to_image = {img.id: img for img in images}
        sorted_images = [id_to_image[id] for id in image_ids if id in id_to_image]

        logger.info(f"Text search found {len(sorted_images)} images for query: {query}")
        return sorted_images

    @staticmethod
    def search_images_smart(
        db: Session,
        owner_id: int,
        query: str,
        limit: int = 50,
        threshold: float = 0.3
    ) -> List[models.Image]:
        """
        Semantic search on images using pgvector embeddings.
        Generates embedding for query and finds similar images.
        Falls back to text search if embeddings are not available.

        Args:
            db: Database session
            owner_id: User ID to filter by
            query: Search query string
            limit: Maximum results to return
            threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of matching Image models with tags eagerly loaded
        """
        from sqlalchemy import text

        if not query or not query.strip():
            return []

        # Check if embedding column exists in images table
        try:
            check_sql = text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'images' AND column_name = 'embedding'
            """)
            result = db.execute(check_sql)
            has_embedding_column = result.fetchone() is not None
        except Exception:
            has_embedding_column = False
            db.rollback()

        if not has_embedding_column:
            logger.info("Image embeddings not available, falling back to text search")
            return ImageService.search_images_text(db, owner_id, query, limit)

        try:
            from features.search.logic.embeddings import generate_embedding

            # Generate embedding for the query
            query_embedding = generate_embedding(query.strip())
            if not query_embedding:
                logger.warning(f"Failed to generate embedding for query: {query}")
                return ImageService.search_images_text(db, owner_id, query, limit)

            # Convert embedding to PostgreSQL array format
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

            # Use raw SQL for vector similarity search
            sql = text("""
                SELECT i.id,
                       1 - (i.embedding <=> :embedding::vector) as similarity
                FROM images i
                WHERE i.owner_id = :owner_id
                  AND i.is_trashed = false
                  AND i.embedding IS NOT NULL
                  AND (1 - (i.embedding <=> :embedding::vector)) >= :threshold
                ORDER BY i.embedding <=> :embedding::vector
                LIMIT :limit
            """)

            result = db.execute(sql, {
                "embedding": embedding_str,
                "owner_id": owner_id,
                "threshold": threshold,
                "limit": limit
            })

            # Get the image IDs from the search results
            image_ids = [row.id for row in result]

            if not image_ids:
                logger.info(f"Smart search found no images above threshold for query: {query}")
                return ImageService.search_images_text(db, owner_id, query, limit)

            # Fetch full image objects with relationships
            images = db.query(models.Image)\
                .options(joinedload(models.Image.tags), joinedload(models.Image.notes))\
                .filter(models.Image.id.in_(image_ids))\
                .all()

            # Sort by the original search order
            id_to_image = {img.id: img for img in images}
            sorted_images = [id_to_image[id] for id in image_ids if id in id_to_image]

            logger.info(f"Smart search found {len(sorted_images)} images for query: {query}")
            return sorted_images

        except Exception as e:
            logger.error(f"Smart search failed: {str(e)}", exc_info=True)
            # Rollback the failed transaction before falling back
            db.rollback()
            return ImageService.search_images_text(db, owner_id, query, limit)
