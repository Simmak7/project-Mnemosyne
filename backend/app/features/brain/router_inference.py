"""Brain feature - Inference, storage, and cleanup endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_user
from models import User

from .schemas import (
    BrainGenerateRequest,
    BrainGenerateResponse,
    BrainChatRequest,
    BrainChatResponse,
    AdapterDiskUsageResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brain", tags=["brain"])


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


# ============================================
# Storage Endpoints
# ============================================

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
