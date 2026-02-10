"""
Mnemosyne Brain Management Router.

Endpoints for building brain, managing brain files, and checking status.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.database import get_db
from core.auth import get_current_user
from core import config
import models

from features.mnemosyne_brain.models.brain_file import BrainFile
from features.mnemosyne_brain.models.brain_build_log import BrainBuildLog
from features.mnemosyne_brain import schemas
from features.mnemosyne_brain.services.topic_generator import compute_content_hash
from features.mnemosyne_brain.services.topic_selector import (
    select_topics,
    _compute_keyword_score,
    _compute_embedding_score,
)

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/mnemosyne", tags=["mnemosyne-brain"])


# ============================================
# Brain Build Endpoints
# ============================================

@router.post("/build", response_model=schemas.BrainBuildStatusResponse)
@limiter.limit("5/minute")
async def trigger_brain_build(
    request: Request,
    body: schemas.BrainBuildRequest = schemas.BrainBuildRequest(),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Trigger a brain build (async via Celery)."""
    # Check if a build is already running
    running = (
        db.query(BrainBuildLog)
        .filter(
            BrainBuildLog.owner_id == current_user.id,
            BrainBuildLog.status == "running",
        )
        .first()
    )
    if running:
        return schemas.BrainBuildStatusResponse(
            build_id=running.id,
            build_type=running.build_type,
            status="running",
            progress_pct=running.progress_pct,
            current_step=running.current_step,
            notes_processed=running.notes_processed,
            started_at=running.started_at,
        )

    # Check note count
    min_notes = getattr(config, "BRAIN_MIN_NOTES", 3)
    note_count = (
        db.query(func.count(models.Note.id))
        .filter(
            models.Note.owner_id == current_user.id,
            models.Note.is_trashed == False,  # noqa: E712
        )
        .scalar()
    )
    if note_count < min_notes:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least {min_notes} notes to build brain (found {note_count})",
        )

    # Dispatch Celery task
    from features.mnemosyne_brain.tasks import build_brain_task
    build_type = "full" if body.full_rebuild else "partial"
    build_brain_task.delay(current_user.id, build_type)

    return schemas.BrainBuildStatusResponse(
        status="running",
        progress_pct=0,
        current_step="Queued",
        build_type=build_type,
    )


