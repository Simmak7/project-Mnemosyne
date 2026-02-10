"""
Documents Feature - CRUD Endpoints

GET /documents/ - List user's documents
GET /documents/{id} - Document detail
DELETE /documents/{id} - Trash document
GET /documents/{id}/file - Serve original PDF
GET /documents/{id}/thumbnail - Serve thumbnail
POST /documents/{id}/retry - Retry failed analysis
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import logging

from core.database import get_db
from core.auth import get_current_active_user
from core import exceptions
import models

from features.documents import schemas
from features.documents.service import DocumentService

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

router = APIRouter()


def _doc_to_response(doc) -> schemas.DocumentResponse:
    """Convert a Document model to response, adding computed fields."""
    resp = schemas.DocumentResponse.model_validate(doc)
    resp.extracted_text_length = len(doc.extracted_text) if doc.extracted_text else 0
    return resp


@router.get("/documents/", response_model=schemas.DocumentListResponse)
async def list_documents(
    request: Request,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "desc",
    collection_id: Optional[int] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List user's documents with optional status filter and sorting."""
    docs, total = DocumentService.get_documents_by_user(
        db, owner_id=current_user.id, status_filter=status,
        skip=skip, limit=limit, sort_by=sort_by, sort_order=sort_order,
        collection_id=collection_id,
    )
    return schemas.DocumentListResponse(
        documents=[_doc_to_response(d) for d in docs],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/documents/{doc_id}", response_model=schemas.DocumentResponse)
async def get_document(
    doc_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get document details."""
    doc = DocumentService.get_document(db, doc_id, current_user.id)
    if not doc:
        raise exceptions.NotFoundException(f"Document {doc_id} not found")
    return _doc_to_response(doc)


@router.delete("/documents/{doc_id}", response_model=schemas.DeleteResponse)
@limiter.limit("20/minute")
async def delete_document(
    request: Request,
    doc_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Move document to trash (soft delete)."""
    deleted = DocumentService.move_to_trash(db, doc_id, current_user.id)
    if not deleted:
        raise exceptions.NotFoundException(f"Document {doc_id} not found")
    return schemas.DeleteResponse(message="Document moved to trash", document_id=doc_id)


@router.get("/documents/{doc_id}/file")
async def serve_document_file(
    doc_id: int,
    inline: bool = False,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Serve the original PDF file. Use ?inline=true for in-browser preview."""
    doc = DocumentService.get_document(db, doc_id, current_user.id)
    if not doc:
        raise exceptions.NotFoundException(f"Document {doc_id} not found")
    if not DocumentService.file_exists(doc.filepath):
        raise exceptions.NotFoundException("Document file not found on disk")
    return FileResponse(
        doc.filepath,
        media_type="application/pdf",
        filename=doc.display_name or doc.filename,
        content_disposition_type="inline" if inline else "attachment",
    )


@router.get("/documents/{doc_id}/thumbnail")
async def serve_document_thumbnail(
    doc_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Serve document thumbnail image."""
    doc = DocumentService.get_document(db, doc_id, current_user.id)
    if not doc or not doc.thumbnail_path:
        raise exceptions.NotFoundException("Thumbnail not found")
    if not DocumentService.file_exists(doc.thumbnail_path):
        raise exceptions.NotFoundException("Thumbnail file not found on disk")
    return FileResponse(doc.thumbnail_path, media_type="image/jpeg")


@router.post("/documents/{doc_id}/retry", response_model=schemas.RetryResponse)
@limiter.limit("10/minute")
async def retry_document_analysis(
    request: Request,
    doc_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retry analysis for a failed document."""
    doc = DocumentService.get_document(db, doc_id, current_user.id)
    if not doc:
        raise exceptions.NotFoundException(f"Document {doc_id} not found")
    if not DocumentService.file_exists(doc.filepath):
        raise exceptions.NotFoundException("Document file not found on disk")

    DocumentService.update_analysis_status(db, doc_id, "queued", None)

    try:
        from features.documents.tasks import analyze_document_task

        task = analyze_document_task.delay(document_id=doc_id, filepath=doc.filepath)
        return schemas.RetryResponse(
            message="Document analysis retry queued",
            document_id=doc_id,
            task_id=task.id,
            analysis_status="queued",
        )
    except Exception as e:
        raise exceptions.ProcessingException(f"Failed to retry: {e}")
