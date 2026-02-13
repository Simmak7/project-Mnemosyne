"""
Notes Feature - Basic CRUD Endpoints

Create, Read, Update, Delete operations for notes.
"""

import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.auth import get_current_active_user
from core import exceptions
from slowapi import Limiter
from slowapi.util import get_remote_address

from features.notes import service
import models
import schemas as main_schemas

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Notes"])


@router.get("/notes/", response_model=List[main_schemas.Note])
async def get_notes(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all notes for the current user."""
    logger.debug(f"Fetching notes for user {current_user.username}, skip={skip}, limit={limit}")

    try:
        notes = service.get_notes_by_user(db, owner_id=current_user.id, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(notes)} notes for user {current_user.username}")
        return [main_schemas.Note.model_validate(note) for note in notes]
    except Exception as e:
        logger.error(f"Error fetching notes for user {current_user.username}: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to retrieve notes")


@router.get("/notes/{note_id}", response_model=main_schemas.Note)
async def get_note(
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific note by ID."""
    logger.debug(f"Note {note_id} requested by user {current_user.username}")

    try:
        note = service.get_note(db, note_id=note_id)
        if not note:
            logger.warning(f"Note {note_id} not found")
            raise exceptions.ResourceNotFoundException("Note", note_id)

        if note.owner_id != current_user.id:
            logger.warning(f"User {current_user.username} attempted to access note {note_id} owned by user {note.owner_id}")
            raise exceptions.AuthorizationException("Not authorized to access this note")

        logger.debug(f"Serving note {note_id} to user {current_user.username}")
        return main_schemas.Note.model_validate(note)

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving note {note_id}: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to retrieve note")


@router.get("/notes/{note_id}/source-document")
async def get_source_document(
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get the source document for a note (if it was created from a document)."""
    from models import Document

    doc = db.query(Document).filter(
        Document.summary_note_id == note_id,
        Document.owner_id == current_user.id,
        Document.is_trashed == False,
    ).first()

    if not doc:
        return {"source_document": None}

    return {
        "source_document": {
            "id": doc.id,
            "filename": doc.filename,
            "display_name": doc.display_name,
            "page_count": doc.page_count,
            "document_type": doc.document_type,
        }
    }


@router.post("/notes/", response_model=main_schemas.Note)
@limiter.limit("30/minute")
async def create_note(
    request: Request,
    note: main_schemas.NoteCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new note."""
    logger.info(f"Note creation request from user {current_user.username}")

    try:
        if not note.title or not note.title.strip():
            raise exceptions.ValidationException("Note title cannot be empty")

        if not note.content:
            note.content = ""

        db_note = service.create_note(
            db=db,
            title=note.title.strip(),
            content=note.content,
            owner_id=current_user.id,
            html_content=note.html_content
        )

        logger.info(f"Note created successfully: ID {db_note.id} for user {current_user.username}")

        # Incrementally update brain for this new note
        try:
            from features.mnemosyne_brain.tasks import incremental_brain_update_task
            incremental_brain_update_task.delay(current_user.id, db_note.id, "created")
        except Exception:
            pass  # Non-critical

        return main_schemas.Note.model_validate(db_note)

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error creating note: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to create note")


@router.put("/notes/{note_id}", response_model=main_schemas.Note)
@limiter.limit("30/minute")
async def update_note(
    request: Request,
    note_id: int,
    note: main_schemas.NoteCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing note."""
    logger.info(f"Note update request for note {note_id} from user {current_user.username}")

    try:
        if not note.title or not note.title.strip():
            raise exceptions.ValidationException("Note title cannot be empty")

        db_note = service.update_note(
            db=db,
            note_id=note_id,
            title=note.title.strip(),
            content=note.content,
            owner_id=current_user.id,
            html_content=note.html_content
        )

        if not db_note:
            logger.warning(f"Note {note_id} not found or not authorized for user {current_user.username}")
            raise exceptions.ResourceNotFoundException("Note", note_id)

        logger.info(f"Note {note_id} updated successfully by user {current_user.username}")

        # Incrementally update brain for this edited note
        try:
            from features.mnemosyne_brain.tasks import incremental_brain_update_task
            incremental_brain_update_task.delay(current_user.id, note_id, "updated")
        except Exception:
            pass  # Non-critical

        return main_schemas.Note.model_validate(db_note)

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error updating note {note_id}: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to update note")


@router.delete("/notes/{note_id}")
@limiter.limit("30/minute")
async def delete_note(
    request: Request,
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a note."""
    logger.info(f"Note delete request for note {note_id} from user {current_user.username}")

    try:
        success = service.delete_note(db=db, note_id=note_id, owner_id=current_user.id)

        if not success:
            logger.warning(f"Note {note_id} not found or not authorized for user {current_user.username}")
            raise exceptions.ResourceNotFoundException("Note", note_id)

        logger.info(f"Note {note_id} deleted successfully by user {current_user.username}")

        # Incrementally update brain for this deleted note
        try:
            from features.mnemosyne_brain.tasks import incremental_brain_update_task
            incremental_brain_update_task.delay(current_user.id, note_id, "deleted")
        except Exception:
            pass  # Non-critical

        return {"status": "success", "message": "Note deleted successfully", "note_id": note_id}

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error deleting note {note_id}: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to delete note")
