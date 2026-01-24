"""
Pydantic schemas for Albums feature.

Provides request/response models for:
- Album CRUD operations
- Album image management
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================
# Request Schemas
# ============================================

class AlbumCreate(BaseModel):
    """Request schema for creating an album."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class AlbumUpdate(BaseModel):
    """Request schema for updating an album."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    cover_image_id: Optional[int] = None


class AddImagesToAlbum(BaseModel):
    """Request schema for adding images to an album."""
    image_ids: List[int] = Field(..., min_items=1)


class RemoveImagesFromAlbum(BaseModel):
    """Request schema for removing images from an album."""
    image_ids: List[int] = Field(..., min_items=1)


# ============================================
# Response Schemas
# ============================================

class AlbumImageResponse(BaseModel):
    """Brief image info for album responses."""
    id: int
    filename: str
    blur_hash: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None

    class Config:
        from_attributes = True


class AlbumResponse(BaseModel):
    """Response schema for album (without images)."""
    id: int
    name: str
    description: Optional[str] = None
    cover_image_id: Optional[int] = None
    image_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Cover image preview
    cover_image: Optional[AlbumImageResponse] = None

    class Config:
        from_attributes = True


class AlbumWithImagesResponse(BaseModel):
    """Response schema for album with full image list."""
    id: int
    name: str
    description: Optional[str] = None
    cover_image_id: Optional[int] = None
    image_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    images: List[AlbumImageResponse] = []

    class Config:
        from_attributes = True


class AlbumListResponse(BaseModel):
    """Response schema for list of albums."""
    albums: List[AlbumResponse]
    total: int
