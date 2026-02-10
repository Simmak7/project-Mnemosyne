"""
Graph Index Service

Single source of truth for typed graph visualization data.
Provides query surfaces for local/map/path views.

Phase 1: Full implementation with actual queries.
"""

from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from sqlalchemy.orm import Session

import models


class NodeType(str, Enum):
    """Supported node types in the typed graph."""
    NOTE = "note"
    TAG = "tag"
    IMAGE = "image"
    COLLECTION = "collection"
    DOCUMENT = "document"
    ENTITY = "entity"  # Future: extracted named entities
    SESSION = "session"  # Future: daily session nodes


class EdgeType(str, Enum):
    """Supported edge types in the typed graph."""
    WIKILINK = "wikilink"  # Explicit [[links]] between notes
    TAG = "tag"  # Note-to-tag assignment
    IMAGE = "image"  # Note-to-image reference
    SOURCE = "source"  # Document-to-note source link
    SEMANTIC = "semantic"  # Embedding similarity
    SESSION = "session"  # Same-day creation
    MENTIONS = "mentions"  # Entity mention (future)


@dataclass
class TypedNode:
    """A node in the typed graph."""
    id: str  # Format: 'note-123', 'tag-456'
    type: NodeType
    title: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TypedEdge:
    """An edge in the typed graph."""
    source: str
    target: str
    type: EdgeType
    weight: float  # 0.0 - 1.0
    evidence: Optional[List[str]] = None  # Snippets explaining connection


@dataclass
class TypedGraphData:
    """Graph data for visualization."""
    nodes: List[TypedNode]
    edges: List[TypedEdge]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommunityInfo:
    """Information about a detected community."""
    id: int
    label: Optional[str] = None
    node_count: int = 0
    top_terms: List[str] = field(default_factory=list)
    center_x: Optional[float] = None
    center_y: Optional[float] = None


@dataclass
class ClusteredGraphData:
    """Graph data with community clustering."""
    nodes: List[TypedNode]
    edges: List[TypedEdge]
    communities: List[CommunityInfo]
    positions: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PathResult:
    """Result of path finding between two nodes."""
    source: str
    target: str
    path: List[TypedNode]  # Full node objects in order
    edges: List[TypedEdge]
    explanation: str
    found: bool = True


