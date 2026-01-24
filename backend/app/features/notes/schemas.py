"""
Notes Feature - Pydantic Schemas

Request/Response schemas for note operations.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Forward reference for Tag schema
class TagRef(BaseModel):
    """Reference to a tag (used in note responses)."""
    id: int
    name: str
    created_at: Optional[datetime] = None
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True


class NoteBase(BaseModel):
    """Base note schema with common fields."""
    title: str
    content: str
    html_content: Optional[str] = None  # Rich HTML content for rendering


class NoteCreate(NoteBase):
    """Schema for creating a note."""
    # Allow extra fields like 'tags', 'wikilinks' from frontend but ignore them
    # Tags will be extracted automatically by wikilink_parser
    model_config = {"extra": "ignore"}


class NoteUpdate(BaseModel):
    """Schema for updating a note (partial updates allowed)."""
    title: Optional[str] = None
    content: Optional[str] = None
    html_content: Optional[str] = None  # Rich HTML content for rendering

    model_config = {"extra": "ignore"}


class NoteResponse(NoteBase):
    """Standard note response schema."""
    id: int
    slug: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    owner_id: Optional[int] = None
    tags: List[TagRef] = []

    class Config:
        from_attributes = True


class NoteEnhanced(BaseModel):
    """Enhanced note with graph relationships and tags."""
    id: int
    title: str
    content: str
    html_content: Optional[str] = None  # Rich HTML content for rendering
    slug: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    owner_id: Optional[int] = None
    tags: List[TagRef] = []
    linked_notes: List[int] = []  # IDs of notes this note links to
    backlinks: List[int] = []     # IDs of notes that link to this note
    image_ids: List[int] = []     # IDs of associated images

    class Config:
        from_attributes = True


# Graph-related schemas
class GraphNode(BaseModel):
    """Node in a note graph."""
    id: int
    title: str
    slug: Optional[str] = None
    created_at: Optional[str] = None


class GraphEdge(BaseModel):
    """Edge in a note graph."""
    source: int
    target: int
    type: str  # "wikilink" or "backlink"


class GraphData(BaseModel):
    """Complete graph data for visualization."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class FullGraphNode(BaseModel):
    """Node for full knowledge graph (includes images and tags)."""
    id: str  # Format: "note-123", "tag-456", "image-789"
    title: str
    type: str  # "note", "tag", "image"
    noteId: Optional[int] = None
    tagId: Optional[int] = None
    imageId: Optional[int] = None
    content: Optional[str] = None
    slug: Optional[str] = None
    filename: Optional[str] = None
    backlinkCount: Optional[int] = None
    linkCount: Optional[int] = None
    noteCount: Optional[int] = None
    created_at: Optional[str] = None


class FullGraphLink(BaseModel):
    """Link for full knowledge graph."""
    source: str
    target: str
    type: str  # "wikilink", "tag", "image"


class FullGraphData(BaseModel):
    """Full knowledge graph data for react-force-graph."""
    nodes: List[FullGraphNode]
    links: List[FullGraphLink]


class MostLinkedNote(BaseModel):
    """Note with backlink count for most-linked endpoint."""
    note_id: int
    title: str
    backlink_count: int


class DeleteResponse(BaseModel):
    """Response for delete operations."""
    status: str
    message: str
    note_id: int
