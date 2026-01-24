"""
Albums feature - User-created collections of images.

Exports:
- AlbumService: Business logic for album operations
- router: FastAPI router for album endpoints
- schemas: Pydantic models for request/response
"""

from .service import AlbumService
from .router import router

__all__ = ["AlbumService", "router"]
