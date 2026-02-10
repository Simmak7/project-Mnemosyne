"""
Graph Feature - AI Operations Endpoints (Semantic, Clustering)

FastAPI endpoints for semantic edges and community detection.
"""

import logging
from fastapi import APIRouter, Depends, Request, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.database import get_db
from core.auth import get_current_active_user
from core import exceptions
from slowapi import Limiter
from slowapi.util import get_remote_address

from features.graph.services import ClusteringService, SemanticEdgesService
import models

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/graph", tags=["Graph V2"])


# ============================================
# Semantic Edges
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

    Generates edges between notes that are semantically similar based on embeddings.
    Notes must have embeddings (from search indexing) to be included.
    """
    logger.info(f"Semantic edge rebuild requested by user {current_user.username}")

    if use_celery:
        from features.graph.tasks import generate_semantic_edges_task
        task = generate_semantic_edges_task.delay(current_user.id, threshold)

        return {
            "status": "processing",
            "task_id": task.id,
            "message": "Semantic edge generation started in background"
        }

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


@router.delete("/semantic/clear")
@limiter.limit("5/minute")
async def clear_semantic_edges(
    request: Request,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete all semantic edges for the current user, reverting to organic links only."""
    try:
        service = SemanticEdgesService(db, current_user.id)
        deleted = service._delete_existing_edges()
        db.commit()
        return {"status": "completed", "edges_deleted": deleted}
    except Exception as e:
        logger.error(f"Error clearing semantic edges: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to clear semantic edges")


@router.get("/semantic/stats")
@limiter.limit("60/minute")
async def get_semantic_stats(
    request: Request,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get statistics about semantic edges for the current user."""
    try:
        service = SemanticEdgesService(db, current_user.id)
        edge_count = service.get_edge_count()

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
# Community Detection
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

    Builds a networkx graph, runs Louvain community detection,
    updates notes.community_id, and computes stable positions.
    """
    logger.info(f"Community rebuild requested by user {current_user.username}")

    if use_celery:
        from features.graph.tasks import detect_communities_task
        task = detect_communities_task.delay(current_user.id, algorithm)

        return {
            "status": "processing",
            "task_id": task.id,
            "message": "Community detection started in background"
        }

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
    """Get statistics about community assignments for the current user."""
    try:
        community_counts = db.query(
            models.Note.community_id,
            func.count(models.Note.id).label("count")
        ).filter(
            models.Note.owner_id == current_user.id,
            models.Note.is_trashed == False
        ).group_by(models.Note.community_id).all()

        communities = []
        unclustered = 0

        for community_id, count in community_counts:
            if community_id is None:
                unclustered = count
            else:
                communities.append({"id": community_id, "node_count": count})

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
# Full Graph Index Rebuild
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

    Convenience endpoint that triggers both semantic edge generation
    and community detection as a single Celery task.
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
