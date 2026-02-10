"""Brain feature - Indexing, samples, and facts endpoints."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.database import get_db
from core.auth import get_current_user
from models import User

from .schemas import (
    TrainingSampleResponse,
    TrainingSampleListResponse,
    CondensedFactResponse,
    IndexingRunResponse,
    TriggerIndexingResponse,
)
from .models import (
    TrainingSample,
    CondensedFact,
    IndexingRun,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brain", tags=["brain"])


# ============================================
# Indexing Endpoints
# ============================================

@router.post("/index", response_model=TriggerIndexingResponse)
async def trigger_indexing(
    background_tasks: BackgroundTasks,
    full_reindex: bool = Query(False, description="Reprocess all content"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Trigger brain indexing (async Celery task)."""
    from .tasks import index_brain_task

    # Check if already indexing
    running = (
        db.query(IndexingRun)
        .filter(
            IndexingRun.owner_id == user.id,
            IndexingRun.status == "running"
        )
        .first()
    )

    if running:
        raise HTTPException(
            status_code=409,
            detail="Indexing already in progress"
        )

    # Trigger Celery task
    task = index_brain_task.delay(user.id, full_reindex)

    return TriggerIndexingResponse(
        task_id=task.id,
        status="started",
        message="Brain indexing started"
    )


@router.get("/index/history", response_model=List[IndexingRunResponse])
async def get_indexing_history(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get history of indexing runs."""
    runs = (
        db.query(IndexingRun)
        .filter(IndexingRun.owner_id == user.id)
        .order_by(IndexingRun.started_at.desc())
        .limit(limit)
        .all()
    )

    return [IndexingRunResponse.model_validate(run) for run in runs]


# ============================================
# Training Samples Endpoints
# ============================================

@router.get("/samples", response_model=TrainingSampleListResponse)
async def list_training_samples(
    sample_type: Optional[str] = None,
    memory_type: Optional[str] = None,
    is_trained: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List training samples with filtering."""
    query = db.query(TrainingSample).filter(TrainingSample.owner_id == user.id)

    if sample_type:
        query = query.filter(TrainingSample.sample_type == sample_type)
    if memory_type:
        query = query.filter(TrainingSample.memory_type == memory_type)
    if is_trained:
        query = query.filter(TrainingSample.is_trained == is_trained)

    total = query.count()
    samples = query.order_by(TrainingSample.created_at.desc()).offset(offset).limit(limit).all()

    # Get counts by type
    by_type = dict(
        db.query(TrainingSample.sample_type, func.count(TrainingSample.id))
        .filter(TrainingSample.owner_id == user.id)
        .group_by(TrainingSample.sample_type)
        .all()
    )

    by_memory_type = dict(
        db.query(TrainingSample.memory_type, func.count(TrainingSample.id))
        .filter(TrainingSample.owner_id == user.id)
        .group_by(TrainingSample.memory_type)
        .all()
    )

    return TrainingSampleListResponse(
        samples=[TrainingSampleResponse.model_validate(s) for s in samples],
        total=total,
        by_type=by_type,
        by_memory_type={str(k): v for k, v in by_memory_type.items()}
    )


@router.delete("/samples/{sample_id}")
async def delete_training_sample(
    sample_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Delete a training sample."""
    sample = (
        db.query(TrainingSample)
        .filter(
            TrainingSample.id == sample_id,
            TrainingSample.owner_id == user.id
        )
        .first()
    )

    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    db.delete(sample)
    db.commit()

    return {"status": "deleted", "id": sample_id}


# ============================================
# Condensed Facts Endpoints
# ============================================

@router.get("/facts", response_model=List[CondensedFactResponse])
async def list_condensed_facts(
    concept: Optional[str] = None,
    fact_type: Optional[str] = None,
    memory_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List condensed facts with filtering."""
    query = db.query(CondensedFact).filter(CondensedFact.owner_id == user.id)

    if concept:
        query = query.filter(CondensedFact.concept.ilike(f"%{concept}%"))
    if fact_type:
        query = query.filter(CondensedFact.fact_type == fact_type)
    if memory_type:
        query = query.filter(CondensedFact.memory_type == memory_type)

    facts = (
        query
        .order_by(CondensedFact.recurrence.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [CondensedFactResponse.model_validate(f) for f in facts]
