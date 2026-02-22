"""
Celery tasks for Mnemosyne Brain operations.

Error categories: transient (retry w/ backoff), permanent (fail now), unknown (retry then fail).
"""

import logging
from datetime import datetime
from celery import Task
from requests.exceptions import ConnectionError, Timeout
from core.celery_app import celery_app
from core import database

logger = logging.getLogger(__name__)
PERMANENT_ERRORS = (FileNotFoundError, ValueError, PermissionError, KeyError)
TRANSIENT_ERRORS = (ConnectionError, Timeout, OSError)
# Shared task decorator defaults for all brain tasks
TASK_DEFAULTS = dict(
    bind=True, base=None, max_retries=3, default_retry_delay=60,
    acks_late=True, reject_on_worker_lost=True,
)


class DatabaseTask(Task):
    """Base task with proper database lifecycle."""
    _db = None

    @property
    def db(self) -> "database.SessionLocal":
        if self._db is None:
            self._db = database.SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs) -> None:
        if self._db is not None:
            self._db.close()
            self._db = None


TASK_DEFAULTS["base"] = DatabaseTask


def _backoff(retries: int) -> int:
    return 120 * (retries + 1)


def _mark_build_failed(db, build_log, error_msg: str) -> None:
    """Safely mark a brain build as failed in the database."""
    try:
        build_log.status = "failed"
        build_log.error_message = str(error_msg)[:500]
        build_log.completed_at = datetime.utcnow()
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass


@celery_app.task(
    **TASK_DEFAULTS,
    name="features.mnemosyne_brain.tasks.build_brain_task",
    time_limit=600, soft_time_limit=540,
)
def build_brain_task(self, user_id: int, build_type: str = "full") -> dict:
    """Build or rebuild the brain for a user."""
    from features.mnemosyne_brain.models.brain_build_log import BrainBuildLog
    from features.mnemosyne_brain.services.brain_builder import build_brain

    logger.info(f"Starting {build_type} brain build for user {user_id}")
    build_log = BrainBuildLog(
        owner_id=user_id, build_type=build_type,
        status="running", progress_pct=0, current_step="Starting",
    )
    self.db.add(build_log)
    self.db.commit()
    self.db.refresh(build_log)

    try:
        build_brain(self.db, user_id, build_log)
        if build_log.status == "completed":
            try:
                from features.nexus.tasks import rebuild_navigation_cache_task
                rebuild_navigation_cache_task.delay(user_id)
            except Exception as e:
                logger.debug(f"NEXUS cache rebuild trigger skipped: {e}")
        return {"build_id": build_log.id, "status": build_log.status}

    except PERMANENT_ERRORS as e:
        logger.error(f"Brain build permanent failure: {e}")
        _mark_build_failed(self.db, build_log, str(e))
        return {"build_id": build_log.id, "status": "failed", "error": str(e)[:200]}
    except TRANSIENT_ERRORS as e:
        logger.warning(f"Brain build transient error: {e}, scheduling retry")
        _mark_build_failed(self.db, build_log, f"Transient: {e}")
        raise self.retry(exc=e, countdown=_backoff(self.request.retries))
    except Exception as e:
        logger.exception(f"Brain build task failed: {e}")
        _mark_build_failed(self.db, build_log, str(e))
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=_backoff(self.request.retries))
        return {"build_id": build_log.id, "status": "failed", "error": str(e)[:200]}


@celery_app.task(
    **TASK_DEFAULTS,
    name="features.mnemosyne_brain.tasks.evolve_memory_task",
)
def evolve_memory_task(self, user_id: int, conversation_id: int) -> dict:
    """Extract learnings from a conversation and append to memory.md."""
    from features.mnemosyne_brain.services.memory_evolver import evolve_memory
    logger.info(f"Evolving memory for user {user_id}, conversation {conversation_id}")

    try:
        evolve_memory(self.db, user_id, conversation_id)
        return {"status": "completed", "user_id": user_id}
    except PERMANENT_ERRORS as e:
        logger.error(f"Memory evolution permanent failure: {e}")
        return {"status": "failed", "error": str(e)[:200]}
    except TRANSIENT_ERRORS as e:
        logger.warning(f"Memory evolution transient error: {e}, scheduling retry")
        raise self.retry(exc=e, countdown=_backoff(self.request.retries))
    except Exception as e:
        logger.error(f"Memory evolution failed: {e}", exc_info=True)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=_backoff(self.request.retries))
        return {"status": "failed", "error": str(e)[:200]}


