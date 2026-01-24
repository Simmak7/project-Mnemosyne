"""
Notes Feature - Business Logic / Service Layer

CRUD operations and business logic for notes.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from features.notes.models import Note, NoteTag
from wikilink_parser import create_slug, extract_hashtags

logger = logging.getLogger(__name__)


def get_note(db: Session, note_id: int) -> Optional[Note]:
    """Get a note by ID."""
    return db.query(Note).filter(Note.id == note_id).first()


def get_notes_by_user(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Note]:
    """Get all non-trashed notes for a user with pagination."""
    return db.query(Note).filter(
        Note.owner_id == owner_id,
        Note.is_trashed == False
    ).offset(skip).limit(limit).all()


def create_note(
    db: Session,
    title: str,
    content: str,
    owner_id: Optional[int] = None,
    html_content: Optional[str] = None
) -> Note:
    """
    Create a new note with auto-generated slug and extract tags.

    Args:
        db: Database session
        title: Note title
        content: Note content (may contain #hashtags and [[wikilinks]])
        owner_id: Owner user ID
        html_content: Rich HTML content for rendering (optional)

    Returns:
        Created Note object
    """
    from tasks_embeddings import generate_note_embedding_task
    from crud import get_or_create_tag

    # Generate unique slug
    base_slug = create_slug(title)
    slug = base_slug
    counter = 2

    # Check for existing slug and append suffix if needed
    while db.query(Note).filter(
        Note.slug == slug,
        Note.owner_id == owner_id
    ).first() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1

    db_note = Note(
        title=title,
        content=content,
        html_content=html_content,
        slug=slug,
        owner_id=owner_id,
        is_standalone=True
    )
    db.add(db_note)

    try:
        db.commit()
        db.refresh(db_note)
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating note '{title}': {e}")
        raise HTTPException(status_code=409, detail="Note with this slug already exists")
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error creating note '{title}': {e}")
        raise HTTPException(status_code=500, detail="Failed to create note")

    # Extract and add tags from content
    if content:
        hashtags = extract_hashtags(content)
        for tag_name in hashtags:
            try:
                tag = get_or_create_tag(db, tag_name, owner_id)
                if tag not in db_note.tags:
                    db_note.tags.append(tag)
            except Exception as e:
                logger.error(f"Error adding tag {tag_name} to note {db_note.id}: {e}", exc_info=True)

        if hashtags:
            try:
                db.commit()
                db.refresh(db_note)
            except Exception as e:
                db.rollback()
                logger.exception(f"Error committing tags for note {db_note.id}: {e}")

    # Trigger embedding generation (async, non-blocking)
    try:
        generate_note_embedding_task.delay(db_note.id)
    except Exception as e:
        logger.error(f"Failed to queue embedding generation for note {db_note.id}: {e}", exc_info=True)

    return db_note


def update_note(
    db: Session,
    note_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    owner_id: Optional[int] = None,
    html_content: Optional[str] = None
) -> Optional[Note]:
    """
    Update a note, regenerate slug if title changes, and extract tags.

    Args:
        db: Database session
        note_id: Note ID to update
        title: New title (optional)
        content: New content (optional)
        owner_id: Owner ID for authorization check
        html_content: Rich HTML content for rendering (optional)

    Returns:
        Updated Note or None if not found/authorized
    """
    from tasks_embeddings import generate_note_embedding_task
    from crud import get_or_create_tag

    note = db.query(Note).filter(Note.id == note_id).first()

    if not note:
        return None

    # Check ownership if owner_id provided
    if owner_id and note.owner_id != owner_id:
        return None

    # Track if content changed (for embedding regeneration)
    content_changed = False

    if title is not None and title != note.title:
        note.title = title

        # Generate unique slug for the new title
        base_slug = create_slug(title)
        slug = base_slug
        counter = 2

        # Check for existing slug (excluding current note)
        while db.query(Note).filter(
            Note.slug == slug,
            Note.owner_id == note.owner_id,
            Note.id != note_id
        ).first() is not None:
            slug = f"{base_slug}-{counter}"
            counter += 1

        note.slug = slug
        content_changed = True  # Title change affects embedding

    if content is not None:
        note.content = content
        content_changed = True

        # Extract and update tags from content
        hashtags = extract_hashtags(content)

        # Remove old tags that are no longer in content
        existing_tag_names = {tag.name for tag in note.tags}
        tags_to_remove = existing_tag_names - hashtags

        for tag_name in tags_to_remove:
            tag = next((t for t in note.tags if t.name == tag_name), None)
            if tag:
                note.tags.remove(tag)

        # Add new tags
        for tag_name in hashtags:
            if tag_name not in existing_tag_names:
                try:
                    tag = get_or_create_tag(db, tag_name, owner_id or note.owner_id)
                    note.tags.append(tag)
                except Exception as e:
                    logger.error(f"Error adding tag {tag_name} to note {note_id}: {e}", exc_info=True)

    # Always update html_content from request (allows clearing by sending null)
    # This is a PUT (full update), so we replace whatever was there
    note.html_content = html_content

    try:
        db.commit()
        db.refresh(note)
    except Exception as e:
        db.rollback()
        logger.exception(f"Error updating note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update note")

    # Trigger embedding regeneration if content changed (async, non-blocking)
    if content_changed:
        try:
            generate_note_embedding_task.delay(note_id)
        except Exception as e:
            logger.error(f"Failed to queue embedding generation for note {note_id}: {e}", exc_info=True)

    return note


def delete_note(db: Session, note_id: int, owner_id: Optional[int] = None) -> bool:
    """
    Delete a note.

    Args:
        db: Database session
        note_id: Note ID to delete
        owner_id: Owner ID for authorization check

    Returns:
        True if successful, False if not found or not authorized
    """
    note = db.query(Note).filter(Note.id == note_id).first()

    if not note:
        return False

    # Check ownership if owner_id provided
    if owner_id and note.owner_id != owner_id:
        return False

    db.delete(note)
    try:
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.exception(f"Error deleting note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete note")


def add_image_to_note(db: Session, image_id: int, note_id: int):
    """Link an image to a note."""
    from models import ImageNoteRelation

    db_relation = ImageNoteRelation(image_id=image_id, note_id=note_id)
    db.add(db_relation)
    try:
        db.commit()
        db.refresh(db_relation)
        return db_relation
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error linking image {image_id} to note {note_id}: {e}")
        raise HTTPException(status_code=409, detail="Image-note relationship already exists")
    except Exception as e:
        db.rollback()
        logger.exception(f"Error linking image {image_id} to note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to link image to note")


# ============================================
# Favorites and Trash Operations
# ============================================

def toggle_favorite(db: Session, note_id: int, owner_id: int) -> Optional[Note]:
    """Toggle the favorite status of a note."""
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == owner_id).first()
    if not note:
        return None

    note.is_favorite = not note.is_favorite
    try:
        db.commit()
        db.refresh(note)
        return note
    except Exception as e:
        db.rollback()
        logger.exception(f"Error toggling favorite for note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle favorite")


def move_to_trash(db: Session, note_id: int, owner_id: int) -> Optional[Note]:
    """Move a note to trash (soft delete)."""
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == owner_id).first()
    if not note:
        return None

    note.is_trashed = True
    note.trashed_at = datetime.now(timezone.utc)
    try:
        db.commit()
        db.refresh(note)
        return note
    except Exception as e:
        db.rollback()
        logger.exception(f"Error moving note {note_id} to trash: {e}")
        raise HTTPException(status_code=500, detail="Failed to move note to trash")


def restore_from_trash(db: Session, note_id: int, owner_id: int) -> Optional[Note]:
    """Restore a note from trash."""
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == owner_id).first()
    if not note:
        return None

    note.is_trashed = False
    note.trashed_at = None
    try:
        db.commit()
        db.refresh(note)
        return note
    except Exception as e:
        db.rollback()
        logger.exception(f"Error restoring note {note_id} from trash: {e}")
        raise HTTPException(status_code=500, detail="Failed to restore note")


def get_favorites(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Note]:
    """Get all favorite notes for a user."""
    return db.query(Note).filter(
        Note.owner_id == owner_id,
        Note.is_favorite == True,
        Note.is_trashed == False
    ).offset(skip).limit(limit).all()


def get_trashed(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Note]:
    """Get all trashed notes for a user."""
    return db.query(Note).filter(
        Note.owner_id == owner_id,
        Note.is_trashed == True
    ).offset(skip).limit(limit).all()


def permanent_delete(db: Session, note_id: int, owner_id: int) -> bool:
    """Permanently delete a note (only works for trashed notes)."""
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == owner_id,
        Note.is_trashed == True
    ).first()

    if not note:
        return False

    db.delete(note)
    try:
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.exception(f"Error permanently deleting note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete note")


def toggle_reviewed(db: Session, note_id: int, owner_id: int) -> Optional[Note]:
    """Toggle the reviewed status of a note."""
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == owner_id).first()
    if not note:
        return None

    note.is_reviewed = not note.is_reviewed
    try:
        db.commit()
        db.refresh(note)
        return note
    except Exception as e:
        db.rollback()
        logger.exception(f"Error toggling reviewed for note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle reviewed")
