"""
Notes Feature - API Router

FastAPI endpoints for note operations.
Split into logical groups: CRUD, Enhanced/Graph, Tags.
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
from features.notes import schemas
from features.notes.models import Note
from features.graph import service as graph_service  # Use graph feature service
import models  # For User model
import schemas as main_schemas  # For backward compatibility with Note schema

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Notes"])


# ============================================
# Basic CRUD Endpoints
# ============================================

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
        return {"status": "success", "message": "Note deleted successfully", "note_id": note_id}

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error deleting note {note_id}: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to delete note")


# ============================================
# Enhanced Notes / Knowledge Graph Endpoints
# ============================================

@router.get("/notes-enhanced/", response_model=List[main_schemas.NoteEnhanced])
async def get_notes_enhanced(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all notes with enhanced graph data (tags, wikilinks, backlinks, images)."""
    logger.debug(f"Fetching enhanced notes for user {current_user.username}, skip={skip}, limit={limit}")

    try:
        notes = db.query(Note).filter(
            Note.owner_id == current_user.id
        ).offset(skip).limit(limit).all()

        result = []
        for note in notes:
            linked_note_ids = graph_service.resolve_wikilinks(db, note.id, note.content, current_user.id)
            backlink_ids = graph_service.get_backlinks(db, note.id, current_user.id)
            image_ids = [img.id for img in note.images]

            result.append({
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "html_content": note.html_content,
                "slug": note.slug,
                "created_at": note.created_at,
                "updated_at": note.updated_at,
                "owner_id": note.owner_id,
                "tags": note.tags,
                "linked_notes": linked_note_ids,
                "backlinks": backlink_ids,
                "image_ids": image_ids,
                "is_favorite": note.is_favorite,
                "is_reviewed": note.is_reviewed,
                "is_trashed": note.is_trashed
            })

        logger.info(f"Retrieved {len(result)} enhanced notes for user {current_user.username}")
        return result

    except Exception as e:
        logger.error(f"Error fetching enhanced notes: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to retrieve enhanced notes")


