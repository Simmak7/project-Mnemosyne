"""
System Feature - API Router

FastAPI endpoints for system operations:
- GET / - Root endpoint (API info)
- GET /health - Health check for all services
- GET /system/stuck-tasks - View items stuck in processing
- GET /models - List available AI models
- GET /models/config - Get current model configuration
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core import config
from core.database import get_db
from core.auth import get_current_user_optional, get_current_user
from core.models_registry import (
    get_all_models, get_all_models_with_status, get_model_info,
    get_models_for_use_case, ModelUseCase, is_model_available
)
from features.system import service
from features.system import schemas

logger = logging.getLogger(__name__)

router = APIRouter(tags=["System"])


@router.get("/", response_model=schemas.RootResponse)
async def read_root():
    """
    Root endpoint - API information.

    Returns basic API information including version and status.
    No authentication required.
    """
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to AI Notes Notetaker Backend!",
        "version": config.API_VERSION,
        "status": "running"
    }


@router.get("/health", response_model=schemas.HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Checks the health of all system components:
    - Ollama AI service
    - PostgreSQL database
    - Upload directory
    - Redis (Celery backend)

    Returns:
        - status: 'healthy', 'degraded', or 'unhealthy'
        - components: Dictionary of component statuses

    Status definitions:
        - healthy: All critical components operational
        - degraded: Non-critical components unavailable (e.g., Ollama)
        - unhealthy: Critical components unavailable (e.g., database)

    No authentication required - used for container health checks.
    """
    system_status = service.get_system_status()

    logger.info(f"Health check: {system_status['status']}")
    return system_status


@router.get("/system/stuck-tasks")
async def get_stuck_tasks(
    current_user=Depends(get_current_user),
):
    """
    View items currently stuck in 'processing' status.

    Returns images and documents that have been in 'processing' state
    longer than the recovery threshold (10 minutes). These items are
    candidates for automatic recovery by the periodic beat task.

    Requires authentication.
    """
    from features.system.tasks import get_stuck_tasks_summary
    summary = get_stuck_tasks_summary()
    logger.info(
        "Stuck tasks query: %d total stuck items",
        summary["total_stuck"],
    )
    return summary


@router.get("/system/gpu-info", response_model=schemas.GpuInfoResponse)
async def get_gpu_info(
    current_user=Depends(get_current_user),
):
    """
    Get GPU/VRAM diagnostic information from Ollama.

    Returns loaded models with their VRAM usage.
    If total_vram_bytes > 0, GPU acceleration is active.
    """
    info = service.get_gpu_info()
    logger.info(f"GPU info: gpu_detected={info.get('gpu_detected')}")
    return info


@router.get("/models", response_model=schemas.ModelsListResponse)
async def list_models(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """
    List all available AI models (local + cloud).

    Returns models with their capabilities, recommended use cases,
    and current configuration. Cloud models show as available when
    the user has a valid API key for the provider.
    """
    # Get user's cloud providers for availability check
    user_cloud_providers = set()
    if current_user:
        from features.settings.api_keys_service import get_user_api_keys_summary
        keys = get_user_api_keys_summary(db, current_user.id)
        user_cloud_providers = {k["provider"] for k in keys if k.get("is_valid", True)}

    models_with_status = get_all_models_with_status(user_cloud_providers)
    models_response = [
        schemas.ModelInfoResponse(**m) for m in models_with_status
    ]

    # Check user's vision model preference first, then fall back to feature flags
    current_vision = None
    if current_user:
        from models import UserPreferences
        prefs = db.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()
        if prefs and getattr(prefs, "vision_model", None):
            current_vision = prefs.vision_model

    if not current_vision:
        if getattr(config, "USE_NEW_MODEL", False) and getattr(config, "NEW_MODEL_ROLLOUT_PERCENT", 0) >= 100:
            current_vision = getattr(config, "OLLAMA_MODEL_NEW", "qwen2.5vl:7b-q4_K_M")
        else:
            current_vision = getattr(config, "OLLAMA_MODEL_OLD", "llama3.2-vision:11b")

    logger.info(f"Models list requested, returning {len(models_response)} models")
    return schemas.ModelsListResponse(
        models=models_response,
        current_rag_model=config.RAG_MODEL,
        current_brain_model=config.BRAIN_MODEL,
        current_nexus_model=config.RAG_MODEL,
        current_vision_model=current_vision,
    )


@router.get("/models/config", response_model=schemas.ModelConfigResponse)
async def get_model_config():
    """
    Get current model configuration.

    Returns the currently configured RAG and Brain models with their info.

    No authentication required.
    """
    rag_info = get_model_info(config.RAG_MODEL)
    brain_info = get_model_info(config.BRAIN_MODEL)

    rag_response = None
    if rag_info:
        rag_response = schemas.ModelInfoResponse(
            id=rag_info.id,
            name=rag_info.name,
            description=rag_info.description,
            size_gb=rag_info.size_gb,
            parameters=rag_info.parameters,
            category=rag_info.category.value,
            use_cases=[uc.value for uc in rag_info.use_cases],
            context_length=rag_info.context_length,
            features=rag_info.features,
            recommended_for=rag_info.recommended_for,
            is_default_rag=rag_info.is_default_rag,
            is_default_brain=rag_info.is_default_brain,
        )

    brain_response = None
    if brain_info:
        brain_response = schemas.ModelInfoResponse(
            id=brain_info.id,
            name=brain_info.name,
            description=brain_info.description,
            size_gb=brain_info.size_gb,
            parameters=brain_info.parameters,
            category=brain_info.category.value,
            use_cases=[uc.value for uc in brain_info.use_cases],
            context_length=brain_info.context_length,
            features=brain_info.features,
            recommended_for=brain_info.recommended_for,
            is_default_rag=brain_info.is_default_rag,
            is_default_brain=brain_info.is_default_brain,
        )

    logger.info(f"Model config requested: RAG={config.RAG_MODEL}, Brain={config.BRAIN_MODEL}")
    return schemas.ModelConfigResponse(
        rag_model=config.RAG_MODEL,
        brain_model=config.BRAIN_MODEL,
        rag_model_info=rag_response,
        brain_model_info=brain_response,
    )
