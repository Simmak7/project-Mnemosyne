"""
Pydantic schemas for the Images feature.

Includes:
- Image creation and response schemas
- Upload response schemas
- Task status schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# Tag Schema (re-used from main schemas for image relationships)
# ============================================================================

class TagInfo(BaseModel):
    """Basic tag information for image responses."""
    id: int
    name: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NoteInfo(BaseModel):
    """Basic note information for image responses."""
    id: int
    title: str
    slug: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Image Schemas
# ============================================================================

class ImageBase(BaseModel):
    """Base image schema with common fields."""
    filename: str
    filepath: str
    prompt: Optional[str] = None
    ai_analysis_status: str = "pending"
    ai_analysis_result: Optional[str] = None


class ImageCreate(ImageBase):
    """Schema for creating an image record."""
    pass


class ImageResponse(BaseModel):
    """Full image response with tags and related notes."""
    id: int
    filename: str
    filepath: str
    display_name: Optional[str] = None  # User-friendly display name
    prompt: Optional[str] = None
    ai_analysis_status: str
    ai_analysis_result: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    owner_id: Optional[int] = None
    # Blur hash fields for instant loading (Phase 3)
    blur_hash: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None  # File size in bytes
    # Favorites and Trash (Phase 4)
    is_favorite: bool = False
    is_trashed: bool = False
    trashed_at: Optional[datetime] = None
    tags: List[TagInfo] = []
    notes: List[NoteInfo] = []

    class Config:
        from_attributes = True


class ImageRename(BaseModel):
    """Request to rename an image."""
    display_name: str = Field(..., min_length=1, max_length=255, description="New display name")


class ImageListResponse(BaseModel):
    """Response for listing images."""
    images: List[ImageResponse]
    total: int
    skip: int
    limit: int


# ============================================================================
# Upload Schemas
# ============================================================================

class UploadResponse(BaseModel):
    """Response after successful image upload."""
    message: str
    filename: str
    image_id: int
    task_id: Optional[str] = None
    prompt: Optional[str] = None
    analysis_status: str = "queued"


class RetryResponse(BaseModel):
    """Response after retrying image analysis."""
    message: str
    image_id: int
    task_id: str
    analysis_status: str = "queued"


class DeleteResponse(BaseModel):
    """Response after deleting an image."""
    message: str
    image_id: int


# ============================================================================
# Task Status Schemas
# ============================================================================

class TaskStatusResponse(BaseModel):
    """Response for task status check."""
    task_id: str
    status: str = Field(..., description="Task state: PENDING, STARTED, SUCCESS, FAILURE, RETRY")
    ready: bool
    message: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None


# ============================================================================
# Analysis Schemas
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Request for custom analysis prompt."""
    prompt: str = Field(
        default="Describe this image in detail",
        description="Custom prompt for AI analysis"
    )
