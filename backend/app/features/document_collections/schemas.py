"""
Document Collections - Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CollectionBase(BaseModel):
    """Base schema for document collection."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class CollectionCreate(CollectionBase):
    """Schema for creating a new document collection."""
    pass


class CollectionUpdate(BaseModel):
    """Schema for updating a document collection."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class DocumentInCollection(BaseModel):
    """Brief document info for collection listing."""
    id: int
    display_name: Optional[str] = None
    filename: str
    uploaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CollectionResponse(CollectionBase):
    """Schema for collection response."""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    document_count: int = 0

    class Config:
        from_attributes = True


class CollectionWithDocuments(CollectionResponse):
    """Collection with list of documents."""
    documents: List[DocumentInCollection] = []


class AddDocumentRequest(BaseModel):
    """Request to add a document to a collection."""
    document_id: int
