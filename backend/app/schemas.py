from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool = True

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class ImageBase(BaseModel):
    filename: str
    filepath: str
    prompt: Optional[str] = None
    ai_analysis_status: str = "pending"
    ai_analysis_result: Optional[str] = None

class ImageCreate(ImageBase):
    pass

class Image(ImageBase):
    id: int
    owner_id: Optional[int] = None
    uploaded_at: Optional[datetime] = None
    tags: List['Tag'] = []
    notes: List['Note'] = []  # Include related notes

    class Config:
        from_attributes = True

class NoteBase(BaseModel):
    title: str
    content: str
    html_content: Optional[str] = None  # Rich HTML content for rendering

class NoteCreate(NoteBase):
    # Allow extra fields like 'tags', 'wikilinks' from frontend but ignore them
    # Tags will be extracted automatically by wikilink_parser
    model_config = {"extra": "ignore"}

class Note(NoteBase):
    id: int
    slug: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    owner_id: Optional[int] = None
    tags: List['Tag'] = []
    # Favorites, Trash, and Review fields
    is_favorite: bool = False
    is_trashed: bool = False
    trashed_at: Optional[datetime] = None
    is_reviewed: bool = False

    class Config:
        from_attributes = True


# Tag Schemas
class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int
    created_at: datetime
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True


# Enhanced Response Schemas
class ImageResponse(BaseModel):
    """Enhanced image response with tags."""
    id: int
    filename: str
    filepath: str
    prompt: Optional[str] = None
    ai_analysis_status: str
    ai_analysis_result: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    owner_id: Optional[int] = None
    tags: List[Tag] = []

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
    tags: List[Tag] = []
    linked_notes: List[int] = []  # IDs of notes this note links to
    backlinks: List[int] = []     # IDs of notes that link to this note
    image_ids: List[int] = []     # IDs of associated images
    is_favorite: bool = False     # Whether the note is favorited
    is_reviewed: bool = False     # Whether the note has been reviewed
    is_trashed: bool = False      # Whether the note is in trash

    class Config:
        from_attributes = True


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


# Search Schemas
class SearchQuery(BaseModel):
    """Search query parameters."""
    q: str  # Search query string
    type: str = "all"  # Filter by type: "all", "notes", "images", "tags"
    date_range: str = "all"  # Date filter: "all", "today", "week", "month", "year"
    sort_by: str = "relevance"  # Sort order: "relevance", "date", "title"
    limit: int = 50  # Maximum results to return


class SearchResultNote(BaseModel):
    """Search result for a note."""
    type: str = "note"
    id: int
    title: str
    content: str
    slug: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    score: float
    tags: List[dict] = []  # List of {id, name} dicts


class SearchResultImage(BaseModel):
    """Search result for an image."""
    type: str = "image"
    id: int
    filename: str
    filepath: str
    prompt: Optional[str] = None
    ai_analysis_status: str
    ai_analysis_result: Optional[str] = None
    uploaded_at: Optional[str] = None
    score: float
    tags: List[dict] = []  # List of {id, name} dicts


class SearchResultTag(BaseModel):
    """Search result for a tag."""
    type: str = "tag"
    id: int
    name: str
    created_at: Optional[str] = None
    score: float
    note_count: int
    image_count: int


class SearchResponse(BaseModel):
    """Response from search endpoint."""
    query: str
    results: List[dict]  # Mixed list of SearchResultNote, SearchResultImage, SearchResultTag
    total: int
    search_type: str  # "fulltext", "semantic", "combined"


# ============================================
# RAG (Retrieval-Augmented Generation) Schemas
# ============================================

class RAGQueryRequest(BaseModel):
    """Request for RAG query endpoint."""
    query: str
    conversation_id: Optional[int] = None  # For multi-turn conversations
    max_sources: int = 10  # Maximum sources to retrieve
    include_images: bool = True  # Whether to search images
    include_graph: bool = True  # Whether to traverse wikilink graph
    min_similarity: float = 0.5  # Minimum similarity threshold


class CitationSource(BaseModel):
    """A source cited in a RAG response."""
    index: int  # [1], [2], etc.
    source_type: str  # 'note', 'chunk', 'image'
    source_id: int
    title: str
    content_preview: str  # First ~200 chars
    relevance_score: float
    retrieval_method: str  # 'semantic', 'wikilink', 'fulltext', 'image_tag'
    hop_count: int = 0  # For graph traversal results
    relationship_chain: Optional[List[dict]] = None  # Explainability chain


class RetrievalMetadata(BaseModel):
    """Metadata about the retrieval process for explainability."""
    total_sources_searched: int
    sources_used: int
    retrieval_methods_used: List[str]
    avg_relevance_score: float
    source_type_breakdown: dict  # {'note': 5, 'image': 2, ...}
    query_type: str  # 'factual', 'exploratory', 'comparison', etc.
    context_tokens_approx: int
    context_truncated: bool = False


class RAGQueryResponse(BaseModel):
    """Response from RAG query endpoint."""
    answer: str
    citations: List[CitationSource]
    used_citation_indices: List[int]  # Which citations were actually used
    retrieval_metadata: RetrievalMetadata
    confidence_score: float  # 0.0 to 1.0
    confidence_level: str  # 'high', 'medium', 'low'
    conversation_id: Optional[int] = None
    message_id: Optional[int] = None


class RAGStreamChunk(BaseModel):
    """A chunk in a streaming RAG response."""
    type: str  # 'token', 'citation_start', 'citation_end', 'metadata', 'error', 'done'
    content: Optional[str] = None  # Token content
    citation: Optional[CitationSource] = None  # For citation events
    metadata: Optional[RetrievalMetadata] = None  # Final metadata
    confidence: Optional[dict] = None  # Confidence info at end


# Conversation Schemas
class ConversationCreate(BaseModel):
    """Create a new conversation."""
    title: Optional[str] = None


class ConversationUpdate(BaseModel):
    """Update a conversation."""
    title: Optional[str] = None
    summary: Optional[str] = None


class ConversationResponse(BaseModel):
    """Response for a conversation."""
    id: int
    title: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    message_count: int = 0

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Response for a chat message."""
    id: int
    conversation_id: int
    role: str  # 'user' or 'assistant'
    content: str
    created_at: datetime
    confidence_score: Optional[float] = None
    retrieval_metadata: Optional[dict] = None
    citations: List[CitationSource] = []

    class Config:
        from_attributes = True


class ConversationWithMessages(BaseModel):
    """Conversation with full message history."""
    id: int
    title: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


# Resolve forward references for Note and Image schemas
Note.model_rebuild()
Image.model_rebuild()

