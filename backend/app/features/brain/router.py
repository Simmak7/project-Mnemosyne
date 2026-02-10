"""Brain Feature - API Router

API endpoints for AI brain indexing, training, and inference.
Combines sub-routers: status, indexing, training, inference.
"""

from fastapi import APIRouter

# Import sub-routers
from features.brain.router_status import router as status_router
from features.brain.router_indexing import router as indexing_router
from features.brain.router_training import router as training_router
from features.brain.router_inference import router as inference_router


def get_brain_router() -> APIRouter:
    """Get the combined brain router with all endpoints."""
    combined = APIRouter()

    # Include all sub-routers (they share the "brain" tag and prefix)
    combined.include_router(status_router)
    combined.include_router(indexing_router)
    combined.include_router(training_router)
    combined.include_router(inference_router)

    return combined


# Default export for backward compatibility
router = get_brain_router()
