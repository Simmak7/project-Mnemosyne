"""
Graph Feature - Celery Tasks

Background tasks for semantic edge generation and community detection.
"""

from core.celery_app import celery_app
from core.database import SessionLocal
from core.logging_config import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, name="features.graph.tasks.generate_semantic_edges")
def generate_semantic_edges_task(self, user_id: int, threshold: float = 0.7):
    """
    Generate semantic similarity edges for a user's notes.

    This task:
    1. Loads all note embeddings for the user
    2. Computes pairwise cosine similarity
    3. Creates edges where similarity > threshold
    4. Stores results in semantic_edges table

    Args:
        user_id: User ID to process
        threshold: Minimum similarity score (0.0 - 1.0)

    Returns:
        Dict with task results
    """
    logger.info(f"Starting semantic edge generation for user {user_id}")

    db = SessionLocal()
    try:
        from features.graph.services.semantic_edges import SemanticEdgesService

        service = SemanticEdgesService(db, user_id)
        result = service.generate_edges(threshold=threshold)

        return {
            "status": "completed",
            "user_id": user_id,
            "edges_created": result.edges_created,
            "edges_deleted": result.edges_deleted,
            "notes_processed": result.notes_processed,
            "threshold": result.threshold,
        }

    except Exception as e:
        logger.error(f"Semantic edge generation failed for user {user_id}: {e}")
        raise

    finally:
        db.close()


@celery_app.task(bind=True, name="features.graph.tasks.detect_communities")
def detect_communities_task(self, user_id: int, algorithm: str = "louvain"):
    """
    Run community detection on a user's knowledge graph.

    This task:
    1. Builds networkx graph from notes and their connections
    2. Runs Louvain community detection
    3. Updates notes.community_id with cluster assignments
    4. Computes stable positions for Map view

    Args:
        user_id: User ID to process
        algorithm: Clustering algorithm ('louvain' or 'leiden')

    Returns:
        Dict with task results
    """
    logger.info(f"Starting community detection for user {user_id} (algo={algorithm})")

    db = SessionLocal()
    try:
        from features.graph.services.clustering import ClusteringService

        service = ClusteringService(db, user_id)

        # Detect communities
        result = service.detect_communities(algorithm=algorithm)

        # Save community assignments
        notes_updated = service.save_communities(result)

        # Compute and save stable positions
        positions = service.compute_stable_positions(result)
        positions_saved = service.save_positions(positions)

        return {
            "status": "completed",
            "user_id": user_id,
            "algorithm": algorithm,
            "community_count": result.community_count,
            "modularity": result.modularity,
            "node_count": result.node_count,
            "notes_updated": notes_updated,
            "positions_saved": positions_saved,
        }

    except Exception as e:
        logger.error(f"Community detection failed for user {user_id}: {e}")
        raise

    finally:
        db.close()


@celery_app.task(bind=True, name="features.graph.tasks.rebuild_graph_index")
def rebuild_graph_index_task(
    self,
    user_id: int,
    include_semantic: bool = True,
    include_clustering: bool = True
):
    """
    Full rebuild of graph index including semantic edges and clustering.

    This is a convenience task that runs both semantic edge generation
    and community detection in sequence.

    Args:
        user_id: User ID to process
        include_semantic: Generate semantic edges
        include_clustering: Run community detection

    Returns:
        Dict with combined results
    """
    logger.info(f"Starting full graph index rebuild for user {user_id}")

    results = {
        "user_id": user_id,
        "status": "completed",
    }

    # Generate semantic edges
    if include_semantic:
        semantic_result = generate_semantic_edges_task(user_id)
        results["semantic"] = semantic_result

    # Run community detection
    if include_clustering:
        clustering_result = detect_communities_task(user_id)
        results["clustering"] = clustering_result

    logger.info(f"Graph index rebuild complete for user {user_id}")
    return results