@router.get("/build/status", response_model=schemas.BrainBuildStatusResponse)
async def get_build_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Check current build progress."""
    latest = (
        db.query(BrainBuildLog)
        .filter(BrainBuildLog.owner_id == current_user.id)
        .order_by(BrainBuildLog.started_at.desc())
        .first()
    )
    if not latest:
        return schemas.BrainBuildStatusResponse(status="none")

    return schemas.BrainBuildStatusResponse(
        build_id=latest.id,
        build_type=latest.build_type,
        status=latest.status,
        progress_pct=latest.progress_pct,
        current_step=latest.current_step,
        notes_processed=latest.notes_processed,
        communities_detected=latest.communities_detected,
        topic_files_generated=latest.topic_files_generated,
        error_message=latest.error_message,
        started_at=latest.started_at,
        completed_at=latest.completed_at,
    )


@router.get("/build/history", response_model=List[schemas.BrainBuildHistoryItem])
async def get_build_history(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List past builds."""
    builds = (
        db.query(BrainBuildLog)
        .filter(BrainBuildLog.owner_id == current_user.id)
        .order_by(BrainBuildLog.started_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return builds


# ============================================
# Brain File Endpoints
# ============================================

@router.get("/files", response_model=List[schemas.BrainFileSummary])
async def list_brain_files(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List all brain files (without full content)."""
    files = (
        db.query(BrainFile)
        .filter(BrainFile.owner_id == current_user.id)
        .order_by(BrainFile.file_type, BrainFile.file_key)
        .all()
    )
    return files


@router.get("/files/{file_key}", response_model=schemas.BrainFileResponse)
async def get_brain_file(
    file_key: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get a brain file by key."""
    brain_file = (
        db.query(BrainFile)
        .filter(
            BrainFile.owner_id == current_user.id,
            BrainFile.file_key == file_key,
        )
        .first()
    )
    if not brain_file:
        raise HTTPException(status_code=404, detail=f"Brain file '{file_key}' not found")
    return brain_file


@router.put("/files/{file_key}", response_model=schemas.BrainFileResponse)
@limiter.limit("20/minute")
async def update_brain_file(
    request: Request,
    file_key: str,
    body: schemas.BrainFileUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update a brain file's content (user edit)."""
    brain_file = (
        db.query(BrainFile)
        .filter(
            BrainFile.owner_id == current_user.id,
            BrainFile.file_key == file_key,
        )
        .first()
    )
    if not brain_file:
        raise HTTPException(status_code=404, detail=f"Brain file '{file_key}' not found")

    brain_file.content = body.content
    brain_file.content_hash = compute_content_hash(body.content)
    brain_file.is_user_edited = True
    brain_file.token_count_approx = len(body.content) // 4

    db.commit()
    db.refresh(brain_file)

    logger.info(f"Brain file '{file_key}' updated by user {current_user.id}")
    return brain_file


# ============================================
# Brain Status Endpoint
# ============================================

@router.get("/status", response_model=schemas.BrainStatusResponse)
async def get_brain_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Overall brain status."""
    files = (
        db.query(BrainFile)
        .filter(BrainFile.owner_id == current_user.id)
        .all()
    )

    note_count = (
        db.query(func.count(models.Note.id))
        .filter(
            models.Note.owner_id == current_user.id,
            models.Note.is_trashed == False,  # noqa: E712
        )
        .scalar()
    )

    running_build = (
        db.query(BrainBuildLog)
        .filter(
            BrainBuildLog.owner_id == current_user.id,
            BrainBuildLog.status == "running",
        )
        .first()
    )

    last_build = (
        db.query(BrainBuildLog)
        .filter(
            BrainBuildLog.owner_id == current_user.id,
            BrainBuildLog.status == "completed",
        )
        .order_by(BrainBuildLog.completed_at.desc())
        .first()
    )

    core_files = [f for f in files if f.file_type == "core"]
    topic_files = [f for f in files if f.file_type == "topic"]
    stale_files = [f for f in files if f.is_stale]
    total_tokens = sum(f.token_count_approx or 0 for f in files)

    min_notes = getattr(config, "BRAIN_MIN_NOTES", 3)

    return schemas.BrainStatusResponse(
        has_brain=len(files) > 0,
        is_ready=len(core_files) >= 3 and not running_build,
        is_building=running_build is not None,
        is_stale=len(stale_files) > 0,
        total_files=len(files),
        core_files=len(core_files),
        topic_files=len(topic_files),
        stale_files=len(stale_files),
        total_tokens=total_tokens,
        last_build_at=last_build.completed_at if last_build else None,
        notes_count=note_count,
        min_notes_required=min_notes,
    )


# ============================================
# Topic Selection Endpoints (Phase 4)
# ============================================

def _get_user_preferences(db: Session, user_id: int) -> models.UserPreferences:
    """Get or create user preferences."""
    prefs = db.query(models.UserPreferences).filter(
        models.UserPreferences.user_id == user_id
    ).first()
    if not prefs:
        prefs = models.UserPreferences(user_id=user_id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.get("/topics/scores", response_model=schemas.TopicScoresResponse)
async def get_topic_scores(
    query: Optional[str] = Query(None, description="Query to score topics against"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get all topics with relevance scores for a query.

    Returns topics sorted by score, indicating which would be auto-selected.
    """
    # Get all topic files
    topics = (
        db.query(BrainFile)
        .filter(
            BrainFile.owner_id == current_user.id,
            BrainFile.file_type == "topic",
        )
        .all()
    )

    # Get pinned topics
    prefs = _get_user_preferences(db, current_user.id)
    pinned = prefs.pinned_brain_topics or []

    # Generate embedding if query provided
    query_embedding = None
    if query:
        try:
            from embeddings import generate_embedding
            query_embedding = generate_embedding(query)
        except Exception:
            pass

    # Score each topic
    scored_topics = []
    query_lower = (query or "").lower()
    query_words = set(query_lower.split()) if query else set()

    for topic in topics:
        if query:
            keyword_score = _compute_keyword_score(query_words, query_lower, topic)
            embedding_score = _compute_embedding_score(query_embedding, topic)
            score = (keyword_score * 0.3) + (embedding_score * 0.7)
        else:
            score = 0.0

        scored_topics.append(schemas.TopicScoreItem(
            file_key=topic.file_key,
            title=topic.title or topic.file_key,
            token_count=topic.token_count_approx or len(topic.content or "") // 4,
            score=round(score, 3),
            is_auto_selected=score >= 0.05 if query else False,
            is_pinned=topic.file_key in pinned,
        ))

    # Sort by score (pinned first, then by score)
    scored_topics.sort(key=lambda x: (not x.is_pinned, -x.score))

    # Calculate token budget info
    core_tokens = getattr(config, "BRAIN_CORE_TOKEN_BUDGET", 2500)
    max_context = getattr(config, "BRAIN_MAX_CONTEXT_TOKENS", 6000)
    topic_budget = max_context - core_tokens - 500  # 500 for prompt overhead

    return schemas.TopicScoresResponse(
        topics=scored_topics,
        pinned=pinned,
        token_budget=topic_budget,
        core_tokens_used=core_tokens,
    )


@router.post("/topics/pin", response_model=schemas.PinnedTopicsResponse)
@limiter.limit("30/minute")
async def pin_topic(
    request: Request,
    body: schemas.PinTopicRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Pin or unpin a topic for always-loading."""
    prefs = _get_user_preferences(db, current_user.id)

    pinned = set(prefs.pinned_brain_topics or [])

    if body.pin:
        # Verify topic exists
        topic = (
            db.query(BrainFile)
            .filter(
                BrainFile.owner_id == current_user.id,
                BrainFile.file_key == body.topic_key,
            )
            .first()
        )
        if not topic:
            raise HTTPException(status_code=404, detail=f"Topic '{body.topic_key}' not found")
        pinned.add(body.topic_key)
    else:
        pinned.discard(body.topic_key)

    prefs.pinned_brain_topics = list(pinned)
    db.commit()

    logger.info(f"User {current_user.id} {'pinned' if body.pin else 'unpinned'} topic '{body.topic_key}'")
    return schemas.PinnedTopicsResponse(pinned=list(pinned))
