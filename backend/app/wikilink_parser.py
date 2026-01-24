"""
Wikilink Parser - BACKWARD COMPATIBILITY SHIM

This module has been migrated to features/graph/wikilink_parser.py

All exports are re-exported here for backward compatibility with
existing code that imports from wikilink_parser.

DEPRECATION NOTICE: Import from features.graph.wikilink_parser instead.
"""

# Re-export all functions from the new location
from features.graph.wikilink_parser import (
    extract_wikilinks,
    parse_wikilink,
    extract_hashtags,
    create_slug,
    find_wikilink_positions,
    replace_wikilinks_with_markdown,
    validate_wikilink_syntax,
)

__all__ = [
    "extract_wikilinks",
    "parse_wikilink",
    "extract_hashtags",
    "create_slug",
    "find_wikilink_positions",
    "replace_wikilinks_with_markdown",
    "validate_wikilink_syntax",
]
