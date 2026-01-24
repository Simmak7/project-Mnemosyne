"""
Tags Feature - Models

Re-exports Tag, NoteTag, and ImageTag models from main models.py.

This is a transitional pattern used during the fractal architecture migration.
The actual model definitions remain in backend/app/models.py to avoid:
1. SQLAlchemy "Table already defined" errors
2. Circular import issues with Note, Image, User relationships
3. Breaking existing code that imports from models.py

Once all features are migrated, models can be consolidated or remain shared.
"""

# Re-export models from the main models module
from models import Tag, NoteTag, ImageTag

__all__ = ["Tag", "NoteTag", "ImageTag"]
