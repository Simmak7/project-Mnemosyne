"""
Celery tasks for image processing and AI analysis.

Tasks:
- analyze_image_task: Analyze image with Ollama AI (30-60s async)

Workflow:
1. Image uploaded via API (instant response with task_id)
2. Celery worker picks up task from Redis queue
3. AI model analyzes image (llama3.2-vision or qwen2.5vl)
4. Note created from AI analysis with extracted tags/wikilinks
5. Image linked to note via image_note_relations table
6. User polls task status until completion

Error handling uses categorised retries:
- Transient (connection/timeout): exponential backoff retries
- Permanent (file not found, bad format): fail immediately
- Unknown: retry up to max_retries, then fail with message

Two-phase commit pattern:
  Phase 1 - Save AI analysis result and mark image completed (MUST succeed)
  Phase 2 - Add tags, create note, link to album (best-effort, failures safe)
"""

from celery import Task
from core.celery_app import celery_app
import logging
from requests.exceptions import ConnectionError, Timeout

from core import database, config
import crud
from model_router import ModelRouter
from features.images.tasks_enrichment import (
    extract_tags,
    add_tags_to_image,
    create_and_link_note,
    add_to_album,
)

logger = logging.getLogger(__name__)

# Errors that should never be retried
PERMANENT_ERRORS = (FileNotFoundError, ValueError, PermissionError)


class DatabaseTask(Task):
    """Base task that provides database session with proper lifecycle management."""
    _db = None

    @property
    def db(self) -> "database.SessionLocal":
        if self._db is None:
            self._db = database.SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs) -> None:
        """Close database session after task completes."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="features.images.tasks.analyze_image",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    reject_on_worker_lost=True,
)
def analyze_image_task(
    self,
    image_id: int,
    image_path: str,
    prompt: str,
    album_id: int = None,
    auto_tagging: bool = True,
    max_tags: int = 10,
    auto_create_note: bool = True,
    vision_model: str = None,
) -> dict:
    """
    Celery task to analyze an image with Ollama AI in the background.

    Uses two-phase commit: core analysis is saved first, then best-effort
    enrichment (tags, notes, album) runs without risking the analysis data.
    """
    logger.info(f"[Task {self.request.id}] Starting AI analysis for image {image_id}")

    try:
        crud.update_image_analysis_result(db=self.db, image_id=image_id, status="processing")

        # Call AI model via ModelRouter (with optional user-selected vision model)
        router = ModelRouter(ollama_host=config.OLLAMA_HOST, vision_model=vision_model)
        result = _call_model_router(router, image_path, prompt)

        if result.get("status") != "success":
            return _handle_router_error(self, image_id, result)

        analysis_text = result.get("response", "No response from AI")
        logger.info(f"[Task {self.request.id}] AI analysis successful for image {image_id}")

        # ── Phase 1: Commit core analysis (must succeed) ──
        # Image analysis data is committed BEFORE any tag/note operations
        # so a tag failure cannot roll back the analysis result.
        crud.update_image_analysis_result(
            db=self.db, image_id=image_id, status="completed", result=analysis_text,
        )
        logger.info(f"[Task {self.request.id}] Phase 1 complete: analysis saved")

        # ── Phase 2: Best-effort enrichment (tags, note, album) ──
        image = crud.get_image(self.db, image_id=image_id)
        content_metadata = result.get("content_metadata", {})

        extracted_tags = extract_tags(
            self.request.id, analysis_text, content_metadata, auto_tagging, max_tags,
        )
        wikilinks = (content_metadata.get("wikilinks", []) if content_metadata else [])

        if image and extracted_tags:
            add_tags_to_image(self.db, self.request.id, image, extracted_tags)

        if auto_create_note and image:
            create_and_link_note(
                self.db, self.request.id, image, image_path,
                analysis_text, extracted_tags, wikilinks,
            )

        if album_id:
            add_to_album(self.db, self.request.id, image_id, album_id)

        return {"status": "completed", "analysis": analysis_text, "image_id": image_id}

    except PERMANENT_ERRORS as e:
        error_msg = f"Permanent error: {e}"
        logger.error(f"[Task {self.request.id}] {error_msg}")
        _mark_image_failed(self.db, image_id, error_msg)
        return {"status": "failed", "error": error_msg}

    except (ConnectionError, Timeout, OSError) as e:
        error_msg = f"Transient error: {e}"
        logger.warning(f"[Task {self.request.id}] {error_msg}, scheduling retry")
        _mark_image_failed(self.db, image_id, error_msg)
        raise self.retry(exc=e, countdown=120 * (self.request.retries + 1))

    except Exception as e:
        error_msg = f"Unexpected error during AI analysis: {e}"
        logger.error(f"[Task {self.request.id}] {error_msg}", exc_info=True)
        _mark_image_failed(self.db, image_id, error_msg)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=120 * (self.request.retries + 1))
        return {"status": "failed", "error": error_msg}


# ── Private helpers ───────────────────────────────────────────────


def _mark_image_failed(db, image_id: int, error_msg: str) -> None:
    """Safely mark image as failed, tolerating DB errors."""
    try:
        crud.update_image_analysis_result(
            db=db, image_id=image_id, status="failed", result=error_msg[:500],
        )
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass


def _call_model_router(router: ModelRouter, image_path: str, prompt: str) -> dict:
    """Call AI model, with or without custom prompt."""
    if prompt:
        return router.analyze_image(image_path=image_path, custom_prompt=prompt, timeout=300)
    return router.analyze_image(image_path=image_path, timeout=300)


def _handle_router_error(task, image_id: int, result: dict) -> dict:
    """Handle non-success response from model router."""
    error_msg = result.get("error", "Unknown error from model router")
    model_used = result.get("model", "unknown")
    logger.error(f"[Task {task.request.id}] Model router error ({model_used}): {error_msg}")

    _mark_image_failed(task.db, image_id, f"Model: {model_used} - {error_msg}")

    # Retry transient connection errors from the router
    if any(kw in error_msg.lower() for kw in ("connect", "timeout", "refused")):
        raise task.retry(exc=Exception(error_msg), countdown=120 * (task.request.retries + 1))

    return {"status": "failed", "error": error_msg}
