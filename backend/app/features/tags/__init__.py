"""
Tags Feature Module

Handles tag management and associations for notes and images.
Tags are case-insensitive, stored lowercase, and owned per-user.

Public API:
- router: FastAPI router with tag endpoints
- Tag, NoteTag, ImageTag: SQLAlchemy models (re-exported from main models)
- TagCreate, TagResponse: Pydantic schemas
- TagService: Business logic for tag operations
"""

from .router import router
from .models import Tag, NoteTag, ImageTag
from .schemas import TagBase, TagCreate, TagResponse
from .service import TagService

__all__ = [
    "router",
    "Tag",
    "NoteTag",
    "ImageTag",
    "TagBase",
    "TagCreate",
    "TagResponse",
    "TagService",
]
