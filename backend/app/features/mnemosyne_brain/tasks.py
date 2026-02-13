"""
Celery tasks for Mnemosyne Brain operations.

Tasks:
- build_brain_task: Full or partial brain rebuild
- evolve_memory_task: Post-conversation memory evolution
- incremental_brain_update_task: Incremental topic update on note change
- mark_brain_stale_task: Mark affected topics as stale (fallback)
"""

import logging
from datetime import datetime

from celery import Task
from core.celery_app import celery_app
from core import database

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with proper database lifecycle."""
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = database.SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="features.mnemosyne_brain.tasks.build_brain_task",
    max_retries=1,
    default_retry_delay=120,
    time_limit=600,
    soft_time_limit=540,
)
def build_brain_task(self, user_id: int, build_type: str = "full"):
    """
    Build or rebuild the brain for a user.

    Args:
        user_id: Owner ID
        build_type: "full" or "partial"
    """
    from features.mnemosyne_brain.models.brain_build_log import BrainBuildLog
    from features.mnemosyne_brain.services.brain_builder import build_brain

    logger.info(f"Starting {build_type} brain build for user {user_id}")

    # Create build log
    build_log = BrainBuildLog(
        owner_id=user_id,
        build_type=build_type,
        status="running",
        progress_pct=0,
        current_step="Starting",
    )
    self.db.add(build_log)
    self.db.commit()
    self.db.refresh(build_log)

    try:
        build_brain(self.db, user_id, build_log)

        # Trigger NEXUS navigation cache rebuild after successful brain build
        if build_log.status == "completed":
            try:
                from features.nexus.tasks import rebuild_navigation_cache_task
                rebuild_navigation_cache_task.delay(user_id)
                logger.info(f"Triggered NEXUS cache rebuild for user {user_id}")
            except Exception as e:
                logger.debug(f"NEXUS cache rebuild trigger skipped: {e}")

    except Exception as e:
        logger.exception(f"Brain build task failed: {e}")
        try:
            build_log.status = "failed"
            build_log.error_message = str(e)[:500]
            build_log.completed_at = datetime.utcnow()
            self.db.commit()
        except Exception:
            self.db.rollback()

    return {"build_id": build_log.id, "status": build_log.status}


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="features.mnemosyne_brain.tasks.evolve_memory_task",
    max_retries=2,
    default_retry_delay=30,
)
def evolve_memory_task(self, user_id: int, conversation_id: int):
    """
    Extract learnings from a conversation and append to memory.md.

    Args:
        user_id: Owner ID
        conversation_id: Brain conversation ID
    """
    from features.mnemosyne_brain.services.memory_evolver import evolve_memory

    logger.info(f"Evolving memory for user {user_id}, conversation {conversation_id}")

    try:
        evolve_memory(self.db, user_id, conversation_id)
    except Exception as e:
        logger.error(f"Memory evolution failed: {e}")


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="features.mnemosyne_brain.tasks.update_conversation_summary_task",
    max_retries=2,
    default_retry_delay=30,
)
def update_conversation_summary_task(self, conversation_id: int):
    """
    Async task to update conversation summary.

    Called after responses when messages_since_summary >= 5.
    """
    from features.mnemosyne_brain.models.brain_conversation import BrainConversation
    from features.mnemosyne_brain.services.conversation_summarizer import (
        should_update_summary,
        update_conversation_summary,
    )

    logger.info(f"Checking summary update for conversation {conversation_id}")

    try:
        conversation = self.db.query(BrainConversation).get(conversation_id)
        if conversation and should_update_summary(conversation):
            update_conversation_summary(self.db, conversation)
    except Exception as e:
        logger.error(f"Summary update failed: {e}")


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="features.mnemosyne_brain.tasks.incremental_brain_update_task",
    max_retries=1,
    default_retry_delay=15,
    time_limit=120,
    soft_time_limit=90,
)
def incremental_brain_update_task(self, user_id: int, note_id: int, change_type: str = "updated"):
    """
    Attempt incremental brain update when a note changes.

    Regenerates only the affected topic(s) instead of a full rebuild.
    Falls back to marking brain as stale on failure.
    """
    from features.mnemosyne_brain.services.incremental_updater import incremental_update

    logger.info(f"Incremental brain update: user={user_id}, note={note_id}, type={change_type}")

    try:
        result = incremental_update(self.db, user_id, note_id, change_type)
        logger.info(f"Incremental update result: {result}")
        return result
    except Exception as e:
        logger.warning(f"Incremental update failed, falling back to stale marking: {e}")
        self.db.rollback()
        try:
            mark_brain_stale_task.delay(user_id, note_id)
        except Exception as e2:
            logger.error(f"Stale marking fallback also failed: {e2}")
        return {"status": "fallback_stale", "error": str(e)[:200]}


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="features.mnemosyne_brain.tasks.mark_brain_stale_task",
    max_retries=1,
    default_retry_delay=10,
)
def mark_brain_stale_task(self, user_id: int, note_id: int = None):
    """
    Mark brain files as stale when notes change.

    If note_id is provided, marks only the topic containing that note.
    Otherwise marks all topics.
    """
    from features.mnemosyne_brain.models.brain_file import BrainFile
    from sqlalchemy import cast
    from sqlalchemy.dialects.postgresql import JSONB

    logger.info(f"Marking brain stale for user {user_id}, note_id={note_id}")

    try:
        if note_id:
            # Find topic files that include this note
            topic_files = (
                self.db.query(BrainFile)
                .filter(
                    BrainFile.owner_id == user_id,
                    BrainFile.file_type == "topic",
                )
                .all()
            )
            for tf in topic_files:
                source_ids = tf.source_note_ids or []
                if note_id in source_ids:
                    tf.is_stale = True
        else:
            # Mark all topics stale
            self.db.query(BrainFile).filter(
                BrainFile.owner_id == user_id,
                BrainFile.file_type == "topic",
            ).update({"is_stale": True})

        # Also mark askimap and mnemosyne as stale
        self.db.query(BrainFile).filter(
            BrainFile.owner_id == user_id,
            BrainFile.file_key.in_(["askimap", "mnemosyne"]),
        ).update({"is_stale": True}, synchronize_session="fetch")

        self.db.commit()
    except Exception as e:
        logger.error(f"Mark stale failed: {e}")
        self.db.rollback()
