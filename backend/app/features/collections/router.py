"""
Note Collections - API Router

FastAPI endpoints for note collection operations.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.auth import get_current_active_user
from core import exceptions
import models

from . import service
from . import schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collections", tags=["Collections"])


@router.get("/", response_model=List[schemas.CollectionResponse])
async def get_collections(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all note collections for the current user."""
    logger.debug(f"Fetching collections for user {current_user.username}")
    collections = service.get_collections(db, owner_id=current_user.id)
    logger.info(f"Retrieved {len(collections)} collections for user {current_user.username}")
    return collections


@router.get("/{collection_id}", response_model=schemas.CollectionWithNotes)
async def get_collection(
    collection_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a single collection with its notes."""
    collection = service.get_collection(db, collection_id, current_user.id)
    if not collection:
        raise exceptions.ResourceNotFoundException("Collection", collection_id)
    return collection


@router.post("/", response_model=schemas.CollectionResponse)
async def create_collection(
    data: schemas.CollectionCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new note collection."""
    logger.info(f"Creating collection '{data.name}' for user {current_user.username}")
    collection = service.create_collection(
        db,
        owner_id=current_user.id,
        name=data.name,
        description=data.description,
        icon=data.icon,
        color=data.color
    )
    return {
        **collection.__dict__,
        "note_count": 0
    }


@router.put("/{collection_id}", response_model=schemas.CollectionResponse)
async def update_collection(
    collection_id: int,
    data: schemas.CollectionUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a collection."""
    collection = service.update_collection(
        db,
        collection_id=collection_id,
        owner_id=current_user.id,
        name=data.name,
        description=data.description,
        icon=data.icon,
        color=data.color
    )
    if not collection:
        raise exceptions.ResourceNotFoundException("Collection", collection_id)

    # Get note count
    note_count = len(collection.notes) if collection.notes else 0

    return {
        **collection.__dict__,
        "note_count": note_count
    }


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a collection (notes are NOT deleted)."""
    success = service.delete_collection(db, collection_id, current_user.id)
    if not success:
        raise exceptions.ResourceNotFoundException("Collection", collection_id)
    return {"status": "success", "message": "Collection deleted"}


@router.post("/{collection_id}/notes")
async def add_note_to_collection(
    collection_id: int,
    data: schemas.AddNoteRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a note to a collection."""
    success = service.add_note_to_collection(
        db, collection_id, data.note_id, current_user.id
    )
    if not success:
        raise exceptions.ResourceNotFoundException("Collection or Note", collection_id)
    return {"status": "success", "message": "Note added to collection"}


@router.delete("/{collection_id}/notes/{note_id}")
async def remove_note_from_collection(
    collection_id: int,
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a note from a collection."""
    success = service.remove_note_from_collection(
        db, collection_id, note_id, current_user.id
    )
    if not success:
        raise exceptions.ResourceNotFoundException("Collection or Note", collection_id)
    return {"status": "success", "message": "Note removed from collection"}


@router.get("/note/{note_id}", response_model=List[dict])
async def get_note_collections(
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all collections that contain a specific note."""
    return service.get_note_collections(db, note_id, current_user.id)
