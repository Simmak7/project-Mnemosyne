"""
Graph Feature - View Endpoints (Local, Map, Path)

FastAPI endpoints for graph visualization views.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_active_user
from core import exceptions
from slowapi import Limiter
from slowapi.util import get_remote_address

from features.graph.services import GraphIndex
from features.graph import schemas
import models

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/graph", tags=["Graph V2"])


# ============================================
# Local Neighborhood View
# ============================================

@router.get("/local", response_model=schemas.LocalGraphResponse)
@limiter.limit("60/minute")
async def get_local_graph(
    request: Request,
    node_id: str = Query(..., description="Center node ID (e.g., 'note-123')", alias="nodeId"),
    depth: int = Query(2, ge=1, le=3, description="Hop depth (1-3)"),
    layers: Optional[str] = Query(None, description="Comma-separated layers: notes,tags,images,semantic"),
    min_weight: float = Query(0.0, ge=0.0, le=1.0, description="Minimum edge weight", alias="minWeight"),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get local neighborhood graph around a focused node.

    Returns typed nodes and edges within `depth` hops of the center node.
    Use this for the Explore View - fast navigation around a selected note.
    """
    logger.debug(f"Local graph requested for node {node_id} by user {current_user.username}")

    try:
        layer_list = ["notes", "tags", "images"]
        if layers:
            layer_list = [l.strip() for l in layers.split(",")]

        graph_index = GraphIndex(db, current_user.id)
        result = graph_index.get_local(
            node_id=node_id, depth=depth, layers=layer_list, min_weight=min_weight
        )

        nodes = [
            schemas.TypedGraphNode(
                id=n.id, type=n.type.value, title=n.title,
                metadata=schemas.TypedNodeMetadata(**n.metadata) if n.metadata else None
            )
            for n in result.nodes
        ]

        edges = [
            schemas.TypedGraphEdge(
                source=e.source, target=e.target, type=e.type.value,
                weight=e.weight, evidence=e.evidence
            )
            for e in result.edges
        ]

        logger.info(f"Local graph: {len(nodes)} nodes, {len(edges)} edges")

        return schemas.LocalGraphResponse(
            nodes=nodes, edges=edges, center=node_id, depth=depth, metadata=result.metadata
        )

    except Exception as e:
        logger.error(f"Error generating local graph: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to generate local graph")


# ============================================
# Map View (Clustered Overview)
# ============================================

@router.get("/map", response_model=schemas.MapGraphResponse)
@limiter.limit("30/minute")
async def get_map_graph(
    request: Request,
    scope: str = Query("all", description="'all', collection ID, or date range"),
    cluster_algo: str = Query("louvain", description="Clustering algorithm: 'louvain' or 'leiden'", alias="clusterAlgo"),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get clustered map view for insight/discovery mode.

    Returns full graph with community clustering and precomputed positions.
    Use this for the Map View - discovery and pattern recognition.
    """
    logger.debug(f"Map graph requested by user {current_user.username}")

    try:
        graph_index = GraphIndex(db, current_user.id)
        result = graph_index.get_map(scope=scope, cluster_algo=cluster_algo, include_positions=True)

        nodes = [
            schemas.TypedGraphNode(
                id=n.id, type=n.type.value, title=n.title,
                metadata=schemas.TypedNodeMetadata(**n.metadata) if n.metadata else None
            )
            for n in result.nodes
        ]

        edges = [
            schemas.TypedGraphEdge(
                source=e.source, target=e.target, type=e.type.value,
                weight=e.weight, evidence=e.evidence
            )
            for e in result.edges
        ]

        communities = [
            schemas.CommunityInfo(
                id=c.id, label=c.label, node_count=c.node_count, top_terms=c.top_terms,
                center={"x": c.center_x, "y": c.center_y} if c.center_x else None
            )
            for c in result.communities
        ]

        positions = {node_id: {"x": pos[0], "y": pos[1]} for node_id, pos in result.positions.items()}

        logger.info(f"Map graph: {len(nodes)} nodes, {len(edges)} edges, {len(communities)} communities")

        return schemas.MapGraphResponse(
            nodes=nodes, edges=edges, communities=communities, positions=positions, metadata=result.metadata
        )

    except Exception as e:
        logger.error(f"Error generating map graph: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to generate map graph")


# ============================================
# Path Finder
# ============================================

@router.get("/path", response_model=schemas.PathResponse)
@limiter.limit("30/minute")
async def find_path(
    request: Request,
    source: str = Query(..., description="Source node ID (e.g., 'note-123')", alias="from"),
    target: str = Query(..., description="Target node ID (e.g., 'note-456')", alias="to"),
    limit: int = Query(10, ge=1, le=20, description="Maximum path length"),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Find path between two nodes with explanation.

    Uses BFS to find the shortest path through the knowledge graph.
    Returns the path with edge types and a human-readable explanation.
    """
    logger.debug(f"Path finding from {source} to {target} by user {current_user.username}")

    try:
        graph_index = GraphIndex(db, current_user.id)
        result = graph_index.get_path(source=source, target=target, limit=limit)

        if result is None:
            return schemas.PathResponse(
                source=source, target=target, path=[], edges=[],
                explanation=f"No path found between {source} and {target}", found=False
            )

        path_nodes = [
            schemas.PathNodeInfo(id=node.id, type=node.type.value, title=node.title)
            for node in result.path
        ]

        edges = [
            schemas.TypedGraphEdge(
                source=e.source, target=e.target, type=e.type.value,
                weight=e.weight, evidence=e.evidence
            )
            for e in result.edges
        ]

        logger.info(f"Path found: {len(result.path)} nodes")

        return schemas.PathResponse(
            source=result.source, target=result.target, path=path_nodes,
            edges=edges, explanation=result.explanation, found=result.found
        )

    except Exception as e:
        logger.error(f"Error finding path: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to find path")
