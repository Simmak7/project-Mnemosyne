"""
Tags Feature - Pydantic Schemas

Defines request/response schemas for tag operations.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TagBase(BaseModel):
    """Base schema for tag data."""
    name: str = Field(..., min_length=1, max_length=100, description="Tag name (case-insensitive)")


class TagCreate(TagBase):
    """Schema for creating a new tag."""
    pass


class TagResponse(TagBase):
    """Schema for tag responses - includes all tag data."""
    id: int
    created_at: datetime
    owner_id: Optional[int] = None
    note_count: Optional[int] = 0  # Number of notes with this tag

    class Config:
        from_attributes = True


# Alias for backward compatibility
Tag = TagResponse


class TagAddResponse(BaseModel):
    """Response schema for adding a tag to a note/image."""
    status: str = Field(default="success")
    tag_id: int
    tag_name: str


class TagRemoveResponse(BaseModel):
    """Response schema for removing a tag from a note/image."""
    status: str = Field(default="success")


__all__ = [
    "TagBase",
    "TagCreate",
    "TagResponse",
    "Tag",
    "TagAddResponse",
    "TagRemoveResponse",
]
