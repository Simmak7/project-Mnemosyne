"""
Notes Feature - API Router

FastAPI endpoints for note operations.
Combines sub-routers: CRUD, Graph, Status/Tags, AI.
"""

from fastapi import APIRouter

# Import sub-routers
from features.notes.router_crud import router as crud_router
from features.notes.router_graph import router as graph_router
from features.notes.router_status import router as status_router
from features.notes.router_ai import router as ai_router


def get_notes_router() -> APIRouter:
    """Get the combined notes router with all endpoints."""
    combined = APIRouter()

    # Include all sub-routers (they share the "Notes" tag)
    combined.include_router(crud_router)
    combined.include_router(graph_router)
    combined.include_router(status_router)
    combined.include_router(ai_router)

    return combined


# Default export for backward compatibility
router = get_notes_router()