@celery_app.task(
    **TASK_DEFAULTS,
    name="features.mnemosyne_brain.tasks.update_conversation_summary_task",
)
def update_conversation_summary_task(self, conversation_id: int) -> dict:
    """Async task to update conversation summary (when messages_since >= 5)."""
    from features.mnemosyne_brain.models.brain_conversation import BrainConversation
    from features.mnemosyne_brain.services.conversation_summarizer import (
        should_update_summary, update_conversation_summary,
    )
    logger.info(f"Checking summary update for conversation {conversation_id}")

    try:
        conversation = self.db.query(BrainConversation).get(conversation_id)
        if not conversation:
            return {"status": "skipped", "reason": "Conversation not found"}
        if not should_update_summary(conversation):
            return {"status": "skipped", "reason": "Summary not needed"}
        update_conversation_summary(self.db, conversation)
        return {"status": "completed", "conversation_id": conversation_id}
    except PERMANENT_ERRORS as e:
        logger.error(f"Summary update permanent failure: {e}")
        return {"status": "failed", "error": str(e)[:200]}
    except TRANSIENT_ERRORS as e:
        logger.warning(f"Summary update transient error: {e}, scheduling retry")
        raise self.retry(exc=e, countdown=_backoff(self.request.retries))
    except Exception as e:
        logger.error(f"Summary update failed: {e}", exc_info=True)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=_backoff(self.request.retries))
        return {"status": "failed", "error": str(e)[:200]}


@celery_app.task(
    **TASK_DEFAULTS,
    name="features.mnemosyne_brain.tasks.incremental_brain_update_task",
    time_limit=120, soft_time_limit=90,
)
def incremental_brain_update_task(
    self, user_id: int, note_id: int, change_type: str = "updated",
) -> dict:
    """Incremental brain update when a note changes. Falls back to stale marking."""
    from features.mnemosyne_brain.services.incremental_updater import incremental_update
    logger.info(f"Incremental brain update: user={user_id}, note={note_id}")

    try:
        result = incremental_update(self.db, user_id, note_id, change_type)
        logger.info(f"Incremental update result: {result}")
        return result
    except TRANSIENT_ERRORS as e:
        logger.warning(f"Incremental update transient error: {e}, scheduling retry")
        self.db.rollback()
        raise self.retry(exc=e, countdown=_backoff(self.request.retries))
    except Exception as e:
        logger.warning(f"Incremental update failed, falling back to stale marking: {e}")
        self.db.rollback()
        try:
            mark_brain_stale_task.delay(user_id, note_id)
        except Exception as e2:
            logger.error(f"Stale marking fallback also failed: {e2}")
        return {"status": "fallback_stale", "error": str(e)[:200]}


@celery_app.task(
    **TASK_DEFAULTS,
    name="features.mnemosyne_brain.tasks.mark_brain_stale_task",
)
def mark_brain_stale_task(self, user_id: int, note_id: int = None) -> dict:
    """Mark brain files as stale when notes change."""
    from features.mnemosyne_brain.models.brain_file import BrainFile
    logger.info(f"Marking brain stale for user {user_id}, note_id={note_id}")

    try:
        if note_id:
            for tf in self.db.query(BrainFile).filter(
                BrainFile.owner_id == user_id, BrainFile.file_type == "topic",
            ).all():
                if note_id in (tf.source_note_ids or []):
                    tf.is_stale = True
        else:
            self.db.query(BrainFile).filter(
                BrainFile.owner_id == user_id, BrainFile.file_type == "topic",
            ).update({"is_stale": True})

        self.db.query(BrainFile).filter(
            BrainFile.owner_id == user_id,
            BrainFile.file_key.in_(["askimap", "mnemosyne"]),
        ).update({"is_stale": True}, synchronize_session="fetch")
        self.db.commit()
        return {"status": "completed", "user_id": user_id}
    except TRANSIENT_ERRORS as e:
        self.db.rollback()
        raise self.retry(exc=e, countdown=_backoff(self.request.retries))
    except Exception as e:
        logger.error(f"Mark stale failed: {e}", exc_info=True)
        self.db.rollback()
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=_backoff(self.request.retries))
        return {"status": "failed", "error": str(e)[:200]}
