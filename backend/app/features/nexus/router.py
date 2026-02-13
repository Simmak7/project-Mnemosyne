"""
NEXUS Router - Combines all NEXUS sub-routers.

Sub-routers:
- router_query: POST /nexus/query, POST /nexus/query/stream, GET /nexus/health
- router_admin: POST /nexus/consolidate, GET /nexus/suggestions (Phase 3)
"""

import logging
from fastapi import APIRouter

from features.nexus.router_query import router as query_router
from features.nexus.router_admin import router as admin_router

logger = logging.getLogger(__name__)


def get_nexus_router() -> APIRouter:
    """Build the combined NEXUS router."""
    combined = APIRouter()
    combined.include_router(query_router)
    combined.include_router(admin_router)
    return combined


router = get_nexus_router()
