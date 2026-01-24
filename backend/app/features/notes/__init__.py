"""
Notes Feature Module

Handles note CRUD operations, wikilinks, tags, and knowledge graph functionality.
This is a core feature with extensive relationships to other modules.
"""

from features.notes.router import router as notes_router
from features.notes.models import Note, NoteTag, NoteChunk
from features.notes import service
from features.notes import schemas

__all__ = [
    # Router
    "notes_router",
    # Models
    "Note",
    "NoteTag",
    "NoteChunk",
    # Modules
    "service",
    "schemas",
]
