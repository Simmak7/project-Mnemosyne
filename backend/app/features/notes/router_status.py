"""
Notes Feature - Status & Tags Endpoints

Endpoints for note status (favorites, trash, reviewed) and tag management.
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.auth import get_current_active_user
from core import exceptions

from features.notes import service
import models
import schemas as main_schemas

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Notes"])


# ============================================
# Note Tags (note-specific tag operations)
# ============================================

@router.post("/notes/{note_id}/tags/{tag_name}")
async def add_tag_to_note(
    note_id: int,
    tag_name: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a tag to a note (creates tag if it doesn't exist)."""
    logger.info(f"Adding tag '{tag_name}' to note {note_id} for user {current_user.username}")

    try:
        import crud
        tag = crud.add_tag_to_note(db, note_id=note_id, tag_name=tag_name, owner_id=current_user.id)
        logger.info(f"Tag '{tag.name}' added to note {note_id}")
        return {"status": "success", "tag_id": tag.id, "tag_name": tag.name}
    except ValueError as e:
        logger.warning(f"Failed to add tag to note: {str(e)}")
        raise exceptions.ResourceNotFoundException("Note", note_id)
    except Exception as e:
        logger.error(f"Error adding tag to note: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to add tag to note")


@router.delete("/notes/{note_id}/tags/{tag_id}")
async def remove_tag_from_note(
    note_id: int,
    tag_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a tag from a note."""
    logger.info(f"Removing tag {tag_id} from note {note_id} for user {current_user.username}")

    try:
        import crud
        success = crud.remove_tag_from_note(db, note_id=note_id, tag_id=tag_id, owner_id=current_user.id)

        if success:
            logger.info(f"Tag {tag_id} removed from note {note_id}")
            return {"status": "success"}
        else:
            logger.warning(f"Failed to remove tag {tag_id} from note {note_id}")
            raise exceptions.ResourceNotFoundException("Note or Tag", f"{note_id}/{tag_id}")
    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error removing tag from note: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to remove tag from note")


# ============================================
# Favorites and Trash Endpoints
# ============================================

@router.post("/notes/{note_id}/favorite", response_model=main_schemas.Note)
async def toggle_note_favorite(
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Toggle the favorite status of a note."""
    logger.info(f"Toggling favorite for note {note_id} by user {current_user.username}")

    try:
        note = service.toggle_favorite(db, note_id=note_id, owner_id=current_user.id)
        if not note:
            raise exceptions.ResourceNotFoundException("Note", note_id)

        logger.info(f"Note {note_id} favorite status: {note.is_favorite}")
        return main_schemas.Note.model_validate(note)

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error toggling favorite: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to toggle favorite")


@router.post("/notes/{note_id}/trash", response_model=main_schemas.Note)
async def move_note_to_trash(
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Move a note to trash (soft delete)."""
    logger.info(f"Moving note {note_id} to trash by user {current_user.username}")

    try:
        note = service.move_to_trash(db, note_id=note_id, owner_id=current_user.id)
        if not note:
            raise exceptions.ResourceNotFoundException("Note", note_id)

        logger.info(f"Note {note_id} moved to trash")
        return main_schemas.Note.model_validate(note)

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error moving note to trash: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to move note to trash")


@router.post("/notes/{note_id}/restore", response_model=main_schemas.Note)
async def restore_note_from_trash(
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Restore a note from trash."""
    logger.info(f"Restoring note {note_id} from trash by user {current_user.username}")

    try:
        note = service.restore_from_trash(db, note_id=note_id, owner_id=current_user.id)
        if not note:
            raise exceptions.ResourceNotFoundException("Note", note_id)

        logger.info(f"Note {note_id} restored from trash")
        return main_schemas.Note.model_validate(note)

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error restoring note from trash: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to restore note from trash")


@router.get("/notes/favorites/", response_model=List[main_schemas.Note])
async def get_favorite_notes(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all favorite notes for the current user."""
    logger.debug(f"Fetching favorite notes for user {current_user.username}")

    try:
        notes = service.get_favorites(db, owner_id=current_user.id, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(notes)} favorite notes for user {current_user.username}")
        return [main_schemas.Note.model_validate(note) for note in notes]

    except Exception as e:
        logger.error(f"Error fetching favorite notes: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to retrieve favorite notes")


@router.get("/notes/trash/", response_model=List[main_schemas.Note])
async def get_trashed_notes(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all trashed notes for the current user."""
    logger.debug(f"Fetching trashed notes for user {current_user.username}")

    try:
        notes = service.get_trashed(db, owner_id=current_user.id, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(notes)} trashed notes for user {current_user.username}")
        return [main_schemas.Note.model_validate(note) for note in notes]

    except Exception as e:
        logger.error(f"Error fetching trashed notes: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to retrieve trashed notes")


@router.delete("/notes/{note_id}/permanent")
async def permanently_delete_note(
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Permanently delete a note (only works for trashed notes)."""
    logger.info(f"Permanently deleting note {note_id} by user {current_user.username}")

    try:
        success = service.permanent_delete(db, note_id=note_id, owner_id=current_user.id)
        if not success:
            raise exceptions.ResourceNotFoundException("Trashed Note", note_id)

        logger.info(f"Note {note_id} permanently deleted")
        return {"status": "success", "message": "Note permanently deleted", "note_id": note_id}

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error permanently deleting note: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to permanently delete note")


@router.post("/notes/{note_id}/reviewed", response_model=main_schemas.Note)
async def toggle_note_reviewed(
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Toggle the reviewed status of a note."""
    logger.info(f"Toggling reviewed for note {note_id} by user {current_user.username}")

    try:
        note = service.toggle_reviewed(db, note_id=note_id, owner_id=current_user.id)
        if not note:
            raise exceptions.ResourceNotFoundException("Note", note_id)

        logger.info(f"Note {note_id} reviewed status: {note.is_reviewed}")
        return main_schemas.Note.model_validate(note)

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error toggling reviewed: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to toggle reviewed")
