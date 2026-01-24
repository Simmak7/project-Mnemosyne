"""
Note Collections Feature

Provides grouping/organization for notes (similar to Albums for images).
"""

from .router import router as collections_router
from .service import (
    get_collections,
    get_collection,
    create_collection,
    update_collection,
    delete_collection,
    add_note_to_collection,
    remove_note_from_collection,
)

__all__ = [
    "collections_router",
    "get_collections",
    "get_collection",
    "create_collection",
    "update_collection",
    "delete_collection",
    "add_note_to_collection",
    "remove_note_from_collection",
]
