"""
Semantic search API endpoints - COMPATIBILITY SHIM.

This module re-exports the router from the new location for backwards compatibility.
New code should import from features.search.router instead.

DEPRECATED: Use features.search.router directly.
"""

# Re-export router from new location
from features.search.router import router

# Also re-export schemas for backwards compatibility
from features.search.schemas import (
    SimilarNoteResult,
    SemanticSearchResponse,
    UnlinkedMentionResult,
    UnlinkedMentionsResponse,
)

__all__ = [
    "router",
    "SimilarNoteResult",
    "SemanticSearchResponse",
    "UnlinkedMentionResult",
    "UnlinkedMentionsResponse",
]
