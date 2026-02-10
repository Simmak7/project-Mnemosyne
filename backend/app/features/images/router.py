"""
Images Feature - API Router

FastAPI endpoints for image upload, processing, and management.
Combines sub-routers: upload, crud, status, search.
"""

from fastapi import APIRouter

# Import sub-routers
from features.images.router_upload import router as upload_router
from features.images.router_crud import router as crud_router
from features.images.router_status import router as status_router
from features.images.router_search import router as search_router


def get_images_router() -> APIRouter:
    """Get the combined images router with all endpoints."""
    combined = APIRouter()

    # Include all sub-routers (they share the "Image Processing" tag)
    combined.include_router(upload_router)
    combined.include_router(crud_router)
    combined.include_router(status_router)
    combined.include_router(search_router)

    return combined


# Default export for backward compatibility
router = get_images_router()
