"""
Graph Feature - API Router V2 (Typed Graph)

FastAPI endpoints for typed knowledge graph operations.
Provides local/map/path views with typed nodes and edges.

Phase 1: New endpoints alongside existing router.py
Phase 2: Semantic edges and clustering endpoints
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Query, BackgroundTasks
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_active_user
from core import exceptions
from slowapi import Limiter
from slowapi.util import get_remote_address

from features.graph.services import GraphIndex, ClusteringService, SemanticEdgesService
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
    node_id: str = Query(
        ...,
        description="Center node ID (e.g., 'note-123', 'tag-456')",
        alias="nodeId"
    ),
    depth: int = Query(
        2,
        ge=1,
        le=3,
        description="Hop depth (1-3)"
    ),
    layers: Optional[str] = Query(
        None,
        description="Comma-separated layers: notes,tags,images,semantic"
    ),
    min_weight: float = Query(
        0.0,
        ge=0.0,
        le=1.0,
        description="Minimum edge weight",
        alias="minWeight"
    ),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get local neighborhood graph around a focused node.

    Returns typed nodes and edges within `depth` hops of the center node.
    Use this for the Explore View - fast navigation around a selected note.

    Args:
        nodeId: Center node ID (e.g., 'note-123')
        depth: How many hops to traverse (1-3)
        layers: Which node types to include (default: notes,tags)
        minWeight: Minimum edge weight to include

    Returns:
        TypedGraphResponse with nodes and edges
    """
    logger.debug(f"Local graph requested for node {node_id} by user {current_user.username}")

    try:
        # Parse layers - include images by default for image-note connections
        layer_list = ["notes", "tags", "images"]
        if layers:
            layer_list = [l.strip() for l in layers.split(",")]

        graph_index = GraphIndex(db, current_user.id)
        result = graph_index.get_local(
            node_id=node_id,
            depth=depth,
            layers=layer_list,
            min_weight=min_weight
        )

        # Convert to response schema
        nodes = [
            schemas.TypedGraphNode(
                id=n.id,
                type=n.type.value,
                title=n.title,
                metadata=schemas.TypedNodeMetadata(**n.metadata) if n.metadata else None
            )
            for n in result.nodes
        ]

        edges = [
            schemas.TypedGraphEdge(
                source=e.source,
                target=e.target,
                type=e.type.value,
                weight=e.weight,
                evidence=e.evidence
            )
            for e in result.edges
        ]

        logger.info(f"Local graph: {len(nodes)} nodes, {len(edges)} edges")

        return schemas.LocalGraphResponse(
            nodes=nodes,
            edges=edges,
            center=node_id,
            depth=depth,
            metadata=result.metadata
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
    cluster_algo: str = Query(
        "louvain",
        description="Clustering algorithm: 'louvain' or 'leiden'",
        alias="clusterAlgo"
    ),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get clustered map view for insight/discovery mode.

    Returns full graph with community clustering and precomputed positions.
    Use this for the Map View - discovery and pattern recognition.

    Args:
        scope: Filter scope ('all', collection ID, date range)
        clusterAlgo: Clustering algorithm (louvain/leiden)

    Returns:
        MapGraphResponse with nodes, edges, communities, and positions
    """
    logger.debug(f"Map graph requested by user {current_user.username}")

    try:
        graph_index = GraphIndex(db, current_user.id)
        result = graph_index.get_map(
            scope=scope,
            cluster_algo=cluster_algo,
            include_positions=True
        )

        # Convert to response schema
        nodes = [
            schemas.TypedGraphNode(
                id=n.id,
                type=n.type.value,
                title=n.title,
                metadata=schemas.TypedNodeMetadata(**n.metadata) if n.metadata else None
            )
            for n in result.nodes
        ]

        edges = [
            schemas.TypedGraphEdge(
                source=e.source,
                target=e.target,
                type=e.type.value,
                weight=e.weight,
                evidence=e.evidence
            )
            for e in result.edges
        ]

        communities = [
            schemas.CommunityInfo(
                id=c.id,
                label=c.label,
                node_count=c.node_count,
                top_terms=c.top_terms,
                center={"x": c.center_x, "y": c.center_y} if c.center_x else None
            )
            for c in result.communities
        ]

        # Convert positions to dict format
        positions = {
            node_id: {"x": pos[0], "y": pos[1]}
            for node_id, pos in result.positions.items()
        }

        logger.info(f"Map graph: {len(nodes)} nodes, {len(edges)} edges, {len(communities)} communities")

        return schemas.MapGraphResponse(
            nodes=nodes,
            edges=edges,
            communities=communities,
            positions=positions,
            metadata=result.metadata
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
    source: str = Query(
        ...,
        description="Source node ID (e.g., 'note-123')",
        alias="from"
    ),
    target: str = Query(
        ...,
        description="Target node ID (e.g., 'note-456')",
        alias="to"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=20,
        description="Maximum path length"
    ),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Find path between two nodes with explanation.

    Uses BFS to find the shortest path through the knowledge graph.
    Returns the path with edge types and a human-readable explanation.

    Args:
        from: Source node ID
        to: Target node ID
        limit: Maximum path length to search

    Returns:
        PathResponse with path, edges, and explanation
    """
    logger.debug(f"Path finding from {source} to {target} by user {current_user.username}")

    try:
        graph_index = GraphIndex(db, current_user.id)
        result = graph_index.get_path(
            source=source,
            target=target,
            limit=limit
        )

        if result is None:
            return schemas.PathResponse(
                source=source,
                target=target,
                path=[],
                edges=[],
                explanation=f"No path found between {source} and {target}",
                found=False
            )

        # Convert path nodes to schema format
        path_nodes = [
            schemas.PathNodeInfo(
                id=node.id,
                type=node.type.value,
                title=node.title
            )
            for node in result.path
        ]

        edges = [
            schemas.TypedGraphEdge(
                source=e.source,
                target=e.target,
                type=e.type.value,
                weight=e.weight,
                evidence=e.evidence
            )
            for e in result.edges
        ]

        logger.info(f"Path found: {len(result.path)} nodes")

        return schemas.PathResponse(
            source=result.source,
            target=result.target,
            path=path_nodes,
            edges=edges,
            explanation=result.explanation,
            found=result.found
        )

    except Exception as e:
        logger.error(f"Error finding path: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to find path")


# ============================================
# Graph Statistics
# ============================================

@router.get("/stats")
@limiter.limit("60/minute")
async def get_graph_stats(
    request: Request,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get graph statistics for the current user.

    Returns counts of nodes and edges by type.
    """
    logger.debug(f"Graph stats requested by user {current_user.username}")

    try:
        graph_index = GraphIndex(db, current_user.id)
        stats = graph_index.get_stats()

        logger.info(f"Graph stats: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
        return stats

    except Exception as e:
        logger.error(f"Error getting graph stats: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to get graph stats")


# ============================================
# Node Details
# ============================================

@router.get("/node/{node_id}", response_model=schemas.TypedGraphNode)
@limiter.limit("60/minute")
async def get_node(
    request: Request,
    node_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get details for a single node.

    Args:
        node_id: Node ID (e.g., 'note-123')

    Returns:
        TypedGraphNode with full metadata
    """
    logger.debug(f"Node {node_id} requested by user {current_user.username}")

    try:
        graph_index = GraphIndex(db, current_user.id)
        node = graph_index.get_node(node_id)

        if node is None:
            raise exceptions.ResourceNotFoundException("Node", node_id)

        return schemas.TypedGraphNode(
            id=node.id,
            type=node.type.value,
            title=node.title,
            metadata=schemas.TypedNodeMetadata(**node.metadata) if node.metadata else None
        )

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error getting node: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to get node")


# ============================================
# Neighbors
# ============================================

@router.get("/node/{node_id}/neighbors")
@limiter.limit("60/minute")
async def get_node_neighbors(
    request: Request,
    node_id: str,
    depth: int = Query(1, ge=1, le=3),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get IDs of neighboring nodes.

    Args:
        node_id: Center node ID
        depth: Hop distance (1-3)

    Returns:
        List of neighbor node IDs
    """
    logger.debug(f"Neighbors for {node_id} requested by user {current_user.username}")

    try:
        graph_index = GraphIndex(db, current_user.id)
        neighbors = graph_index.get_neighbors(node_id, depth=depth)

        return {
            "node_id": node_id,
            "depth": depth,
            "neighbors": neighbors,
            "count": len(neighbors)
        }

    except Exception as e:
        logger.error(f"Error getting neighbors: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to get neighbors")


# ============================================
# Semantic Edges (Phase 2)
# ============================================

@router.post("/semantic/rebuild")
@limiter.limit("5/minute")
async def rebuild_semantic_edges(
    request: Request,
    threshold: float = Query(0.7, ge=0.3, le=0.95, description="Similarity threshold"),
    background_tasks: BackgroundTasks = None,
    use_celery: bool = Query(True, description="Use Celery for async processing"),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Rebuild semantic similarity edges for the current user.

    This endpoint generates edges between notes that are semantically similar
    based on their embeddings. Notes must have embeddings (from the search
    indexing process) to be included.

    Args:
        threshold: Minimum similarity score (0.3 - 0.95, default 0.7)
        use_celery: If True, runs as background Celery task (recommended)

    Returns:
        Task info if async, or result if sync
    """
    logger.info(f"Semantic edge rebuild requested by user {current_user.username}")

    if use_celery:
        # Run as Celery background task
        from features.graph.tasks import generate_semantic_edges_task
        task = generate_semantic_edges_task.delay(current_user.id, threshold)

        return {
            "status": "processing",
            "task_id": task.id,
            "message": "Semantic edge generation started in background"
        }

    # Run synchronously
    try:
        service = SemanticEdgesService(db, current_user.id)
        result = service.generate_edges(threshold=threshold)

        return {
            "status": "completed",
            "edges_created": result.edges_created,
            "edges_deleted": result.edges_deleted,
            "notes_processed": result.notes_processed,
            "threshold": result.threshold
        }

    except Exception as e:
        logger.error(f"Error rebuilding semantic edges: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to rebuild semantic edges")


@router.get("/semantic/stats")
@limiter.limit("60/minute")
async def get_semantic_stats(
    request: Request,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics about semantic edges for the current user.

    Returns:
        Edge count and coverage information
    """
    try:
        service = SemanticEdgesService(db, current_user.id)
        edge_count = service.get_edge_count()

        # Count notes with embeddings
        note_count = db.query(models.Note).filter(
            models.Note.owner_id == current_user.id,
            models.Note.is_trashed == False,
            models.Note.embedding.isnot(None)
        ).count()

        return {
            "semantic_edge_count": edge_count,
            "notes_with_embeddings": note_count,
            "edges_per_note_avg": round(edge_count / max(note_count, 1) * 2, 2)
        }

    except Exception as e:
        logger.error(f"Error getting semantic stats: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to get semantic stats")


# ============================================
# Community Detection (Phase 2)
# ============================================

@router.post("/communities/rebuild")
@limiter.limit("5/minute")
async def rebuild_communities(
    request: Request,
    algorithm: str = Query("louvain", description="Algorithm: 'louvain' or 'leiden'"),
    use_celery: bool = Query(True, description="Use Celery for async processing"),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Run community detection and update cluster assignments.

    This endpoint:
    1. Builds a networkx graph from notes and their connections
    2. Runs Louvain community detection
    3. Updates notes.community_id with cluster assignments
    4. Computes stable positions for Map view

    Args:
        algorithm: Clustering algorithm ('louvain' recommended)
        use_celery: If True, runs as background Celery task

    Returns:
        Task info if async, or result if sync
    """
    logger.info(f"Community rebuild requested by user {current_user.username}")

    if use_celery:
        # Run as Celery background task
        from features.graph.tasks import detect_communities_task
        task = detect_communities_task.delay(current_user.id, algorithm)

        return {
            "status": "processing",
            "task_id": task.id,
            "message": "Community detection started in background"
        }

    # Run synchronously
    try:
        service = ClusteringService(db, current_user.id)
        result = service.detect_communities(algorithm=algorithm)
        notes_updated = service.save_communities(result)
        positions = service.compute_stable_positions(result)
        positions_saved = service.save_positions(positions)

        return {
            "status": "completed",
            "algorithm": algorithm,
            "community_count": result.community_count,
            "modularity": result.modularity,
            "node_count": result.node_count,
            "notes_updated": notes_updated,
            "positions_saved": positions_saved
        }

    except Exception as e:
        logger.error(f"Error rebuilding communities: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to rebuild communities")


@router.get("/communities/stats")
@limiter.limit("60/minute")
async def get_community_stats(
    request: Request,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics about community assignments for the current user.

    Returns:
        Community count and distribution information
    """
    try:
        # Count notes by community
        from sqlalchemy import func

        community_counts = db.query(
            models.Note.community_id,
            func.count(models.Note.id).label("count")
        ).filter(
            models.Note.owner_id == current_user.id,
            models.Note.is_trashed == False
        ).group_by(models.Note.community_id).all()

        # Build response
        communities = []
        unclustered = 0

        for community_id, count in community_counts:
            if community_id is None:
                unclustered = count
            else:
                communities.append({
                    "id": community_id,
                    "node_count": count
                })

        return {
            "community_count": len(communities),
            "communities": communities,
            "unclustered_count": unclustered,
            "total_notes": sum(c["node_count"] for c in communities) + unclustered
        }

    except Exception as e:
        logger.error(f"Error getting community stats: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to get community stats")


# ============================================
# Node Search (for PathFinder autocomplete)
# ============================================

@router.get("/search")
@limiter.limit("60/minute")
async def search_nodes(
    request: Request,
    q: str = Query(
        ...,
        min_length=1,
        description="Search query for node title"
    ),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Search for nodes by title for autocomplete in PathFinder.

    Args:
        q: Search query (case-insensitive partial match)
        limit: Maximum results to return

    Returns:
        List of matching nodes with id, title, type
    """
    logger.debug(f"Node search for '{q}' by user {current_user.username}")

    try:
        results = []

        # Search notes
        notes = db.query(models.Note).filter(
            models.Note.owner_id == current_user.id,
            models.Note.is_trashed == False,
            models.Note.title.ilike(f"%{q}%")
        ).limit(limit).all()

        for note in notes:
            results.append({
                "id": f"note-{note.id}",
                "title": note.title or f"Note {note.id}",
                "type": "note",
            })

        # Search tags
        tags = db.query(models.Tag).filter(
            models.Tag.owner_id == current_user.id,
            models.Tag.name.ilike(f"%{q}%")
        ).limit(limit).all()

        for tag in tags:
            results.append({
                "id": f"tag-{tag.id}",
                "title": tag.name,
                "type": "tag",
            })

        # Search images
        images = db.query(models.Image).filter(
            models.Image.owner_id == current_user.id,
            models.Image.filename.ilike(f"%{q}%")
        ).limit(limit).all()

        for image in images:
            results.append({
                "id": f"image-{image.id}",
                "title": image.filename,
                "type": "image",
            })

        # Sort by relevance (exact matches first)
        q_lower = q.lower()
        results.sort(key=lambda x: (
            0 if x["title"].lower().startswith(q_lower) else 1,
            len(x["title"])
        ))

        logger.info(f"Node search found {len(results)} results for '{q}'")
        return {"nodes": results[:limit]}

    except Exception as e:
        logger.error(f"Error searching nodes: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to search nodes")


# ============================================
# Full Graph Index Rebuild (Phase 2)
# ============================================

@router.post("/index/rebuild")
@limiter.limit("2/minute")
async def rebuild_graph_index(
    request: Request,
    include_semantic: bool = Query(True, description="Generate semantic edges"),
    include_clustering: bool = Query(True, description="Run community detection"),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Full rebuild of graph index including semantic edges and clustering.

    This is a convenience endpoint that triggers both semantic edge generation
    and community detection as a single Celery task.

    Args:
        include_semantic: Generate semantic similarity edges
        include_clustering: Run Louvain community detection

    Returns:
        Task info for tracking progress
    """
    logger.info(f"Full graph index rebuild requested by user {current_user.username}")

    from features.graph.tasks import rebuild_graph_index_task
    task = rebuild_graph_index_task.delay(
        current_user.id,
        include_semantic=include_semantic,
        include_clustering=include_clustering
    )

    return {
        "status": "processing",
        "task_id": task.id,
        "message": "Graph index rebuild started in background",
        "options": {
            "include_semantic": include_semantic,
            "include_clustering": include_clustering
        }
    }
