"""
Pydantic schemas for search API.

Defines request validation and response serialization for:
- Full-text search endpoints
- Semantic search endpoints
- Unlinked mentions endpoint
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Full-text Search Schemas
# ============================================================================

class SearchResultBase(BaseModel):
    """Base schema for search results."""
    id: int
    title: str
    score: float = Field(..., description="Relevance score (0-1)")
    type: str = Field(..., description="Result type: 'note', 'image', or 'tag'")

    class Config:
        from_attributes = True


class NoteSearchResult(SearchResultBase):
    """Search result for a note."""
    type: str = "note"
    content: str
    slug: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    tags: List[Any] = []


class ImageSearchResult(SearchResultBase):
    """Search result for an image."""
    type: str = "image"
    filename: str
    filepath: str
    prompt: Optional[str] = None
    ai_analysis_status: Optional[str] = None
    ai_analysis_result: Optional[str] = None
    uploaded_at: Optional[str] = None
    tags: List[Any] = []


class TagSearchResult(SearchResultBase):
    """Search result for a tag."""
    type: str = "tag"
    name: str
    created_at: Optional[str] = None
    note_count: int = 0
    image_count: int = 0


class FulltextSearchResponse(BaseModel):
    """Response for full-text search."""
    results: List[Any] = Field(..., description="Mixed list of note, image, and tag results")
    query: str = Field(..., description="Original search query")
    total: int = Field(..., description="Total number of results")
    type_filter: str = Field(default="all", description="Type filter applied")
    date_range: str = Field(default="all", description="Date range filter applied")


class TagSearchResponse(BaseModel):
    """Response for search by tag."""
    notes: List[NoteSearchResult] = []
    images: List[ImageSearchResult] = []
    tag_name: str


# ============================================================================
# Semantic Search Schemas
# ============================================================================

class SimilarNoteResult(BaseModel):
    """Result for a similar note from semantic search."""
    id: int
    title: str
    content: str
    similarity: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score (0-1)")
    snippet: str = Field(..., description="Content preview")
    slug: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class SemanticSearchResponse(BaseModel):
    """Response for semantic search."""
    results: List[SimilarNoteResult]
    query: str = Field(..., description="Original search query")
    total: int = Field(..., description="Number of results")
    threshold: float = Field(..., description="Similarity threshold used")


class SimilarNotesResponse(BaseModel):
    """Response for finding similar notes."""
    results: List[SimilarNoteResult]
    source_note_id: int
    source_note_title: str
    total: int


# ============================================================================
# Unlinked Mentions Schemas
# ============================================================================

class UnlinkedMentionResult(BaseModel):
    """Result for an unlinked mention."""
    id: int
    title: str
    similarity: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score (0-1)")
    snippet: str = Field(..., description="Content preview showing why it's relevant")

    class Config:
        from_attributes = True


class UnlinkedMentionsResponse(BaseModel):
    """Response for unlinked mentions."""
    results: List[UnlinkedMentionResult]
    note_id: int = Field(..., description="Source note ID")
    note_title: str = Field(..., description="Source note title")
    total: int = Field(..., description="Number of unlinked mentions found")


# ============================================================================
# Embedding Schemas
# ============================================================================

class EmbeddingCoverageResponse(BaseModel):
    """Response for embedding coverage statistics."""
    total_notes: int
    notes_with_embedding: int
    notes_without_embedding: int
    coverage_percent: float


class EmbeddingRegenerateResponse(BaseModel):
    """Response for embedding regeneration request."""
    status: str = Field(..., description="Status: 'queued' or 'error'")
    note_id: int
    task_id: Optional[str] = None
    message: str
