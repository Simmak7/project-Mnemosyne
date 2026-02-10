"""
Notes Feature - Enhanced Notes & Knowledge Graph Endpoints

Endpoints for notes with graph relationships: wikilinks, backlinks, etc.
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
from features.notes.models import Note
from features.graph import service as graph_service
import models
import schemas as main_schemas

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Notes"])


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
            Note.owner_id == current_user.id,
            Note.is_trashed == False
        ).order_by(Note.created_at.desc()).offset(skip).limit(limit).all()

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
                "is_trashed": note.is_trashed,
                "is_standalone": getattr(note, 'is_standalone', True),
                "source": getattr(note, 'source', 'manual'),
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
            "is_trashed": note.is_trashed,
            "is_standalone": getattr(note, 'is_standalone', True),
            "source": getattr(note, 'source', 'manual'),
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
