"""
Search CRUD operations - COMPATIBILITY SHIM.

This module re-exports functions from the new location for backwards compatibility.
New code should import from features.search.logic.fulltext instead.

DEPRECATED: Use features.search.logic.fulltext directly.
"""

# Re-export all functions from new location
from features.search.logic.fulltext import (
    parse_search_query,
    apply_date_filter,
    search_notes_fulltext,
    search_images_fulltext,
    search_tags_fuzzy,
    search_combined,
    search_by_tag,
)

__all__ = [
    "parse_search_query",
    "apply_date_filter",
    "search_notes_fulltext",
    "search_images_fulltext",
    "search_tags_fuzzy",
    "search_combined",
    "search_by_tag",
]
