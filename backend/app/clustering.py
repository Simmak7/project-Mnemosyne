"""
AI clustering module - COMPATIBILITY SHIM.

This module re-exports functions from the new location for backwards compatibility.
New code should import from features.images.logic.clustering instead.

DEPRECATED: Use features.images.logic.clustering directly.
"""

# Re-export all functions from new location
from features.images.logic.clustering import (
    ClusterResult,
    extract_keywords_tfidf,
    generate_cluster_label,
    select_cluster_emoji,
    cluster_notes_by_embeddings,
    get_cluster_statistics,
    STOP_WORDS,
)

__all__ = [
    "ClusterResult",
    "extract_keywords_tfidf",
    "generate_cluster_label",
    "select_cluster_emoji",
    "cluster_notes_by_embeddings",
    "get_cluster_statistics",
    "STOP_WORDS",
]
