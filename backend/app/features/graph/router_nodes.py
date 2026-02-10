"""
Graph Feature - Node Operations Endpoints

FastAPI endpoints for node details, neighbors, search, and stats.
"""

import logging
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
# Graph Statistics
# ============================================

@router.get("/stats")
@limiter.limit("60/minute")
async def get_graph_stats(
    request: Request,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get graph statistics for the current user."""
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
    """Get details for a single node."""
    logger.debug(f"Node {node_id} requested by user {current_user.username}")

    try:
        graph_index = GraphIndex(db, current_user.id)
        node = graph_index.get_node(node_id)

        if node is None:
            raise exceptions.ResourceNotFoundException("Node", node_id)

        return schemas.TypedGraphNode(
            id=node.id, type=node.type.value, title=node.title,
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
    """Get IDs of neighboring nodes."""
    logger.debug(f"Neighbors for {node_id} requested by user {current_user.username}")

    try:
        graph_index = GraphIndex(db, current_user.id)
        neighbors = graph_index.get_neighbors(node_id, depth=depth)

        return {"node_id": node_id, "depth": depth, "neighbors": neighbors, "count": len(neighbors)}

    except Exception as e:
        logger.error(f"Error getting neighbors: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to get neighbors")


# ============================================
# Node Search (for PathFinder autocomplete)
# ============================================

@router.get("/search")
@limiter.limit("60/minute")
async def search_nodes(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query for node title"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search for nodes by title for autocomplete in PathFinder."""
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
            results.append({"id": f"tag-{tag.id}", "title": tag.name, "type": "tag"})

        # Search images
        images = db.query(models.Image).filter(
            models.Image.owner_id == current_user.id,
            models.Image.filename.ilike(f"%{q}%")
        ).limit(limit).all()

        for image in images:
            results.append({"id": f"image-{image.id}", "title": image.filename, "type": "image"})

        # Sort by relevance (exact matches first)
        q_lower = q.lower()
        results.sort(key=lambda x: (0 if x["title"].lower().startswith(q_lower) else 1, len(x["title"])))

        logger.info(f"Node search found {len(results)} results for '{q}'")
        return {"nodes": results[:limit]}

    except Exception as e:
        logger.error(f"Error searching nodes: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to search nodes")
