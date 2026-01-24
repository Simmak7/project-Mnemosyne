"""
Graph Feature - Pydantic Schemas

Defines request/response models for knowledge graph operations.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ============================================
# Graph Node Schemas
# ============================================

class GraphNode(BaseModel):
    """Basic graph node for single-note graph visualization."""
    id: int
    title: str
    slug: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class GraphEdge(BaseModel):
    """Edge between two nodes."""
    source: int
    target: int
    type: str = Field(..., description="Edge type: 'wikilink' or 'backlink'")


class GraphData(BaseModel):
    """Graph data for single-note visualization."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]


# ============================================
# Full Graph Schemas (for react-force-graph)
# ============================================

class FullGraphNode(BaseModel):
    """
    Full graph node for workspace knowledge graph.

    Node ID format: '{type}-{id}' e.g., 'note-123', 'tag-456', 'image-789'
    """
    id: str = Field(..., description="Format: 'note-{id}', 'tag-{id}', 'image-{id}'")
    title: str
    type: str = Field(..., description="Node type: 'note', 'tag', 'image'")

    # Type-specific IDs
    noteId: Optional[int] = None
    tagId: Optional[int] = None
    imageId: Optional[int] = None

    # Note-specific fields
    content: Optional[str] = None
    slug: Optional[str] = None
    backlinkCount: Optional[int] = None
    linkCount: Optional[int] = None

    # Tag-specific fields
    noteCount: Optional[int] = None

    # Image-specific fields
    filename: Optional[str] = None

    # Common fields
    created_at: Optional[str] = None


class FullGraphLink(BaseModel):
    """
    Link between two nodes in the full graph.

    Link types:
    - 'wikilink': note → note (via [[wikilinks]])
    - 'tag': note → tag
    - 'image': note → image
    """
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: str = Field(..., description="Link type: 'wikilink', 'tag', 'image'")


class FullGraphData(BaseModel):
    """Full knowledge graph data for workspace visualization."""
    nodes: List[FullGraphNode]
    links: List[FullGraphLink]


# ============================================
# Backlink Schemas
# ============================================

class BacklinkNote(BaseModel):
    """Note that links to another note (backlink)."""
    id: int
    title: str
    slug: Optional[str] = None
    content_snippet: Optional[str] = Field(None, description="Preview of content containing the link")
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BacklinksResponse(BaseModel):
    """Response for backlinks endpoint."""
    note_id: int
    backlinks: List[BacklinkNote]
    count: int


# ============================================
# Most Linked Schemas
# ============================================

class MostLinkedNote(BaseModel):
    """Note with its backlink count."""
    note_id: int
    title: str
    backlink_count: int


class MostLinkedResponse(BaseModel):
    """Response for most-linked notes endpoint."""
    notes: List[MostLinkedNote]
    total: int


# ============================================
# Wikilink Resolution Schemas
# ============================================

class WikilinkTarget(BaseModel):
    """Resolved wikilink target."""
    raw_link: str = Field(..., description="Original wikilink text")
    target_title: str = Field(..., description="Resolved target title")
    alias: Optional[str] = Field(None, description="Display alias if provided")
    resolved_note_id: Optional[int] = Field(None, description="ID of resolved note, None if unresolved")
    exists: bool = Field(..., description="Whether the target note exists")


class WikilinkValidationError(BaseModel):
    """Wikilink syntax error."""
    line: int
    message: str


class WikilinkValidationResponse(BaseModel):
    """Response for wikilink validation."""
    valid: bool
    errors: List[WikilinkValidationError]
    wikilinks_found: int


# ============================================
# Typed Graph Schemas (Phase 0 - Brain Graph)
# ============================================

class TypedNodeMetadata(BaseModel):
    """Metadata for a typed graph node."""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    excerpt: Optional[str] = None
    thumbnail: Optional[str] = None
    color: Optional[str] = None
    community_id: Optional[int] = None
    note_count: Optional[int] = None


