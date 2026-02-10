"""Search feature - Embedding management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from core.database import get_db
from core.auth import get_current_user
from models import User, Note

from features.search import schemas
from features.search.logic.semantic import get_embedding_coverage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/embeddings/coverage", response_model=schemas.EmbeddingCoverageResponse)
async def get_embedding_coverage_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics about embedding coverage.

    Returns the number of notes with/without embeddings and coverage percentage.
    Useful for monitoring embedding generation progress.

    **Rate limit:** 30 requests/minute
    """
    try:
        stats = get_embedding_coverage(db, current_user.id)
        return schemas.EmbeddingCoverageResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get embedding coverage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notes/{note_id}/regenerate-embedding", response_model=schemas.EmbeddingRegenerateResponse)
async def regenerate_note_embedding_endpoint(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger embedding regeneration for a note.

    Useful for fixing corrupted embeddings or updating after significant changes.

    **Rate limit:** 10 requests/minute
    """
    # Import here to avoid circular imports
    from features.search.tasks import generate_note_embedding_task

    # Verify note exists
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id
    ).first()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    try:
        task = generate_note_embedding_task.delay(note_id)
        logger.info(f"Queued embedding regeneration for note {note_id}: task_id={task.id}")

        return schemas.EmbeddingRegenerateResponse(
            status="queued",
            note_id=note_id,
            task_id=task.id,
            message="Embedding generation queued. Check task status for progress."
        )

    except Exception as e:
        logger.error(f"Failed to queue embedding task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue embedding generation: {str(e)}"
        )
