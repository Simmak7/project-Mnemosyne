"""
Pydantic schemas for the Buckets feature.

Includes schemas for:
- AI Clusters
- Orphan notes
- Inbox notes
- Daily notes
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Cluster Schemas
# ============================================================================

class ClusterInfo(BaseModel):
    """Information about a cluster."""
    cluster_id: int
    label: str
    keywords: List[str]
    size: int
    emoji: str
    note_ids: List[int]

    class Config:
        from_attributes = True


class ClusterListResponse(BaseModel):
    """Response for cluster list."""
    clusters: List[ClusterInfo]
    total_clusters: int
    total_notes: int
    average_cluster_size: float
    cached: bool = Field(default=False, description="Whether result came from cache")


class ClusterNotesResponse(BaseModel):
    """Response for notes in a cluster."""
    cluster_id: int
    label: str
    keywords: List[str]
    notes: List["NoteBasicInfo"]
    total: int


class CacheInvalidateResponse(BaseModel):
    """Response for cache invalidation."""
    status: str
    invalidated_keys: int
    message: str


# ============================================================================
# Note Schemas
# ============================================================================

class NoteBasicInfo(BaseModel):
    """Basic note information."""
    id: int
    title: str
    content: str
    html_content: Optional[str] = None  # Rich HTML content for rendering
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class OrphansResponse(BaseModel):
    """Response for orphan notes."""
    notes: List[NoteBasicInfo]
    total: int
    description: str = "Notes with no wikilinks (incoming or outgoing)"


class InboxResponse(BaseModel):
    """Response for inbox notes."""
    notes: List[NoteBasicInfo]
    total: int
    description: str = "Recently created notes (last 7 days)"


# ============================================================================
# Daily Notes Schemas
# ============================================================================

class DailyNoteResponse(BaseModel):
    """Response for a daily note."""
    id: int
    title: str
    content: str
    html_content: Optional[str] = None  # Rich HTML content for rendering
    date: str
    created_at: str
    updated_at: Optional[str]
    is_new: bool = Field(default=False, description="Whether this note was just created")

    class Config:
        from_attributes = True


class DailyNotesListResponse(BaseModel):
    """Response for daily notes list."""
    notes: List[DailyNoteResponse]
    total: int
    description: str = "Daily notes organized by date"


# Resolve forward references
ClusterNotesResponse.model_rebuild()
