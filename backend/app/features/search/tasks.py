"""
Celery tasks for search-related background operations.

Tasks:
- generate_note_embedding_task: Generate embedding for a single note
- regenerate_all_embeddings_task: Batch regeneration for all notes
"""

import logging
from typing import Optional

from core.celery_app import celery_app
from core.database import SessionLocal
from models import Note
from features.search.logic.embeddings import generate_embedding, prepare_note_text
from sqlalchemy import select

logger = logging.getLogger(__name__)


@celery_app.task(
    name="features.search.tasks.generate_note_embedding",
    bind=True,
    max_retries=3,
    default_retry_delay=60  # Retry after 1 minute
)
def generate_note_embedding_task(self, note_id: int) -> dict:
    """
    Generate and store embedding for a note.

    This task runs in the background (via Celery) to generate semantic embeddings
    for notes. It combines the note's title and content, generates an embedding
    using Ollama's nomic-embed-text model, and stores it in the database.

    Args:
        note_id: ID of the note to generate embedding for

    Returns:
        dict with status and result information

    Raises:
        Exception: If embedding generation fails after max retries
    """
    db = SessionLocal()

    try:
        logger.info(f"Starting embedding generation for note {note_id}")

        # Fetch the note
        stmt = select(Note).where(Note.id == note_id)
        result = db.execute(stmt)
        note = result.scalar_one_or_none()

        if not note:
            logger.error(f"Note {note_id} not found")
            return {
                "status": "error",
                "note_id": note_id,
                "error": "Note not found"
            }

        # Prepare text for embedding
        text = prepare_note_text(note.title or "", note.content or "")

        if not text.strip():
            logger.warning(f"Note {note_id} has no content, skipping embedding")
            return {
                "status": "skipped",
                "note_id": note_id,
                "reason": "No content"
            }

        # Generate embedding
        try:
            embedding = generate_embedding(text)

            if not embedding:
                error_msg = "Embedding generation returned None"
                logger.error(f"Failed to generate embedding for note {note_id}: {error_msg}")

                # Retry the task
                raise self.retry(exc=Exception(error_msg))

            # Store embedding in database
            note.embedding = embedding
            db.commit()

            logger.info(
                f"Successfully generated and stored embedding for note {note_id} "
                f"({len(embedding)} dimensions)"
            )

            # Also queue chunk generation for RAG
            try:
                from features.rag_chat.tasks import generate_note_chunks_task
                generate_note_chunks_task.delay(note_id, generate_embeddings=True)
                logger.info(f"Queued chunk generation for note {note_id}")
            except Exception as chunk_err:
                logger.warning(f"Failed to queue chunk generation for note {note_id}: {chunk_err}")

            return {
                "status": "success",
                "note_id": note_id,
                "embedding_dimension": len(embedding),
                "text_length": len(text)
            }

        except Exception as e:
            logger.error(
                f"Error generating embedding for note {note_id}: {str(e)}",
                exc_info=True
            )

            # Retry the task (up to max_retries times)
            if self.request.retries < self.max_retries:
                logger.info(
                    f"Retrying embedding generation for note {note_id} "
                    f"(attempt {self.request.retries + 1}/{self.max_retries})"
                )
                raise self.retry(exc=e)
            else:
                logger.error(
                    f"Max retries reached for note {note_id}, giving up"
                )
                return {
                    "status": "failed",
                    "note_id": note_id,
                    "error": str(e),
                    "retries": self.request.retries
                }

    except Exception as e:
        logger.error(
            f"Unexpected error in embedding task for note {note_id}: {str(e)}",
            exc_info=True
        )
        db.rollback()
        raise

    finally:
        db.close()


@celery_app.task(
    name="features.search.tasks.regenerate_all_embeddings",
    bind=True
)
def regenerate_all_embeddings_task(self, owner_id: Optional[int] = None) -> dict:
    """
    Regenerate embeddings for all notes (or all notes for a specific user).

    This is a batch task that queues individual embedding generation tasks
    for all notes in the database. Useful for:
    - Initial population of embeddings after migration
    - Regenerating embeddings after model changes
    - Fixing corrupted embeddings

    Args:
        owner_id: If provided, only regenerate embeddings for this user's notes

    Returns:
        dict with count of queued tasks
    """
    db = SessionLocal()

    try:
        logger.info("Starting batch embedding regeneration")

        # Query all notes (optionally filtered by owner)
        stmt = select(Note.id)
        if owner_id:
            stmt = stmt.where(Note.owner_id == owner_id)
            logger.info(f"Filtering notes for owner_id={owner_id}")

        result = db.execute(stmt)
        note_ids = [row[0] for row in result.fetchall()]

        logger.info(f"Found {len(note_ids)} notes to process")

        # Queue individual tasks
        queued = 0
        failed = 0

        for note_id in note_ids:
            try:
                generate_note_embedding_task.delay(note_id)
                queued += 1
            except Exception as e:
                logger.error(f"Failed to queue task for note {note_id}: {e}")
                failed += 1

        logger.info(
            f"Batch embedding regeneration completed: "
            f"{queued} queued, {failed} failed"
        )

        return {
            "status": "completed",
            "total_notes": len(note_ids),
            "queued": queued,
            "failed": failed,
            "owner_id": owner_id
        }

    except Exception as e:
        logger.error(
            f"Error in batch embedding regeneration: {str(e)}",
            exc_info=True
        )
        raise

    finally:
        db.close()
