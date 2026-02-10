"""Brain feature - Training and adapter endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_user
from models import User

from .schemas import (
    AdapterResponse,
    AdapterListResponse,
    TriggerTrainingRequest,
    TriggerTrainingResponse,
)
from .models import (
    TrainingSample,
    BrainAdapter,
)
from .services import LoRATrainer, TrainingConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brain", tags=["brain"])


# ============================================
# Training Endpoints
# ============================================

@router.post("/train", response_model=TriggerTrainingResponse)
async def trigger_training(
    request: TriggerTrainingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Trigger brain training (async Celery task).

    Note: Full implementation in Phase 5.
    """
    from .tasks import train_brain_task

    # Check if already training
    training = (
        db.query(BrainAdapter)
        .filter(
            BrainAdapter.owner_id == user.id,
            BrainAdapter.status == "training"
        )
        .first()
    )

    if training:
        raise HTTPException(
            status_code=409,
            detail="Training already in progress"
        )

    # Check for training samples
    samples_count = (
        db.query(TrainingSample)
        .filter(
            TrainingSample.owner_id == user.id,
            TrainingSample.is_trained == "pending"
        )
        .count()
    )

    if samples_count == 0:
        raise HTTPException(
            status_code=400,
            detail="No training samples available. Run indexing first."
        )

    # Create adapter record
    trainer = LoRATrainer(db, user.id)
    config = TrainingConfig(
        base_model=request.base_model,
        lora_r=request.lora_r,
        lora_alpha=request.lora_alpha,
        epochs=request.epochs,
        learning_rate=request.learning_rate
    )
    adapter = trainer.create_adapter_record(config)

    # Trigger Celery task
    task = train_brain_task.delay(user.id, adapter.id)

    return TriggerTrainingResponse(
        task_id=task.id,
        status="started",
        adapter_version=adapter.version,
        message=f"Training started for adapter v{adapter.version}"
    )


# ============================================
# Adapter Endpoints
# ============================================

@router.get("/adapters", response_model=AdapterListResponse)
async def list_adapters(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all brain adapter versions."""
    adapters = (
        db.query(BrainAdapter)
        .filter(BrainAdapter.owner_id == user.id)
        .order_by(BrainAdapter.version.desc())
        .all()
    )

    active_adapter = next((a for a in adapters if a.is_active), None)

    return AdapterListResponse(
        adapters=[AdapterResponse.model_validate(a) for a in adapters],
        active_version=active_adapter.version if active_adapter else None
    )


@router.post("/adapters/{version}/activate")
async def activate_adapter(
    version: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Activate a specific adapter version."""
    trainer = LoRATrainer(db, user.id)

    if trainer.activate_adapter(version):
        return {"status": "activated", "version": version}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Adapter version {version} not found or not ready"
        )


@router.delete("/adapters/{version}")
async def delete_adapter(
    version: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Delete an adapter version."""
    adapter = (
        db.query(BrainAdapter)
        .filter(
            BrainAdapter.owner_id == user.id,
            BrainAdapter.version == version
        )
        .first()
    )

    if not adapter:
        raise HTTPException(status_code=404, detail="Adapter not found")

    if adapter.is_active:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete active adapter"
        )

    db.delete(adapter)
    db.commit()

    return {"status": "deleted", "version": version}
