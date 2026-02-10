"""
Documents Feature - Review & Approval Endpoints

POST /documents/{id}/approve - Approve suggestions, create summary note
POST /documents/{id}/reject - Skip review, mark completed
PUT /documents/{id}/suggestions - Edit suggestions before approval
POST /documents/{id}/extract-to-note - Append extracted text to summary note
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
import logging

from core.database import get_db
from core.auth import get_current_active_user
from core import exceptions
import models

from features.documents import schemas
from features.documents.service import DocumentService
from features.documents.services.approval import DocumentApprovalService

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/documents/{doc_id}/approve",
    response_model=schemas.ReviewApprovalResponse,
)
@limiter.limit("20/minute")
async def approve_document(
    request: Request,
    doc_id: int,
    approval: schemas.ReviewApprovalRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Approve AI suggestions and create a summary note.

    The user can select which tags/wikilinks to keep and edit the summary.
    Creates a Note linked to this document.
    """
    doc = DocumentService.get_document(db, doc_id, current_user.id)
    if not doc:
        raise exceptions.NotFoundException(f"Document {doc_id} not found")

    if doc.ai_analysis_status not in ("needs_review", "completed"):
        raise exceptions.ValidationException(
            f"Document must be in 'needs_review' status. Current: {doc.ai_analysis_status}"
        )

    try:
        result = DocumentApprovalService.approve_and_create_note(
            db=db,
            document=doc,
            owner_id=current_user.id,
            approved_tags=approval.approved_tags,
            approved_wikilinks=approval.approved_wikilinks,
            summary_title=approval.summary_title,
            summary_content=approval.summary_content,
        )
        return schemas.ReviewApprovalResponse(
            message="Document approved. Summary note created.",
            document_id=doc_id,
            note_id=result["note_id"],
            tags_applied=result["tags_applied"],
            status="completed",
        )
    except Exception as e:
        logger.error(f"Approval failed for doc {doc_id}: {e}", exc_info=True)
        raise exceptions.ProcessingException(f"Failed to approve: {e}")


@router.post("/documents/{doc_id}/reject")
@limiter.limit("20/minute")
async def reject_document(
    request: Request,
    doc_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Skip review and mark document as completed without creating a note."""
    doc = DocumentService.get_document(db, doc_id, current_user.id)
    if not doc:
        raise exceptions.NotFoundException(f"Document {doc_id} not found")

    doc.ai_analysis_status = "completed"
    db.commit()

    return {"message": "Review skipped", "document_id": doc_id, "status": "completed"}


@router.put(
    "/documents/{doc_id}/suggestions",
    response_model=schemas.DocumentResponse,
)
async def update_suggestions(
    doc_id: int,
    update: schemas.SuggestionsUpdateRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Edit AI suggestions before approval."""
    doc = DocumentService.get_document(db, doc_id, current_user.id)
    if not doc:
        raise exceptions.NotFoundException(f"Document {doc_id} not found")

    if update.suggested_tags is not None:
        doc.suggested_tags = update.suggested_tags
    if update.suggested_wikilinks is not None:
        doc.suggested_wikilinks = update.suggested_wikilinks
    if update.ai_summary is not None:
        doc.ai_summary = update.ai_summary

    db.commit()
    db.refresh(doc)

    return schemas.DocumentResponse.model_validate(doc)


@router.post(
    "/documents/{doc_id}/extract-to-note",
    response_model=schemas.ExtractTextToNoteResponse,
)
@limiter.limit("10/minute")
async def extract_text_to_note(
    request: Request,
    doc_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Append the full extracted text to the document's summary note."""
    doc = DocumentService.get_document(db, doc_id, current_user.id)
    if not doc:
        raise exceptions.NotFoundException(f"Document {doc_id} not found")

    if not doc.summary_note_id:
        raise exceptions.ValidationException(
            "Document has no summary note. Approve the document first."
        )

    if not doc.extracted_text or not doc.extracted_text.strip():
        raise exceptions.ValidationException("No extracted text available.")

    note = db.query(models.Note).filter(
        models.Note.id == doc.summary_note_id,
        models.Note.owner_id == current_user.id,
    ).first()
    if not note:
        raise exceptions.NotFoundException("Summary note not found")

    text = doc.extracted_text.strip()
    section = f"\n\n---\n## Full Extracted Text\n\n{text}"
    note.content = (note.content or "") + section
    doc.text_appended_to_note = True
    db.commit()

    return schemas.ExtractTextToNoteResponse(
        message="Extracted text appended to note",
        document_id=doc_id,
        note_id=note.id,
        chars_appended=len(text),
    )
