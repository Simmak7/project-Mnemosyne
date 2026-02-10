"""Search Feature - API Router

API endpoints for full-text search, semantic search, and embedding management.
Combines sub-routers: fulltext, semantic, embeddings.
"""

from fastapi import APIRouter

# Import sub-routers
from features.search.router_fulltext import router as fulltext_router
from features.search.router_semantic import router as semantic_router
from features.search.router_embeddings import router as embeddings_router


def get_search_router() -> APIRouter:
    """Get the combined search router with all endpoints."""
    combined = APIRouter()

    # Include all sub-routers (they share the "search" tag and prefix)
    combined.include_router(fulltext_router)
    combined.include_router(semantic_router)
    combined.include_router(embeddings_router)

    return combined


# Default export for backward compatibility
router = get_search_router()