class GraphIndex:
    """
    Typed graph index service.

    Provides query methods for different graph views:
    - get_local(): Local neighborhood around a focused node
    - get_map(): Clustered overview for insight mode
    - get_path(): Path finding between two nodes

    Usage:
        index = GraphIndex(db, user_id)
        local_data = index.get_local("note-123", depth=2)
        map_data = index.get_map()
        path = index.get_path("note-1", "note-5")
    """

    def __init__(self, db: Session, user_id: int):
        """Initialize graph index for a user."""
        self.db = db
        self.user_id = user_id
        self._builder = None

    @property
    def builder(self):
        """Lazy-load TypedGraphBuilder."""
        if self._builder is None:
            from .typed_graph import TypedGraphBuilder
            self._builder = TypedGraphBuilder(self.db, self.user_id)
        return self._builder

    def get_local(
        self,
        node_id: str,
        depth: int = 2,
        layers: Optional[List[str]] = None,
        min_weight: float = 0.0
    ) -> TypedGraphData:
        """
        Get local neighborhood graph around a focused node.

        Args:
            node_id: Center node ID (e.g., 'note-123')
            depth: How many hops to traverse (1-3 recommended)
            layers: Node types to include ('notes', 'tags', 'images', 'semantic')
            min_weight: Minimum edge weight to include (0.0 - 1.0)

        Returns:
            TypedGraphData with nodes and edges in neighborhood
        """
        if layers is None:
            layers = ["notes", "tags"]

        return self.builder.build_local_graph(
            center_node_id=node_id,
            depth=depth,
            layers=layers,
            min_weight=min_weight
        )

    def get_map(
        self,
        scope: str = "all",
        cluster_algo: str = "louvain",
        include_positions: bool = True
    ) -> ClusteredGraphData:
        """
        Get clustered map view for insight/discovery mode.

        Args:
            scope: 'all', collection ID, or date range
            cluster_algo: 'louvain' or 'leiden'
            include_positions: Include precomputed node positions

        Returns:
            ClusteredGraphData with community-clustered nodes
        """
        # Build full graph
        graph_data = self.builder.build_full_graph(include_semantic=False)

        # Group nodes by community
        communities = self._detect_communities(graph_data.nodes)

        # Get positions if available
        positions = {}
        if include_positions:
            positions = self._get_cached_positions()

        return ClusteredGraphData(
            nodes=graph_data.nodes,
            edges=graph_data.edges,
            communities=communities,
            positions=positions,
            metadata={
                "scope": scope,
                "cluster_algo": cluster_algo,
                "node_count": len(graph_data.nodes),
                "edge_count": len(graph_data.edges),
                "community_count": len(communities),
            }
        )

    def get_path(
        self,
        source: str,
        target: str,
        limit: int = 10
    ) -> Optional[PathResult]:
        """
        Find path between two nodes with explanation.

        Uses BFS to find shortest path through the graph.

        Args:
            source: Source node ID
            target: Target node ID
            limit: Maximum path length to search

        Returns:
            PathResult with path and explanation, or None if not connected
        """
        # Build full graph for path finding
        graph_data = self.builder.build_full_graph(include_semantic=False)

        # Build node lookup map for converting IDs to full nodes
        node_map: Dict[str, TypedNode] = {node.id: node for node in graph_data.nodes}

        # Build adjacency list
        adjacency: Dict[str, List[Tuple[str, TypedEdge]]] = {}
        for edge in graph_data.edges:
            if edge.source not in adjacency:
                adjacency[edge.source] = []
            adjacency[edge.source].append((edge.target, edge))

            # Make edges bidirectional for path finding
            if edge.target not in adjacency:
                adjacency[edge.target] = []
            # Create reverse edge
            reverse_edge = TypedEdge(
                source=edge.target,
                target=edge.source,
                type=edge.type,
                weight=edge.weight,
                evidence=edge.evidence
            )
            adjacency[edge.target].append((edge.source, reverse_edge))

        # BFS to find shortest path (returns list of node IDs)
        path_ids, edges = self._bfs_path(adjacency, source, target, limit)

        if not path_ids:
            return PathResult(
                source=source,
                target=target,
                path=[],
                edges=[],
                explanation=f"No path found between {source} and {target}",
                found=False
            )

        # Convert path IDs to full node objects
        path_nodes = []
        for node_id in path_ids:
            if node_id in node_map:
                path_nodes.append(node_map[node_id])
            else:
                # Fallback: create minimal node if not found
                node_type = node_id.split('-')[0] if '-' in node_id else 'unknown'
                path_nodes.append(TypedNode(
                    id=node_id,
                    type=NodeType(node_type) if node_type in [e.value for e in NodeType] else NodeType.NOTE,
                    title=node_id,
                    metadata={}
                ))

        # Generate explanation
        explanation = self._generate_path_explanation(path_ids, edges)

        return PathResult(
            source=source,
            target=target,
            path=path_nodes,
            edges=edges,
            explanation=explanation,
            found=True
        )

    def _bfs_path(
        self,
        adjacency: Dict[str, List[Tuple[str, TypedEdge]]],
        source: str,
        target: str,
        limit: int
    ) -> Tuple[List[str], List[TypedEdge]]:
        """BFS to find shortest path."""
        if source == target:
            return [source], []

        # Queue: (current_node, path, edges)
        queue: deque = deque([(source, [source], [])])
        visited: Set[str] = {source}

        while queue:
            current, path, edges = queue.popleft()

            if len(path) > limit:
                continue

            neighbors = adjacency.get(current, [])
            for neighbor, edge in neighbors:
                if neighbor == target:
                    return path + [neighbor], edges + [edge]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor], edges + [edge]))

        return [], []

    def _generate_path_explanation(
        self,
        path: List[str],
        edges: List[TypedEdge]
    ) -> str:
        """Generate human-readable path explanation."""
        if not path or not edges:
            return "No path found."

        parts = []
        for i, edge in enumerate(edges):
            source_name = self._get_node_title(path[i])
            target_name = self._get_node_title(path[i + 1])
            edge_desc = self._edge_type_description(edge.type)
            parts.append(f"{source_name} {edge_desc} {target_name}")

        return " → ".join(parts)

    def _edge_type_description(self, edge_type: EdgeType) -> str:
        """Get human-readable edge type description."""
        descriptions = {
            EdgeType.WIKILINK: "links to",
            EdgeType.TAG: "shares tag with",
            EdgeType.IMAGE: "shares image with",
            EdgeType.SOURCE: "is source of",
            EdgeType.SEMANTIC: "is similar to",
            EdgeType.SESSION: "was created with",
        }
        return descriptions.get(edge_type, "connects to")

    def _get_node_title(self, node_id: str) -> str:
        """Get title for a node ID."""
        node = self.get_node(node_id)
        return node.title if node else node_id

    def get_node(self, node_id: str) -> Optional[TypedNode]:
        """
        Get a single node by ID.

        Args:
            node_id: Node ID (e.g., 'note-123')

        Returns:
            TypedNode or None if not found
        """
        return self.builder._get_node_by_id(node_id)

    def get_neighbors(self, node_id: str, depth: int = 1) -> List[str]:
        """
        Get IDs of neighboring nodes.

        Args:
            node_id: Center node ID
            depth: Hop distance

        Returns:
            List of neighbor node IDs
        """
        local_graph = self.get_local(node_id, depth=depth)
        return [node.id for node in local_graph.nodes if node.id != node_id]

    def _detect_communities(self, nodes: List[TypedNode]) -> List[CommunityInfo]:
        """
        Detect communities from node community_id assignments.

        For now, reads from existing community_id field.
        Phase 2 will add actual Louvain/Leiden detection.
        """
        community_map: Dict[int, List[TypedNode]] = {}

        for node in nodes:
            community_id = node.metadata.get("community_id")
            if community_id is not None:
                if community_id not in community_map:
                    community_map[community_id] = []
                community_map[community_id].append(node)

        communities = []
        for cid, community_nodes in community_map.items():
            # Get top terms from note titles
            top_terms = []
            for n in community_nodes[:5]:
                if n.type == NodeType.NOTE:
                    words = n.title.split()[:2]
                    top_terms.extend(words)

            communities.append(CommunityInfo(
                id=cid,
                label=f"Cluster {cid}",
                node_count=len(community_nodes),
                top_terms=top_terms[:5],
            ))

        # Add unclustered nodes as "Other"
        unclustered = [n for n in nodes if n.metadata.get("community_id") is None]
        if unclustered:
            communities.append(CommunityInfo(
                id=-1,
                label="Unclustered",
                node_count=len(unclustered),
                top_terms=[],
            ))

        return communities

    def _get_cached_positions(self) -> Dict[str, Tuple[float, float]]:
        """
        Get cached node positions from graph_positions table.
        """
        try:
            from features.graph.models import GraphPosition

            positions = self.db.query(GraphPosition).filter(
                GraphPosition.owner_id == self.user_id,
                GraphPosition.view_type == "map"
            ).all()

            return {
                f"{pos.node_type}-{pos.node_id}": (pos.x, pos.y)
                for pos in positions
            }
        except Exception:
            return {}

    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics for the user."""
        graph_data = self.builder.build_full_graph(include_semantic=False)

        # Count by type
        node_counts = {}
        for node in graph_data.nodes:
            node_type = node.type.value
            node_counts[node_type] = node_counts.get(node_type, 0) + 1

        edge_counts = {}
        for edge in graph_data.edges:
            edge_type = edge.type.value
            edge_counts[edge_type] = edge_counts.get(edge_type, 0) + 1

        return {
            "total_nodes": len(graph_data.nodes),
            "total_edges": len(graph_data.edges),
            "node_counts": node_counts,
            "edge_counts": edge_counts,
        }
