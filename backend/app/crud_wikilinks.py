"""
CRUD Wikilinks - BACKWARD COMPATIBILITY SHIM

This module has been migrated to features/graph/service.py

All exports are re-exported here for backward compatibility with
existing code that imports from crud_wikilinks.

DEPRECATION NOTICE: Import from features.graph.service instead.
"""

# Re-export all functions from the new location
from features.graph.service import (
    resolve_wikilinks,
    get_backlinks,
    get_or_create_note_by_wikilink,
    get_note_graph_data,
    find_orphaned_notes,
    get_most_linked_notes,
)

__all__ = [
    "resolve_wikilinks",
    "get_backlinks",
    "get_or_create_note_by_wikilink",
    "get_note_graph_data",
    "find_orphaned_notes",
    "get_most_linked_notes",
]
