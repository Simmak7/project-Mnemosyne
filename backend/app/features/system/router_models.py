"""
Model Management Router - Pull, delete, and check updates for Ollama models.

Endpoints:
- POST /models/pull - SSE stream for downloading models
- DELETE /models/{model_name} - Delete a model from Ollama
- GET /models/updates - Check for available model updates
"""

import logging
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.auth import get_current_user
from features.system.model_management import pull_model_stream, delete_model
from features.system.update_checker import check_all_updates
from features.system.schemas import ModelUpdatesResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["Model Management"])


class ModelPullRequest(BaseModel):
    """Request schema for model pull."""
    model: str


@router.post("/pull")
async def pull_model(
    request: ModelPullRequest,
    current_user=Depends(get_current_user),
):
    """
    Pull/download a model from Ollama registry.

    Returns an SSE stream with download progress events.
    Each event contains: status, total, completed, percent.

    When complete, the final event has status='success'.
    """
    model_name = request.model.strip()
    if not model_name:
        return {"status": "error", "error": "Model name is required"}

    logger.info(f"User {current_user.username} pulling model: {model_name}")

    return StreamingResponse(
        pull_model_stream(model_name),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/updates", response_model=ModelUpdatesResponse)
async def get_model_updates(
    force: bool = Query(False, description="Bypass cache and re-check"),
    current_user=Depends(get_current_user),
):
    """Check all installed Ollama models for available updates."""
    updates = check_all_updates(force=force)
    return ModelUpdatesResponse(updates=updates, checked_count=len(updates))


@router.delete("/{model_name:path}")
async def remove_model(
    model_name: str,
    current_user=Depends(get_current_user),
):
    """
    Delete a model from Ollama.

    The model_name can include colons (e.g., qwen3-vl:7b).
    """
    logger.info(f"User {current_user.username} deleting model: {model_name}")
    result = delete_model(model_name)
    return result
