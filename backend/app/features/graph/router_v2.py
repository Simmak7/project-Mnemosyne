"""
Graph Feature - API Router V2 (Typed Graph)

FastAPI endpoints for typed knowledge graph operations.
Provides local/map/path views with typed nodes and edges.

Combines sub-routers: views, nodes, ai operations.
"""

from fastapi import APIRouter

# Import sub-routers
from features.graph.router_views import router as views_router
from features.graph.router_nodes import router as nodes_router
from features.graph.router_ai import router as ai_router


def get_graph_v2_router() -> APIRouter:
    """Get the combined graph v2 router with all endpoints."""
    combined = APIRouter()

    # Include all sub-routers (they share the /graph prefix and Graph V2 tag)
    combined.include_router(views_router)
    combined.include_router(nodes_router)
    combined.include_router(ai_router)

    return combined


# Default export for backward compatibility
router = get_graph_v2_router()
