"""
RAG Chat Schemas - Pydantic validation schemas for RAG feature.

Schemas:
- RAGQueryRequest: Query input with options for sources, images, graph
- RAGQueryResponse: Query result with answer, citations, metadata
- CitationSource: Individual citation with relevance and retrieval method
- RetrievalMetadata: Explainability data (methods used, breakdown, confidence)
- ConversationResponse: Conversation summary
- MessageResponse: Message with citations
- ConversationWithMessages: Full conversation history
- RAGStreamChunk: Streaming response event
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class RAGQueryRequest(BaseModel):
    """Request for RAG query endpoint."""
    query: str
    conversation_id: Optional[int] = None  # For multi-turn conversations
    auto_create_conversation: bool = True  # Auto-create if no conversation_id
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

    # NEXUS fields (all optional, backward-compatible with RAG mode)
    origin_type: Optional[str] = None
    artifact_id: Optional[int] = None
    artifact_url: Optional[str] = None
    community_name: Optional[str] = None
    community_id: Optional[int] = None
    tags: List[str] = []
    direct_wikilinks: List[dict] = []
    path_to_other_results: List[dict] = []
    note_url: Optional[str] = None
    graph_url: Optional[str] = None


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
    model_used: Optional[str] = None  # Which model generated this response


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

    # NEXUS insights (rebuilt from stored citations on load)
    connection_insights: List[dict] = []
    exploration_suggestions: List[dict] = []


# Export all schemas
__all__ = [
    "RAGQueryRequest",
    "CitationSource",
    "RetrievalMetadata",
    "RAGQueryResponse",
    "RAGStreamChunk",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "MessageResponse",
    "ConversationWithMessages",
]
