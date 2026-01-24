"""
Notes Feature - SQLAlchemy Models

Re-exports Note-related models from the main models module.
This is a transitional approach during fractal migration - models
stay in models.py because other features depend on them.

NOTE: During full migration, this would contain the actual model definitions.
For now, we re-export to avoid circular imports and model conflicts.
"""

# Re-export from main models
# This allows features/notes to be self-contained in its API
# while avoiding SQLAlchemy table definition conflicts
from models import Note, NoteTag, NoteChunk

__all__ = ["Note", "NoteTag", "NoteChunk"]
