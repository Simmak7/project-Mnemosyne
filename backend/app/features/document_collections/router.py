"""
Document Collections - API Router

FastAPI endpoints for document collection operations.
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

router = APIRouter(prefix="/document-collections", tags=["Document Collections"])


@router.get("/", response_model=List[schemas.CollectionResponse])
async def get_collections(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all document collections for the current user."""
    collections = service.get_collections(db, owner_id=current_user.id)
    return collections


@router.get("/document/{document_id}", response_model=List[dict])
async def get_document_collections(
    document_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all collections that contain a specific document."""
    return service.get_document_collections(db, document_id, current_user.id)


@router.get("/{collection_id}", response_model=schemas.CollectionWithDocuments)
async def get_collection(
    collection_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a single collection with its documents."""
    collection = service.get_collection(db, collection_id, current_user.id)
    if not collection:
        raise exceptions.ResourceNotFoundException("Document Collection", collection_id)
    return collection


@router.post("/", response_model=schemas.CollectionResponse)
async def create_collection(
    data: schemas.CollectionCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new document collection."""
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
        "document_count": 0
    }


@router.put("/{collection_id}", response_model=schemas.CollectionResponse)
async def update_collection(
    collection_id: int,
    data: schemas.CollectionUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a document collection."""
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
        raise exceptions.ResourceNotFoundException("Document Collection", collection_id)

    doc_count = len(collection.documents) if collection.documents else 0
    return {
        **collection.__dict__,
        "document_count": doc_count
    }


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a collection (documents are NOT deleted)."""
    success = service.delete_collection(db, collection_id, current_user.id)
    if not success:
        raise exceptions.ResourceNotFoundException("Document Collection", collection_id)
    return {"status": "success", "message": "Collection deleted"}


@router.post("/{collection_id}/documents")
async def add_document_to_collection(
    collection_id: int,
    data: schemas.AddDocumentRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a document to a collection."""
    success = service.add_document_to_collection(
        db, collection_id, data.document_id, current_user.id
    )
    if not success:
        raise exceptions.ResourceNotFoundException("Collection or Document", collection_id)
    return {"status": "success", "message": "Document added to collection"}


@router.delete("/{collection_id}/documents/{document_id}")
async def remove_document_from_collection(
    collection_id: int,
    document_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a document from a collection."""
    success = service.remove_document_from_collection(
        db, collection_id, document_id, current_user.id
    )
    if not success:
        raise exceptions.ResourceNotFoundException("Collection or Document", collection_id)
    return {"status": "success", "message": "Document removed from collection"}
