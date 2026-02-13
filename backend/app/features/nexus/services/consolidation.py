"""
NEXUS Consolidation Engine

Background process that refreshes graph metadata:
1. PageRank: Compute importance scores and store in nexus_importance_scores
2. Community refresh: Call existing ClusteringService
3. Semantic edge refresh: Call existing SemanticEdgesService
4. Missing links: Detect semantically similar unlinked notes
5. Navigation cache: Rebuild cached maps
6. Access patterns: Analyze co-retrieval frequency
"""

import logging
from typing import Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from features.nexus.models import NexusImportanceScore
from features.nexus.services.navigation_cache_service import build_navigation_cache
from features.nexus.services.missing_links import detect_missing_links

logger = logging.getLogger(__name__)


def run_consolidation(
    db: Session,
    owner_id: int,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Run full NEXUS consolidation pipeline.

    Args:
        db: Database session
        owner_id: User ID
        force: Force refresh even if not stale

    Returns:
        Dict with step results
    """
    results = {}

    # Step 1: PageRank
    try:
        pr_result = _run_pagerank(db, owner_id)
        results["pagerank"] = pr_result
    except Exception as e:
        logger.error(f"PageRank step failed: {e}")
        results["pagerank"] = {"status": "failed", "error": str(e)}

    # Step 2: Community refresh
    try:
        comm_result = _refresh_communities(db, owner_id)
        results["communities"] = comm_result
    except Exception as e:
        logger.error(f"Community refresh failed: {e}")
        results["communities"] = {"status": "failed", "error": str(e)}

    # Step 3: Semantic edge refresh
    try:
        sem_result = _refresh_semantic_edges(db, owner_id)
        results["semantic_edges"] = sem_result
    except Exception as e:
        logger.error(f"Semantic edge refresh failed: {e}")
        results["semantic_edges"] = {"status": "failed", "error": str(e)}

    # Step 4: Missing links
    try:
        ml_result = detect_missing_links(db, owner_id)
        results["missing_links"] = ml_result
    except Exception as e:
        logger.error(f"Missing link detection failed: {e}")
        results["missing_links"] = {"status": "failed", "error": str(e)}

    # Step 5: Navigation cache
    try:
        cache_result = build_navigation_cache(db, owner_id)
        results["navigation_cache"] = cache_result
    except Exception as e:
        logger.error(f"Navigation cache build failed: {e}")
        results["navigation_cache"] = {"status": "failed", "error": str(e)}

    logger.info(f"Consolidation complete for user {owner_id}: {results}")
    return results


def _run_pagerank(db: Session, owner_id: int) -> Dict[str, Any]:
    """Compute PageRank and store in nexus_importance_scores."""
    try:
        import networkx as nx
    except ImportError:
        return {"status": "skipped", "reason": "networkx not available"}

    # Build graph
    G = nx.DiGraph()

    # Add wikilink edges
    result = db.execute(text("""
        SELECT nw.source_note_id, nw.target_note_id
        FROM note_links nw
        JOIN notes n1 ON n1.id = nw.source_note_id AND n1.owner_id = :owner_id
        JOIN notes n2 ON n2.id = nw.target_note_id AND n2.owner_id = :owner_id
        WHERE n1.is_trashed = false AND n2.is_trashed = false
    """), {"owner_id": owner_id})

    for row in result:
        G.add_edge(row.source_note_id, row.target_note_id, weight=1.0)

    if G.number_of_nodes() == 0:
        return {"status": "skipped", "reason": "no graph edges"}

    # Compute PageRank
    scores = nx.pagerank(G, alpha=0.85, max_iter=100)

    # Store scores
    updated = 0
    for note_id, score in scores.items():
        existing = db.query(NexusImportanceScore).filter(
            NexusImportanceScore.owner_id == owner_id,
            NexusImportanceScore.note_id == note_id,
        ).first()

        if existing:
            existing.pagerank_score = score
        else:
            db.add(NexusImportanceScore(
                owner_id=owner_id,
                note_id=note_id,
                pagerank_score=score,
            ))
        updated += 1

    db.commit()
    return {"status": "success", "notes_scored": updated}


def _refresh_communities(db: Session, owner_id: int) -> Dict[str, Any]:
    """Run community detection using existing ClusteringService."""
    try:
        from features.graph.services.clustering import ClusteringService, CLUSTERING_AVAILABLE
        if not CLUSTERING_AVAILABLE:
            return {"status": "skipped", "reason": "clustering libs not available"}

        service = ClusteringService(db, owner_id)
        result = service.detect_communities()

        if result.community_count > 0:
            service.save_communities(result)
            return {
                "status": "success",
                "communities": result.community_count,
                "modularity": round(result.modularity, 3),
            }
        return {"status": "skipped", "reason": "no communities detected"}

    except Exception as e:
        return {"status": "failed", "error": str(e)}


def _refresh_semantic_edges(db: Session, owner_id: int) -> Dict[str, Any]:
    """Refresh semantic edges using existing SemanticEdgesService."""
    try:
        from features.graph.services.semantic_edges import SemanticEdgesService
        service = SemanticEdgesService(db, owner_id)
        result = service.generate_edges()
        return {
            "status": "success",
            "edges_created": result.edges_created,
            "notes_processed": result.notes_processed,
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}
