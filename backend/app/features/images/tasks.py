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

AI Models (via ModelRouter):
- llama3.2-vision:11b (stable, 4.7GB)
- qwen2.5vl:7b-q4_K_M (experimental, quantized)
"""

from celery import Task
from core.celery_app import celery_app
import logging
from pathlib import Path

from core import database, config
import crud
from model_router import ModelRouter
from features.albums.service import AlbumService
from features.images.tasks_helpers import (
    extract_image_metadata,
    generate_note_title,
    format_note_content,
    extract_tags_from_ai_response,
)

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task that provides database session with proper lifecycle management."""
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = database.SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """Close database session after task completes."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(bind=True, base=DatabaseTask, name="features.images.tasks.analyze_image")
def analyze_image_task(self, image_id: int, image_path: str, prompt: str, album_id: int = None):
    """
    Celery task to analyze an image with Ollama AI in the background.

    Task flow:
    1. Update image status to 'processing'
    2. Call AI model via ModelRouter (handles model selection)
    3. Extract tags and wikilinks from AI response
    4. Create note with formatted content
    5. Link image to note
    6. Add tags to both image and note
    7. Add image to album (if album_id provided)

    Args:
        image_id: Database ID of the image
        image_path: File system path to the image
        prompt: Analysis prompt for the AI (optional, router selects if empty)
        album_id: Album ID to add image to after analysis (optional)

    Returns:
        dict: Task result with status and analysis text
    """
    logger.info(f"[Task {self.request.id}] Starting AI analysis for image {image_id}")

    try:
        # Update image status to processing
        crud.update_image_analysis_result(
            db=self.db,
            image_id=image_id,
            status="processing"
        )
        logger.debug(f"[Task {self.request.id}] Image {image_id} status updated to processing")

        # Initialize model router
        router = ModelRouter(ollama_host=config.OLLAMA_HOST)

        logger.debug(f"[Task {self.request.id}] Routing analysis request for image {image_id}")

        try:
            # Call model router (handles model selection, prompt selection, and API call)
            if prompt:
                result = router.analyze_image(
                    image_path=image_path,
                    custom_prompt=prompt,
                    timeout=300
                )
            else:
                # No custom prompt - let router select based on PROMPT_ROLLOUT_PERCENT
                result = router.analyze_image(
                    image_path=image_path,
                    timeout=300
                )

            # Check if analysis was successful
            if result.get("status") == "success":
                analysis_text = result.get("response", "No response from AI")
                logger.info(f"[Task {self.request.id}] AI analysis successful for image {image_id}")

                # Update image analysis result
                crud.update_image_analysis_result(
                    db=self.db,
                    image_id=image_id,
                    status="completed",
                    result=analysis_text
                )

                # Extract tags and wikilinks from AI response
                extracted_tags = []
                extracted_wikilinks = []

                try:
                    # Use adaptive prompt metadata if available
                    content_metadata = result.get("content_metadata", {})

                    if content_metadata and content_metadata.get("tags"):
                        extracted_tags = content_metadata["tags"]
                        logger.info(f"[Task {self.request.id}] Using adaptive prompt tags: {len(extracted_tags)} tags")
                    else:
                        extracted_tags = extract_tags_from_ai_response(analysis_text)
                        logger.info(f"[Task {self.request.id}] Using legacy tag extraction: {len(extracted_tags)} tags")

                    # Extract wikilinks from metadata
                    extracted_wikilinks = content_metadata.get("wikilinks", []) if content_metadata else []
                    if extracted_wikilinks:
                        logger.info(f"[Task {self.request.id}] Extracted {len(extracted_wikilinks)} wikilinks")

                    image = crud.get_image(self.db, image_id=image_id)

                    if image and extracted_tags:
                        logger.info(f"[Task {self.request.id}] Extracted {len(extracted_tags)} tags: {extracted_tags}")

                        for tag_name in extracted_tags:
                            try:
                                crud.add_tag_to_image(
                                    db=self.db,
                                    image_id=image_id,
                                    tag_name=tag_name,
                                    owner_id=image.owner_id
                                )
                            except Exception as tag_err:
                                logger.warning(f"[Task {self.request.id}] Failed to add tag '{tag_name}': {str(tag_err)}")
                                self.db.rollback()

                        logger.info(f"[Task {self.request.id}] Tags added to image {image_id}")
                except Exception as e:
                    logger.warning(f"[Task {self.request.id}] Failed to extract/add tags: {str(e)}")
                    self.db.rollback()

                # Create note with analysis
                try:
                    image = crud.get_image(self.db, image_id=image_id)

                    # Extract EXIF metadata for better title generation
                    metadata = extract_image_metadata(image_path)

                    # Generate meaningful title from AI analysis
                    note_title = generate_note_title(
                        ai_analysis=analysis_text,
                        image_filename=Path(image_path).name,
                        metadata=metadata
                    )

                    # Format note content with tags and wikilinks
                    note_content = format_note_content(
                        ai_analysis=analysis_text,
                        tags=extracted_tags,
                        wikilinks=extracted_wikilinks
                    )

                    note = crud.create_note(
                        db=self.db,
                        title=note_title,
                        content=note_content,
                        owner_id=image.owner_id if image else None
                    )
                    logger.info(f"[Task {self.request.id}] Note created: ID {note.id}, title '{note_title}'")

                    # Auto-set image display_name from note title
                    try:
                        crud.update_image_display_name(
                            db=self.db,
                            image_id=image_id,
                            display_name=note_title
                        )
                        logger.info(f"[Task {self.request.id}] Image display_name set to '{note_title}'")
                    except Exception as name_err:
                        logger.warning(f"[Task {self.request.id}] Failed to set display_name: {str(name_err)}")
                        self.db.rollback()

                    # Link the note to the image
                    try:
                        crud.add_image_to_note(db=self.db, image_id=image_id, note_id=note.id)
                        logger.info(f"[Task {self.request.id}] Linked note {note.id} to image {image_id}")
                    except Exception as link_err:
                        logger.warning(f"[Task {self.request.id}] Failed to link note to image: {str(link_err)}")
                        self.db.rollback()

                    # Add tags to the note
                    if extracted_tags:
                        for tag_name in extracted_tags:
                            try:
                                crud.add_tag_to_note(
                                    db=self.db,
                                    note_id=note.id,
                                    tag_name=tag_name,
                                    owner_id=image.owner_id
                                )
                            except Exception as tag_err:
                                logger.warning(f"[Task {self.request.id}] Failed to add tag '{tag_name}' to note: {str(tag_err)}")
                                self.db.rollback()
                except Exception as e:
                    logger.error(f"[Task {self.request.id}] Failed to create note: {str(e)}", exc_info=True)
                    self.db.rollback()

                # Add image to album if album_id was provided
                if album_id:
                    try:
                        image = crud.get_image(self.db, image_id=image_id)
                        if image:
                            added = AlbumService.add_images_to_album(
                                db=self.db,
                                album_id=album_id,
                                owner_id=image.owner_id,
                                image_ids=[image_id]
                            )
                            if added > 0:
                                logger.info(f"[Task {self.request.id}] Added image {image_id} to album {album_id}")
                            else:
                                logger.warning(f"[Task {self.request.id}] Image {image_id} already in album {album_id} or album not found")
                    except Exception as album_err:
                        logger.warning(f"[Task {self.request.id}] Failed to add image to album {album_id}: {str(album_err)}")
                        self.db.rollback()

                return {
                    "status": "completed",
                    "analysis": analysis_text,
                    "image_id": image_id
                }

            else:
                # Handle router error response
                error_msg = result.get("error", "Unknown error from model router")
                model_used = result.get("model", "unknown")
                logger.error(f"[Task {self.request.id}] Model router error ({model_used}): {error_msg}")

                crud.update_image_analysis_result(
                    db=self.db,
                    image_id=image_id,
                    status="failed",
                    result=f"Model: {model_used} - {error_msg}"
                )

                # Retry if connection error detected
                if "connect" in error_msg.lower() or "connection" in error_msg.lower():
                    logger.info(f"[Task {self.request.id}] Connection error detected, retrying in 60s")
                    raise self.retry(exc=Exception(error_msg), countdown=60, max_retries=3)

                return {"status": "failed", "error": error_msg}

        except FileNotFoundError as e:
            error_msg = f"Image file not found: {str(e)}"
            logger.error(f"[Task {self.request.id}] {error_msg}")
            crud.update_image_analysis_result(
                db=self.db,
                image_id=image_id,
                status="failed",
                result=error_msg
            )
            return {"status": "failed", "error": error_msg}

        except Exception as e:
            error_msg = f"Unexpected error during analysis: {str(e)}"
            logger.error(f"[Task {self.request.id}] {error_msg}", exc_info=True)
            crud.update_image_analysis_result(
                db=self.db,
                image_id=image_id,
                status="failed",
                result=error_msg
            )
            return {"status": "failed", "error": error_msg}

    except Exception as e:
        error_msg = f"Unexpected error during AI analysis: {str(e)}"
        logger.error(f"[Task {self.request.id}] {error_msg}", exc_info=True)
        crud.update_image_analysis_result(
            db=self.db,
            image_id=image_id,
            status="failed",
            result=error_msg
        )
        return {"status": "failed", "error": error_msg}
