"""
Graph Feature - Knowledge Graph and Wikilinks

Provides:
- Wikilink parsing and resolution
- Backlink detection
- Knowledge graph data generation
- Orphaned note detection
- Typed graph visualization (Brain Graph - Phase 0+)
- Community clustering (Louvain/Leiden)
- Semantic edge generation
"""

from features.graph.wikilink_parser import (
    extract_wikilinks,
    parse_wikilink,
    extract_hashtags,
    create_slug,
    find_wikilink_positions,
    replace_wikilinks_with_markdown,
    validate_wikilink_syntax,
)

from features.graph.service import (
    resolve_wikilinks,
    get_backlinks,
    get_or_create_note_by_wikilink,
    get_note_graph_data,
    find_orphaned_notes,
    get_most_linked_notes,
    get_full_graph_data,
)

from features.graph.router import router as graph_router
from features.graph.router_v2 import router as graph_router_v2

# Phase 1: Typed Graph Services (Brain Graph)
from features.graph.services import (
    GraphIndex,
    TypedGraphBuilder,
    NodeType,
    EdgeType,
)

# Phase 2: Clustering and Semantic Edges
from features.graph.services import (
    ClusteringService,
    ClusterResult,
    SemanticEdgesService,
    SemanticEdgeResult,
)

# Phase 0: Typed Graph Models
from features.graph.models import SemanticEdge, GraphPosition, CommunityMetadata

__all__ = [
    # Parser utilities
    "extract_wikilinks",
    "parse_wikilink",
    "extract_hashtags",
    "create_slug",
    "find_wikilink_positions",
    "replace_wikilinks_with_markdown",
    "validate_wikilink_syntax",
    # Service functions
    "resolve_wikilinks",
    "get_backlinks",
    "get_or_create_note_by_wikilink",
    "get_note_graph_data",
    "find_orphaned_notes",
    "get_most_linked_notes",
    "get_full_graph_data",
    # Routers
    "graph_router",
    "graph_router_v2",
    # Phase 1: Typed Graph (Brain Graph)
    "GraphIndex",
    "TypedGraphBuilder",
    "NodeType",
    "EdgeType",
    # Phase 2: Clustering and Semantic Edges
    "ClusteringService",
    "ClusterResult",
    "SemanticEdgesService",
    "SemanticEdgeResult",
    # Models
    "SemanticEdge",
    "GraphPosition",
    "CommunityMetadata",
]