@router.get("/notes/{note_id}/enhanced", response_model=main_schemas.NoteEnhanced)
async def get_note_enhanced(
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a single note with full graph relationships."""
    logger.debug(f"Enhanced note {note_id} requested by user {current_user.username}")

    try:
        note = service.get_note(db, note_id=note_id)
        if not note:
            logger.warning(f"Note {note_id} not found")
            raise exceptions.ResourceNotFoundException("Note", note_id)

        if note.owner_id != current_user.id:
            raise exceptions.AuthorizationException("Not authorized to access this note")

        linked_note_ids = graph_service.resolve_wikilinks(db, note.id, note.content, current_user.id)
        backlink_ids = graph_service.get_backlinks(db, note.id, current_user.id)
        image_ids = [img.id for img in note.images]

        return {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "html_content": note.html_content,
            "slug": note.slug,
            "created_at": note.created_at,
            "updated_at": note.updated_at,
            "owner_id": note.owner_id,
            "tags": note.tags,
            "linked_notes": linked_note_ids,
            "backlinks": backlink_ids,
            "image_ids": image_ids,
            "is_favorite": note.is_favorite,
            "is_reviewed": note.is_reviewed,
            "is_trashed": note.is_trashed
        }

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving enhanced note {note_id}: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to retrieve enhanced note")


@router.get("/notes/{note_id}/graph", response_model=main_schemas.GraphData)
async def get_note_graph(
    note_id: int,
    depth: int = 1,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get graph visualization data for a note."""
    logger.debug(f"Graph data requested for note {note_id} with depth {depth}")

    if depth < 1 or depth > 3:
        raise exceptions.ValidationException("Depth must be between 1 and 3")

    try:
        note = service.get_note(db, note_id=note_id)
        if not note:
            raise exceptions.ResourceNotFoundException("Note", note_id)

        if note.owner_id != current_user.id:
            raise exceptions.AuthorizationException("Not authorized to access this note")

        graph_data = graph_service.get_note_graph_data(db, note_id, current_user.id, depth)

        logger.info(f"Graph data retrieved: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges")
        return graph_data

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error generating graph data: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to generate graph data")


@router.get("/notes/{note_id}/backlinks")
@limiter.limit("30/minute")
async def get_note_backlinks(
    request: Request,
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all notes that link to this note (backlinks)."""
    logger.debug(f"Backlinks requested for note {note_id}")

    try:
        note = service.get_note(db, note_id=note_id)
        if not note:
            raise exceptions.ResourceNotFoundException("Note", note_id)

        if note.owner_id != current_user.id:
            raise exceptions.AuthorizationException("Not authorized to access this note")

        backlink_ids = graph_service.get_backlinks(db, note_id, current_user.id)

        backlink_notes = db.query(Note).filter(
            Note.id.in_(backlink_ids),
            Note.owner_id == current_user.id
        ).all()

        logger.info(f"Found {len(backlink_notes)} backlinks for note {note_id}")
        return [main_schemas.Note.model_validate(note) for note in backlink_notes]

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error fetching backlinks: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to fetch backlinks")


@router.get("/notes/orphaned/list")
async def get_orphaned_notes(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get notes with no wikilinks, backlinks, or tags (orphaned notes)."""
    logger.debug(f"Fetching orphaned notes for user {current_user.username}")

    try:
        orphaned_ids = graph_service.find_orphaned_notes(db, current_user.id)

        notes = db.query(Note).filter(
            Note.id.in_(orphaned_ids),
            Note.owner_id == current_user.id
        ).all()

        logger.info(f"Found {len(notes)} orphaned notes for user {current_user.username}")
        return [main_schemas.Note.model_validate(note) for note in notes]

    except Exception as e:
        logger.error(f"Error finding orphaned notes: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to find orphaned notes")


@router.get("/notes/most-linked/")
async def get_most_linked_notes(
    limit: int = 10,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get notes with the most backlinks (most referenced notes)."""
    logger.debug(f"Fetching most linked notes for user {current_user.username}")

    try:
        results = graph_service.get_most_linked_notes(db, current_user.id, limit)

        return [
            {
                "note_id": note_id,
                "title": title,
                "backlink_count": count
            }
            for note_id, title, count in results
        ]

    except Exception as e:
        logger.error(f"Error getting most linked notes: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to get most linked notes")


# ============================================
# Full Knowledge Graph - MOVED to features/graph/router.py
# The /graph/data endpoint is now handled by graph_router
# ============================================


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


# ============================================
# AI Enhancement Endpoints
# ============================================

@router.post("/notes/{note_id}/improve-title")
@limiter.limit("10/minute")
async def improve_note_title(
    request: Request,
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Use AI to generate an improved title for a note."""
    logger.info(f"AI title improvement requested for note {note_id}")

    try:
        note = service.get_note(db, note_id=note_id)
        if not note:
            raise exceptions.ResourceNotFoundException("Note", note_id)
        if note.owner_id != current_user.id:
            raise exceptions.AuthorizationException("Not authorized")

        from features.notes import ai_service
        improved = ai_service.improve_title(note.content or "", note.title)

        return {"original_title": note.title, "improved_title": improved}

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error improving title: {str(e)}", exc_info=True)
        raise exceptions.OllamaServiceException("Failed to improve title")


@router.post("/notes/{note_id}/summarize")
@limiter.limit("10/minute")
async def summarize_note(
    request: Request,
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Use AI to generate a summary of a note."""
    logger.info(f"AI summarization requested for note {note_id}")

    try:
        note = service.get_note(db, note_id=note_id)
        if not note:
            raise exceptions.ResourceNotFoundException("Note", note_id)
        if note.owner_id != current_user.id:
            raise exceptions.AuthorizationException("Not authorized")

        from features.notes import ai_service
        summary = ai_service.summarize_note(note.content or "", note.title)

        return {"title": note.title, "summary": summary}

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error summarizing note: {str(e)}", exc_info=True)
        raise exceptions.OllamaServiceException("Failed to summarize note")


@router.post("/notes/{note_id}/suggest-wikilinks")
@limiter.limit("10/minute")
async def suggest_note_wikilinks(
    request: Request,
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Use AI to suggest potential wikilink connections."""
    logger.info(f"AI wikilink suggestions requested for note {note_id}")

    try:
        note = service.get_note(db, note_id=note_id)
        if not note:
            raise exceptions.ResourceNotFoundException("Note", note_id)
        if note.owner_id != current_user.id:
            raise exceptions.AuthorizationException("Not authorized")

        from features.notes import ai_service
        suggestions = ai_service.suggest_wikilinks(
            db, note_id, note.content or "", note.title, current_user.id
        )

        return {"note_id": note_id, "suggestions": suggestions}

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error suggesting wikilinks: {str(e)}", exc_info=True)
        raise exceptions.OllamaServiceException("Failed to suggest wikilinks")


@router.post("/notes/{note_id}/enhance")
@limiter.limit("5/minute")
async def enhance_note_all(
    request: Request,
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Run all AI enhancements on a note (title, summary, wikilinks)."""
    logger.info(f"Full AI enhancement requested for note {note_id}")

    try:
        note = service.get_note(db, note_id=note_id)
        if not note:
            raise exceptions.ResourceNotFoundException("Note", note_id)
        if note.owner_id != current_user.id:
            raise exceptions.AuthorizationException("Not authorized")

        from features.notes import ai_service
        results = ai_service.enhance_note(
            db, note_id, note.content or "", note.title, current_user.id
        )

        return {
            "note_id": note_id,
            "original_title": note.title,
            **results
        }

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error enhancing note: {str(e)}", exc_info=True)
        raise exceptions.OllamaServiceException("Failed to enhance note")


@router.post("/notes/{note_id}/regenerate")
@limiter.limit("5/minute")
async def regenerate_note_from_source(
    request: Request,
    note_id: int,
    apply: bool = False,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Regenerate note content from its linked source image.

    Re-analyzes the linked image using AI and generates fresh content.
    Use apply=true to automatically update the note with the new content.
    """
    logger.info(f"Regenerate from source requested for note {note_id}")

    try:
        from features.notes import ai_service

        # Get regenerated content
        result = ai_service.regenerate_from_source(
            db=db,
            note_id=note_id,
            owner_id=current_user.id
        )

        # Optionally apply changes to the note
        if apply:
            note = service.update_note(
                db=db,
                note_id=note_id,
                owner_id=current_user.id,
                title=result["new_title"],
                content=result["new_content"]
            )
            return {
                "note_id": note_id,
                "applied": True,
                "new_title": result["new_title"],
                "new_content": result["new_content"],
                "image_id": result["image_id"]
            }

        return {
            "note_id": note_id,
            "applied": False,
            "new_title": result["new_title"],
            "new_content": result["new_content"],
            "image_id": result["image_id"]
        }

    except ValueError as e:
        logger.warning(f"Regenerate failed: {str(e)}")
        raise exceptions.ValidationException(str(e))
    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating note: {str(e)}", exc_info=True)
        raise exceptions.OllamaServiceException("Failed to regenerate from source")
