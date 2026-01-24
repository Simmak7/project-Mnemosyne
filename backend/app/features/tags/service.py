"""
Tags Feature - Service Layer

Business logic for tag operations including:
- Get/create tags (case-insensitive, stored lowercase)
- Add/remove tags from notes
- Add/remove tags from images
- List tags for a user
"""

import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

import models

logger = logging.getLogger(__name__)


class TagService:
    """Service class for tag-related operations."""

    @staticmethod
    def get_or_create_tag(
        db: Session,
        tag_name: str,
        owner_id: Optional[int] = None
    ) -> models.Tag:
        """
        Get existing tag or create new one.
        Tags are case-insensitive and stored in lowercase.

        Args:
            db: Database session
            tag_name: Name of the tag
            owner_id: ID of the tag owner (user)

        Returns:
            Tag model instance

        Raises:
            HTTPException: On database errors
        """
        tag_name_lower = tag_name.lower().strip()

        # Try to find existing tag
        tag = db.query(models.Tag).filter(
            models.Tag.name == tag_name_lower,
            models.Tag.owner_id == owner_id
        ).first()

        if tag:
            return tag

        # Create new tag
        tag = models.Tag(name=tag_name_lower, owner_id=owner_id)
        db.add(tag)

        try:
            db.commit()
            db.refresh(tag)
            return tag
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error creating tag '{tag_name}': {e}")
            # Try to fetch again - might have been created by concurrent request
            tag = db.query(models.Tag).filter(
                models.Tag.name == tag_name_lower,
                models.Tag.owner_id == owner_id
            ).first()
            if tag:
                return tag
            raise HTTPException(status_code=409, detail="Tag creation conflict")
        except Exception as e:
            db.rollback()
            logger.exception(f"Error creating tag '{tag_name}': {e}")
            raise HTTPException(status_code=500, detail="Failed to create tag")

    @staticmethod
    def get_tags_by_user(db: Session, owner_id: int) -> List[models.Tag]:
        """
        Get all tags for a user.

        Args:
            db: Database session
            owner_id: ID of the tag owner

        Returns:
            List of Tag model instances
        """
        return db.query(models.Tag).filter(models.Tag.owner_id == owner_id).all()

    @staticmethod
    def get_tag_by_id(db: Session, tag_id: int) -> Optional[models.Tag]:
        """
        Get a tag by its ID.

        Args:
            db: Database session
            tag_id: ID of the tag

        Returns:
            Tag model instance or None if not found
        """
        return db.query(models.Tag).filter(models.Tag.id == tag_id).first()

    @staticmethod
    def add_tag_to_note(
        db: Session,
        note_id: int,
        tag_name: str,
        owner_id: int
    ) -> models.Tag:
        """
        Add a tag to a note (creates tag if doesn't exist).

        Args:
            db: Database session
            note_id: ID of the note
            tag_name: Name of the tag to add
            owner_id: ID of the note owner

        Returns:
            Tag model instance

        Raises:
            ValueError: If note not found or not owned by user
            HTTPException: On database errors
        """
        note = db.query(models.Note).filter(
            models.Note.id == note_id,
            models.Note.owner_id == owner_id
        ).first()

        if not note:
            raise ValueError(f"Note {note_id} not found or not owned by user {owner_id}")

        tag = TagService.get_or_create_tag(db, tag_name, owner_id)

        # Add relationship if not exists
        if tag not in note.tags:
            note.tags.append(tag)
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                logger.exception(f"Error adding tag '{tag_name}' to note {note_id}: {e}")
                raise HTTPException(status_code=500, detail="Failed to add tag to note")

        return tag

    @staticmethod
    def remove_tag_from_note(
        db: Session,
        note_id: int,
        tag_id: int,
        owner_id: int
    ) -> bool:
        """
        Remove a tag from a note.

        Args:
            db: Database session
            note_id: ID of the note
            tag_id: ID of the tag to remove
            owner_id: ID of the note owner

        Returns:
            True if tag was removed, False if note/tag not found

        Raises:
            HTTPException: On database errors
        """
        note = db.query(models.Note).filter(
            models.Note.id == note_id,
            models.Note.owner_id == owner_id
        ).first()

        if not note:
            return False

        tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()

        if tag and tag in note.tags:
            note.tags.remove(tag)
            try:
                db.commit()
                return True
            except Exception as e:
                db.rollback()
                logger.exception(f"Error removing tag {tag_id} from note {note_id}: {e}")
                raise HTTPException(status_code=500, detail="Failed to remove tag from note")

        return False

    @staticmethod
    def add_tag_to_image(
        db: Session,
        image_id: int,
        tag_name: str,
        owner_id: int
    ) -> models.Tag:
        """
        Add a tag to an image (creates tag if doesn't exist).

        Args:
            db: Database session
            image_id: ID of the image
            tag_name: Name of the tag to add
            owner_id: ID of the image owner

        Returns:
            Tag model instance

        Raises:
            ValueError: If image not found or not owned by user
            HTTPException: On database errors
        """
        image = db.query(models.Image).filter(
            models.Image.id == image_id,
            models.Image.owner_id == owner_id
        ).first()

        if not image:
            raise ValueError(f"Image {image_id} not found or not owned by user {owner_id}")

        tag = TagService.get_or_create_tag(db, tag_name, owner_id)

        # Add relationship if not exists
        if tag not in image.tags:
            image.tags.append(tag)
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                logger.exception(f"Error adding tag '{tag_name}' to image {image_id}: {e}")
                raise HTTPException(status_code=500, detail="Failed to add tag to image")

        return tag

    @staticmethod
    def remove_tag_from_image(
        db: Session,
        image_id: int,
        tag_id: int,
        owner_id: int
    ) -> bool:
        """
        Remove a tag from an image.

        Args:
            db: Database session
            image_id: ID of the image
            tag_id: ID of the tag to remove
            owner_id: ID of the image owner

        Returns:
            True if tag was removed, False if image/tag not found

        Raises:
            HTTPException: On database errors
        """
        image = db.query(models.Image).filter(
            models.Image.id == image_id,
            models.Image.owner_id == owner_id
        ).first()

        if not image:
            return False

        tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()

        if tag and tag in image.tags:
            image.tags.remove(tag)
            try:
                db.commit()
                return True
            except Exception as e:
                db.rollback()
                logger.exception(f"Error removing tag {tag_id} from image {image_id}: {e}")
                raise HTTPException(status_code=500, detail="Failed to remove tag from image")

        return False


__all__ = ["TagService"]
