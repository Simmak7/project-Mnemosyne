"""Brain feature - Status endpoints."""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_user
from models import User

from .schemas import BrainStatusResponse
from .models import (
    TrainingSample,
    CondensedFact,
    BrainAdapter,
    IndexingRun,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brain", tags=["brain"])


@router.get("/status", response_model=BrainStatusResponse)
async def get_brain_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get current status of user's AI brain."""
    # Get active adapter
    active_adapter = (
        db.query(BrainAdapter)
        .filter(
            BrainAdapter.owner_id == user.id,
            BrainAdapter.is_active == True
        )
        .first()
    )

    # Count facts and samples
    facts_count = (
        db.query(CondensedFact)
        .filter(CondensedFact.owner_id == user.id)
        .count()
    )

    samples_count = (
        db.query(TrainingSample)
        .filter(TrainingSample.owner_id == user.id)
        .count()
    )

    # Get last indexing run
    last_run = (
        db.query(IndexingRun)
        .filter(
            IndexingRun.owner_id == user.id,
            IndexingRun.status == "completed"
        )
        .order_by(IndexingRun.completed_at.desc())
        .first()
    )

    # Determine status
    if active_adapter:
        status = "ready"
    elif samples_count > 0:
        status = "indexed"
    else:
        status = "none"

    # Check if currently indexing
    running_index = (
        db.query(IndexingRun)
        .filter(
            IndexingRun.owner_id == user.id,
            IndexingRun.status == "running"
        )
        .first()
    )
    if running_index:
        status = "indexing"

    # Check if currently training
    training_adapter = (
        db.query(BrainAdapter)
        .filter(
            BrainAdapter.owner_id == user.id,
            BrainAdapter.status == "training"
        )
        .first()
    )
    if training_adapter:
        status = "training"

    return BrainStatusResponse(
        has_adapter=active_adapter is not None,
        active_version=active_adapter.version if active_adapter else None,
        base_model=active_adapter.base_model if active_adapter else None,
        status=status,
        notes_indexed=last_run.notes_processed if last_run else 0,
        images_indexed=last_run.images_processed if last_run else 0,
        samples_count=samples_count,
        facts_count=facts_count,
        last_indexed=last_run.completed_at if last_run else None,
        last_trained=active_adapter.training_completed_at if active_adapter else None,
    )