class TypedGraphNode(BaseModel):
    """
    Node in the typed knowledge graph.

    Node types: 'note', 'tag', 'image', 'collection', 'entity', 'session'
    Node ID format: '{type}-{id}' (e.g., 'note-123', 'tag-456')
    """
    id: str = Field(..., description="Format: 'note-{id}', 'tag-{id}', etc.")
    type: str = Field(..., description="Node type: 'note', 'tag', 'image', 'collection'")
    title: str
    metadata: Optional[TypedNodeMetadata] = None


class TypedGraphEdge(BaseModel):
    """
    Edge in the typed knowledge graph.

    Edge types:
    - 'wikilink': Explicit [[link]] between notes (weight: 1.0)
    - 'tag': Note-to-tag assignment (weight: 0.7)
    - 'image': Note-to-image reference (weight: 0.6)
    - 'semantic': Embedding similarity (weight: 0.3-0.9)
    - 'session': Same-day creation (weight: 0.2)
    """
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: str = Field(..., description="Edge type")
    weight: float = Field(..., ge=0.0, le=1.0, description="Edge weight (0.0 - 1.0)")
    evidence: Optional[List[str]] = Field(None, description="Snippets explaining connection")


class TypedGraphResponse(BaseModel):
    """Response containing typed graph data."""
    nodes: List[TypedGraphNode]
    edges: List[TypedGraphEdge]
    metadata: Optional[dict] = None


# ============================================
# Local Graph Query Schemas
# ============================================

class LocalGraphRequest(BaseModel):
    """Request for local neighborhood graph."""
    node_id: str = Field(..., description="Center node ID (e.g., 'note-123')")
    depth: int = Field(2, ge=1, le=3, description="Hop depth (1-3)")
    layers: Optional[List[str]] = Field(
        None,
        description="Node types to include: 'notes', 'tags', 'images', 'semantic'"
    )
    min_weight: float = Field(0.0, ge=0.0, le=1.0, description="Minimum edge weight")


class LocalGraphResponse(TypedGraphResponse):
    """Response for local neighborhood graph."""
    center: str = Field(..., description="Center node ID")
    depth: int


# ============================================
# Map View (Clustered) Schemas
# ============================================

class CommunityInfo(BaseModel):
    """Information about a detected community/cluster."""
    id: int
    label: Optional[str] = None
    node_count: int
    top_terms: Optional[List[str]] = None
    center: Optional[dict] = None  # {"x": float, "y": float}


class MapGraphRequest(BaseModel):
    """Request for clustered map view."""
    scope: str = Field("all", description="'all', collection ID, or date range")
    cluster_algo: str = Field("louvain", description="'louvain' or 'leiden'")
    include_bundled: bool = Field(False, description="Include edge bundling data")


class MapGraphResponse(TypedGraphResponse):
    """Response for clustered map view."""
    communities: List[CommunityInfo]
    positions: Optional[dict] = None  # Precomputed node positions


# ============================================
# Path Finder Schemas
# ============================================

class PathRequest(BaseModel):
    """Request to find path between two nodes."""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    limit: int = Field(10, ge=1, le=20, description="Maximum path length")


class PathNodeInfo(BaseModel):
    """Node information in a path result."""
    id: str
    type: str
    title: str


class PathResponse(BaseModel):
    """Response with path between two nodes."""
    source: str
    target: str
    path: List[PathNodeInfo] = Field(..., description="Full node objects in path order")
    edges: List[TypedGraphEdge]
    explanation: str = Field(..., description="Human-readable path explanation")
    found: bool = Field(..., description="Whether a path was found")


# ============================================
# Semantic Edge Schemas
# ============================================

class SemanticEdgeCreate(BaseModel):
    """Create a new semantic edge."""
    source_type: str
    source_id: int
    target_type: str
    target_id: int
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class SemanticEdgeResponse(BaseModel):
    """Response for a semantic edge."""
    id: int
    source_type: str
    source_id: int
    target_type: str
    target_id: int
    similarity_score: float
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# Graph Position Schemas
# ============================================

class GraphPositionUpdate(BaseModel):
    """Update position for a graph node."""
    node_type: str
    node_id: int
    x: float
    y: float
    is_pinned: bool = False
    view_type: str = "map"


class GraphPositionResponse(BaseModel):
    """Response for a graph position."""
    node_id: str = Field(..., description="Format: 'note-123'")
    x: float
    y: float
    is_pinned: bool
