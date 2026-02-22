"""
System Feature - Celery Tasks

Periodic tasks for system maintenance:
- Stuck task recovery: resets items stuck in "processing" status
"""

import logging
from datetime import datetime, timedelta, timezone

from core.celery_app import celery_app
from core.database import SessionLocal
from models import Image, Document

logger = logging.getLogger(__name__)

# Items stuck longer than this threshold are considered abandoned
STUCK_THRESHOLD_MINUTES = 10


@celery_app.task(name="features.system.tasks.recover_stuck_tasks")
def recover_stuck_tasks():
    """
    Reset items stuck in 'processing' status back to 'failed'.

    Runs every 15 minutes via Celery beat. If a Celery worker crashes
    mid-task, images/documents remain in 'processing' forever. This
    task detects items that have been 'processing' longer than the
    threshold and resets them so users can retry.

    Returns:
        dict with counts of recovered images and documents
    """
    db = SessionLocal()
    cutoff = datetime.now(timezone.utc) - timedelta(
        minutes=STUCK_THRESHOLD_MINUTES
    )

    try:
        # Recover stuck images
        stuck_images = (
            db.query(Image)
            .filter(
                Image.ai_analysis_status == "processing",
                Image.uploaded_at < cutoff,
            )
            .all()
        )

        image_count = len(stuck_images)
        for img in stuck_images:
            img.ai_analysis_status = "failed"
            logger.warning(
                "Recovered stuck image id=%d filename=%s "
                "(stuck since %s)",
                img.id,
                img.filename,
                img.uploaded_at,
            )

        # Recover stuck documents
        stuck_docs = (
            db.query(Document)
            .filter(
                Document.ai_analysis_status == "processing",
                Document.uploaded_at < cutoff,
            )
            .all()
        )

        doc_count = len(stuck_docs)
        for doc in stuck_docs:
            doc.ai_analysis_status = "failed"
            logger.warning(
                "Recovered stuck document id=%d filename=%s "
                "(stuck since %s)",
                doc.id,
                doc.filename,
                doc.uploaded_at,
            )

        if image_count or doc_count:
            db.commit()
            logger.info(
                "Stuck task recovery complete: %d images, %d documents reset",
                image_count,
                doc_count,
            )
        else:
            logger.debug("Stuck task recovery: no stuck items found")

        return {
            "recovered_images": image_count,
            "recovered_documents": doc_count,
        }

    except Exception as e:
        db.rollback()
        logger.error("Stuck task recovery failed: %s", str(e), exc_info=True)
        raise
    finally:
        db.close()


def get_stuck_tasks_summary():
    """
    Query current stuck items (for the admin endpoint).

    Returns a dict with lists of stuck image and document summaries.
    """
    db = SessionLocal()
    cutoff = datetime.now(timezone.utc) - timedelta(
        minutes=STUCK_THRESHOLD_MINUTES
    )

    try:
        stuck_images = (
            db.query(Image)
            .filter(
                Image.ai_analysis_status == "processing",
                Image.uploaded_at < cutoff,
            )
            .all()
        )

        stuck_docs = (
            db.query(Document)
            .filter(
                Document.ai_analysis_status == "processing",
                Document.uploaded_at < cutoff,
            )
            .all()
        )

        return {
            "stuck_images": [
                {
                    "id": img.id,
                    "filename": img.filename,
                    "uploaded_at": img.uploaded_at.isoformat()
                    if img.uploaded_at
                    else None,
                    "owner_id": img.owner_id,
                }
                for img in stuck_images
            ],
            "stuck_documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "uploaded_at": doc.uploaded_at.isoformat()
                    if doc.uploaded_at
                    else None,
                    "owner_id": doc.owner_id,
                }
                for doc in stuck_docs
            ],
            "threshold_minutes": STUCK_THRESHOLD_MINUTES,
            "total_stuck": len(stuck_images) + len(stuck_docs),
        }
    finally:
        db.close()
