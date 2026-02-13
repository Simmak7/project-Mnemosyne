"""
NEXUS Celery Tasks

Background tasks for:
- Navigation cache rebuild (triggered after Brain build)
- Consolidation (PageRank, community refresh, missing links)
- Access pattern recording
"""

import logging
from core.celery_app import celery_app
from core.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(
    name="features.nexus.tasks.rebuild_navigation_cache_task",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def rebuild_navigation_cache_task(self, user_id: int) -> dict:
    """Rebuild navigation cache for a user (called after Brain build)."""
    db = SessionLocal()
    try:
        from features.nexus.services.navigation_cache_service import (
            build_navigation_cache,
        )
        result = build_navigation_cache(db, user_id)
        logger.info(f"Navigation cache rebuilt for user {user_id}: {result}")
        return {"status": "success", **result}
    except Exception as e:
        logger.error(f"Navigation cache rebuild failed: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(
    name="features.nexus.tasks.run_consolidation_task",
    bind=True,
    max_retries=1,
    soft_time_limit=540,
    time_limit=600,
)
def run_consolidation_task(self, user_id: int, force: bool = False) -> dict:
    """Run full NEXUS consolidation (Phase 3)."""
    db = SessionLocal()
    try:
        from features.nexus.services.consolidation import run_consolidation
        result = run_consolidation(db, user_id, force=force)
        logger.info(f"Consolidation completed for user {user_id}: {result}")
        return {"status": "success", **result}
    except Exception as e:
        logger.error(f"Consolidation failed for user {user_id}: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(
    name="features.nexus.tasks.record_access_patterns_task",
)
def record_access_patterns_task(
    user_id: int, note_ids: list
) -> dict:
    """Record co-retrieval patterns for a set of notes."""
    if len(note_ids) < 2:
        return {"status": "skipped", "reason": "not enough notes"}

    db = SessionLocal()
    try:
        from sqlalchemy import text
        # Record all pairs
        pairs_recorded = 0
        for i in range(len(note_ids)):
            for j in range(i + 1, min(len(note_ids), i + 6)):
                a, b = min(note_ids[i], note_ids[j]), max(note_ids[i], note_ids[j])
                db.execute(text("""
                    INSERT INTO nexus_access_patterns
                        (owner_id, note_id_a, note_id_b, co_retrieval_count)
                    VALUES (:owner_id, :a, :b, 1)
                    ON CONFLICT (owner_id, note_id_a, note_id_b)
                    DO UPDATE SET
                        co_retrieval_count = nexus_access_patterns.co_retrieval_count + 1,
                        last_co_retrieved_at = NOW()
                """), {"owner_id": user_id, "a": a, "b": b})
                pairs_recorded += 1
        db.commit()
        return {"status": "success", "pairs_recorded": pairs_recorded}
    except Exception as e:
        logger.error(f"Access pattern recording failed: {e}")
        db.rollback()
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
