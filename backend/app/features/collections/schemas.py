"""
Note Collections - Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CollectionBase(BaseModel):
    """Base schema for note collection."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None  # Emoji or icon name
    color: Optional[str] = None  # Hex color code


class CollectionCreate(CollectionBase):
    """Schema for creating a new collection."""
    pass


class CollectionUpdate(BaseModel):
    """Schema for updating a collection."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class NoteInCollection(BaseModel):
    """Brief note info for collection listing."""
    id: int
    title: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CollectionResponse(CollectionBase):
    """Schema for collection response."""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    note_count: int = 0

    class Config:
        from_attributes = True


class CollectionWithNotes(CollectionResponse):
    """Collection with list of notes."""
    notes: List[NoteInCollection] = []


class AddNoteRequest(BaseModel):
    """Request to add a note to a collection."""
    note_id: int
