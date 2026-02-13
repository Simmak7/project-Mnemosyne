"""
NEXUS Admin Endpoints

POST /nexus/consolidate           - Trigger consolidation
GET  /nexus/suggestions           - Get pending link suggestions
POST /nexus/suggestions/{id}/accept  - Accept a link suggestion
POST /nexus/suggestions/{id}/dismiss - Dismiss a link suggestion
GET  /nexus/cache/stats           - Navigation cache statistics
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.database import get_db
from core.auth import get_current_user
from models import User
from features.nexus import schemas
from features.nexus.models import NexusLinkSuggestion, NexusNavigationCache
from features.nexus.services.missing_links import get_pending_suggestions
from features.nexus.tasks import run_consolidation_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nexus", tags=["nexus-admin"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/consolidate")
@limiter.limit("2/minute")
async def trigger_consolidation(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger NEXUS consolidation (async via Celery)."""
    task = run_consolidation_task.delay(current_user.id, force=True)
    return {
        "status": "queued",
        "task_id": str(task.id),
        "message": "Consolidation started. This may take a few minutes.",
    }


@router.get("/suggestions")
@limiter.limit("30/minute")
async def list_suggestions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
):
    """Get pending link suggestions."""
    suggestions = get_pending_suggestions(db, current_user.id, limit)
    return {"suggestions": suggestions, "count": len(suggestions)}


@router.post("/suggestions/{suggestion_id}/accept")
@limiter.limit("20/minute")
async def accept_suggestion(
    request: Request,
    suggestion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept a link suggestion (creates wikilink)."""
    suggestion = db.query(NexusLinkSuggestion).filter(
        NexusLinkSuggestion.id == suggestion_id,
        NexusLinkSuggestion.owner_id == current_user.id,
    ).first()

    if not suggestion:
        raise HTTPException(404, "Suggestion not found")

    if suggestion.status != "pending":
        raise HTTPException(400, f"Suggestion already {suggestion.status}")

    # Create wikilink
    from sqlalchemy import text
    try:
        db.execute(text("""
            INSERT INTO note_links (source_note_id, target_note_id)
            VALUES (:source, :target)
            ON CONFLICT DO NOTHING
        """), {
            "source": suggestion.source_note_id,
            "target": suggestion.target_note_id,
        })
        suggestion.status = "accepted"
        db.commit()
        return {"status": "accepted", "wikilink_created": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Failed to create wikilink: {str(e)}")


@router.post("/suggestions/{suggestion_id}/dismiss")
@limiter.limit("20/minute")
async def dismiss_suggestion(
    request: Request,
    suggestion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dismiss a link suggestion."""
    suggestion = db.query(NexusLinkSuggestion).filter(
        NexusLinkSuggestion.id == suggestion_id,
        NexusLinkSuggestion.owner_id == current_user.id,
    ).first()

    if not suggestion:
        raise HTTPException(404, "Suggestion not found")

    suggestion.status = "dismissed"
    db.commit()
    return {"status": "dismissed"}


@router.get("/cache/stats")
@limiter.limit("30/minute")
async def cache_stats(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get navigation cache statistics."""
    caches = db.query(NexusNavigationCache).filter(
        NexusNavigationCache.owner_id == current_user.id,
    ).all()

    stats = {}
    for cache in caches:
        stats[cache.cache_type] = {
            "version": cache.version,
            "content_length": len(cache.content),
            "updated_at": cache.updated_at.isoformat() if cache.updated_at else None,
        }

    return {"caches": stats, "ready": len(stats) >= 2}


@router.get("/health")
async def nexus_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check NEXUS system health and mode availability."""
    cache = db.query(NexusNavigationCache).filter(
        NexusNavigationCache.owner_id == current_user.id,
    ).first()

    return schemas.NexusHealthResponse(
        status="healthy",
        navigation_cache_ready=cache is not None,
        mode_availability={
            "fast": True,
            "standard": cache is not None,
            "deep": cache is not None,
        },
    )
