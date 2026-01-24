"""
Graph Feature - API Router

FastAPI endpoints for knowledge graph operations.
Includes wikilink resolution, backlinks, and full graph visualization.
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

from features.graph import service
from features.graph import schemas
import models
import schemas as main_schemas  # For backward compatibility

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Graph"])


# ============================================
# Full Knowledge Graph
# ============================================

@router.get("/graph/data")
@limiter.limit("30/minute")
async def get_full_graph_data(
    request: Request,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get full knowledge graph data (all notes, tags, images) in react-force-graph format.

    Returns nodes and links for visualization:
    - Nodes: notes (blue), tags (orange), images (green)
    - Links: wikilinks (note→note), tag (note→tag), image (note→image)
    """
    logger.debug(f"Full graph data requested for user {current_user.username}")

    try:
        graph_data = service.get_full_graph_data(db, current_user.id)
        logger.info(f"Full graph data retrieved: {len(graph_data['nodes'])} nodes, {len(graph_data['links'])} links")
        return graph_data

    except Exception as e:
        logger.error(f"Error generating full graph data: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to generate graph data")


# ============================================
# Note-Specific Graph Endpoints
# ============================================

@router.get("/notes/{note_id}/graph", response_model=main_schemas.GraphData)
async def get_note_graph(
    note_id: int,
    depth: int = 1,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get graph visualization data for a single note.

    Args:
        note_id: The note to build the graph around
        depth: How many connection levels to include (1-3)

    Returns:
        Graph data with nodes and edges
    """
    logger.debug(f"Graph data requested for note {note_id} with depth {depth}")

    if depth < 1 or depth > 3:
        raise exceptions.ValidationException("Depth must be between 1 and 3")

    try:
        # Verify note exists and belongs to user
        note = db.query(models.Note).filter(
            models.Note.id == note_id,
            models.Note.owner_id == current_user.id
        ).first()

        if not note:
            raise exceptions.ResourceNotFoundException("Note", note_id)

        graph_data = service.get_note_graph_data(db, note_id, current_user.id, depth)

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
    """
    Get all notes that link TO this note (backlinks).

    Returns list of notes containing [[wikilinks]] to this note.
    """
    logger.debug(f"Backlinks requested for note {note_id}")

    try:
        # Verify note exists and belongs to user
        note = db.query(models.Note).filter(
            models.Note.id == note_id,
            models.Note.owner_id == current_user.id
        ).first()

        if not note:
            raise exceptions.ResourceNotFoundException("Note", note_id)

        backlink_ids = service.get_backlinks(db, note_id, current_user.id)

        backlink_notes = db.query(models.Note).filter(
            models.Note.id.in_(backlink_ids),
            models.Note.owner_id == current_user.id
        ).all()

        logger.info(f"Found {len(backlink_notes)} backlinks for note {note_id}")
        return [main_schemas.Note.model_validate(note) for note in backlink_notes]

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error fetching backlinks: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to fetch backlinks")


# ============================================
# Orphaned & Most Linked Notes
# ============================================

@router.get("/notes/orphaned/list")
async def get_orphaned_notes(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get notes with no wikilinks, backlinks, or tags (orphaned notes).

    These are notes that are disconnected from the knowledge graph.
    """
    logger.debug(f"Fetching orphaned notes for user {current_user.username}")

    try:
        orphaned_ids = service.find_orphaned_notes(db, current_user.id)

        notes = db.query(models.Note).filter(
            models.Note.id.in_(orphaned_ids),
            models.Note.owner_id == current_user.id
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
    """
    Get notes with the most backlinks (most referenced notes).

    These are the hub notes in your knowledge graph.
    """
    logger.debug(f"Fetching most linked notes for user {current_user.username}")

    try:
        results = service.get_most_linked_notes(db, current_user.id, limit)

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
# Wikilink Operations
# ============================================

@router.post("/wikilinks/resolve")
async def resolve_wikilinks(
    content: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Resolve [[wikilinks]] in content to note IDs.

    Useful for validating wikilinks before saving.
    """
    try:
        from features.graph.wikilink_parser import extract_wikilinks, validate_wikilink_syntax

        # Validate syntax
        errors = validate_wikilink_syntax(content)
        if errors:
            return {
                "valid": False,
                "errors": [{"line": line, "message": msg} for line, msg in errors],
                "resolved_links": []
            }

        # Extract and resolve wikilinks
        wikilinks = extract_wikilinks(content)
        resolved = []

        for wikilink in wikilinks:
            note = service.get_or_create_note_by_wikilink(
                db, wikilink, current_user.id, auto_create=False
            )
            resolved.append({
                "raw_link": wikilink,
                "exists": note is not None,
                "note_id": note.id if note else None,
                "title": note.title if note else wikilink
            })

        return {
            "valid": True,
            "errors": [],
            "resolved_links": resolved
        }

    except Exception as e:
        logger.error(f"Error resolving wikilinks: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to resolve wikilinks")


@router.post("/wikilinks/create-stub")
async def create_stub_note(
    title: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a stub note from a wikilink target.

    If the note already exists, returns the existing note.
    """
    try:
        note = service.get_or_create_note_by_wikilink(
            db, title, current_user.id, auto_create=True
        )

        return {
            "note_id": note.id,
            "title": note.title,
            "slug": note.slug,
            "created": note.content.endswith("*This note was auto-created from a wikilink.*")
        }

    except Exception as e:
        logger.error(f"Error creating stub note: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to create stub note")
