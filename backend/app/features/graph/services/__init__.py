"""
Graph Feature - Services

Service layer for typed knowledge graph operations.
Phase 1: Full implementations for local/map/path queries.
Phase 2: Semantic edges and community clustering.
"""

from .graph_index import (
    GraphIndex,
    TypedNode,
    TypedEdge,
    TypedGraphData,
    ClusteredGraphData,
    CommunityInfo,
    PathResult,
    NodeType,
    EdgeType,
)
from .typed_graph import TypedGraphBuilder
from .clustering import ClusteringService, ClusterResult
from .semantic_edges import SemanticEdgesService, SemanticEdgeResult

__all__ = [
    # Main services
    "GraphIndex",
    "TypedGraphBuilder",
    "ClusteringService",
    "SemanticEdgesService",
    # Data classes
    "TypedNode",
    "TypedEdge",
    "TypedGraphData",
    "ClusteredGraphData",
    "CommunityInfo",
    "PathResult",
    "ClusterResult",
    "SemanticEdgeResult",
    # Enums
    "NodeType",
    "EdgeType",
]
