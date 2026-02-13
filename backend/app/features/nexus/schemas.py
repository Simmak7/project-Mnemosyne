"""
NEXUS Schemas - Pydantic models for graph-native adaptive retrieval.

Schemas:
- NexusQueryRequest: Query input with optional mode override
- NexusRichCitation: Citation with graph context + origin tracing
- NexusRetrievalMetadata: Extended metadata with mode/strategy info
- NexusQueryResponse: Full response with connections + suggestions
- NexusStreamChunk: SSE streaming event types
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class QueryMode(str, Enum):
    """NEXUS query routing modes."""
    FAST = "fast"
    STANDARD = "standard"
    DEEP = "deep"
    AUTO = "auto"


class QueryIntent(str, Enum):
    """Detected query intent for fusion weighting."""
    FACTUAL = "factual"
    SYNTHESIS = "synthesis"
    EXPLORATION = "exploration"
    TEMPORAL = "temporal"
    CREATIVE = "creative"


class NexusQueryRequest(BaseModel):
    """Request for NEXUS query endpoint."""
    query: str
    conversation_id: Optional[int] = None
    auto_create_conversation: bool = True
    mode: QueryMode = QueryMode.AUTO
    max_sources: int = 10
    include_images: bool = True
    include_graph: bool = True
    min_similarity: float = 0.4


class NexusRichCitation(BaseModel):
    """A rich citation with graph context and origin tracing."""
    index: int
    source_type: str  # note | chunk | image
    source_id: int
    title: str
    content_preview: str
    relevance_score: float
    retrieval_method: str  # semantic | graph_nav | wikilink | fulltext | diffusion
    hop_count: int = 0

    # Origin tracing
    origin_type: Optional[str] = None  # manual | image_analysis | document_analysis
    artifact_id: Optional[int] = None
    artifact_filename: Optional[str] = None

    # Graph context
    community_name: Optional[str] = None
    community_id: Optional[int] = None
    community_top_terms: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    direct_wikilinks: List[Dict[str, Any]] = Field(default_factory=list)
    path_to_other_results: List[Dict[str, Any]] = Field(default_factory=list)

    # Deep links
    note_url: Optional[str] = None
    graph_url: Optional[str] = None
    artifact_url: Optional[str] = None


class ConnectionInsight(BaseModel):
    """A discovered connection between retrieved sources."""
    source_index: int
    target_index: int
    connection_type: str  # wikilink | shared_community | shared_tag | co_retrieval
    description: str


class ExplorationSuggestion(BaseModel):
    """A suggested follow-up query based on graph context."""
    query: str
    reason: str
    related_citation_indices: List[int] = Field(default_factory=list)


class NexusRetrievalMetadata(BaseModel):
    """Extended retrieval metadata with NEXUS-specific info."""
    mode: str  # FAST | STANDARD | DEEP
    mode_auto_detected: bool = False
    intent: str = "factual"
    strategies_used: List[str] = Field(default_factory=list)
    total_sources_searched: int = 0
    sources_used: int = 0
    avg_relevance_score: float = 0.0
    source_type_breakdown: Dict[str, int] = Field(default_factory=dict)
    context_tokens_approx: int = 0
    context_truncated: bool = False
    graph_communities_searched: int = 0
    navigation_cache_hit: bool = False


class NexusQueryResponse(BaseModel):
    """Full NEXUS response with rich citations and graph insights."""
    answer: str
    rich_citations: List[NexusRichCitation] = Field(default_factory=list)
    used_citation_indices: List[int] = Field(default_factory=list)
    connection_insights: List[ConnectionInsight] = Field(default_factory=list)
    exploration_suggestions: List[ExplorationSuggestion] = Field(default_factory=list)
    missing_link_suggestions: List[Dict[str, Any]] = Field(default_factory=list)
    retrieval_metadata: NexusRetrievalMetadata
    confidence_score: float = 0.0
    confidence_level: str = "medium"
    conversation_id: Optional[int] = None
    message_id: Optional[int] = None
    model_used: Optional[str] = None


class NexusStreamChunk(BaseModel):
    """A chunk in a streaming NEXUS response."""
    type: str  # token | citations | connections | suggestions | metadata | error | done
    content: Optional[str] = None
    citations: Optional[List[NexusRichCitation]] = None
    connections: Optional[List[ConnectionInsight]] = None
    suggestions: Optional[List[ExplorationSuggestion]] = None
    metadata: Optional[NexusRetrievalMetadata] = None


class NexusHealthResponse(BaseModel):
    """NEXUS system health."""
    status: str
    navigation_cache_ready: bool = False
    consolidation_last_run: Optional[datetime] = None
    mode_availability: Dict[str, bool] = Field(default_factory=dict)


class NexusConsolidateRequest(BaseModel):
    """Request to trigger consolidation."""
    force: bool = False


class NexusLinkSuggestionResponse(BaseModel):
    """A pending link suggestion for the user."""
    id: int
    source_note_id: int
    source_note_title: str
    target_note_id: int
    target_note_title: str
    similarity_score: float
    co_retrieval_count: int
