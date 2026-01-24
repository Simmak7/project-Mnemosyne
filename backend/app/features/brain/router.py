"""Brain feature API endpoints.

Endpoints:
- GET /brain/status - Current brain status
- POST /brain/index - Trigger indexing
- GET /brain/index/{task_id} - Get indexing progress
- GET /brain/samples - List training samples
- GET /brain/facts - List condensed facts
- POST /brain/train - Trigger training (Phase 5)
- GET /brain/train/{task_id} - Get training progress
- GET /brain/adapters - List adapter versions
- POST /brain/adapters/{version}/activate - Activate adapter
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.database import get_db
from core.auth import get_current_user
from models import User

from .schemas import (
    BrainStatusResponse,
    AdapterResponse,
    AdapterListResponse,
    TrainingSampleResponse,
    TrainingSampleListResponse,
    CondensedFactResponse,
    IndexingRunResponse,
    TriggerIndexingResponse,
    TriggerTrainingRequest,
    TriggerTrainingResponse,
    BrainGenerateRequest,
    BrainGenerateResponse,
    BrainChatRequest,
    BrainChatResponse,
    AdapterDiskUsageResponse,
)
from .models import (
    TrainingSample,
    CondensedFact,
    BrainAdapter,
    IndexingRun,
    MemoryType,
)
from .services import BrainIndexer, LoRATrainer, TrainingConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brain", tags=["brain"])


# ============================================
# Status Endpoints
# ============================================

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


# ============================================
# Training Endpoints (Phase 5 Stubs)
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


# ============================================
# Inference Endpoints
# ============================================

@router.post("/generate", response_model=BrainGenerateResponse)
async def generate_with_brain(
    request: BrainGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Generate text using the trained brain adapter.

    Requires an active adapter to be set.
    """
    from .services import BrainInference

    inference = BrainInference(db, user.id)

    # Check for active adapter
    adapter = inference.get_active_adapter()
    if not adapter:
        raise HTTPException(
            status_code=400,
            detail="No active adapter. Train your brain first."
        )

    result = inference.generate(
        prompt=request.prompt,
        max_length=request.max_length,
        temperature=request.temperature,
        top_p=request.top_p
    )

    if result is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate response"
        )

    return BrainGenerateResponse(
        text=result,
        adapter_version=inference.loaded_version,
        model_loaded=inference.is_loaded
    )


@router.post("/chat", response_model=BrainChatResponse)
async def chat_with_brain(
    request: BrainChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Chat with the trained brain adapter.

    Requires an active adapter to be set.
    """
    from .services import BrainInference

    inference = BrainInference(db, user.id)

    adapter = inference.get_active_adapter()
    if not adapter:
        raise HTTPException(
            status_code=400,
            detail="No active adapter. Train your brain first."
        )

    result = inference.chat(
        messages=request.messages,
        max_length=request.max_length,
        temperature=request.temperature
    )

    if result is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate response"
        )

    return BrainChatResponse(
        message=result,
        adapter_version=inference.loaded_version,
        model_loaded=inference.is_loaded
    )


@router.get("/storage", response_model=AdapterDiskUsageResponse)
async def get_storage_usage(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get disk usage statistics for adapter storage."""
    from .services import AdapterStorage

    storage = AdapterStorage(user.id)
    usage = storage.get_disk_usage()

    return AdapterDiskUsageResponse(**usage)


@router.post("/cleanup")
async def cleanup_adapters(
    keep_count: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Clean up old adapter versions, keeping the most recent N."""
    from .tasks import cleanup_old_adapters_task

    task = cleanup_old_adapters_task.delay(user.id, keep_count)

    return {
        "task_id": task.id,
        "message": f"Cleanup started, keeping {keep_count} versions"
    }
