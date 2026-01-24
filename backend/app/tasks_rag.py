"""
Celery tasks for RAG (Retrieval-Augmented Generation) system.

Background tasks for:
- Generating chunks for notes and images
- Generating embeddings for chunks
- Backfilling existing content
"""

import logging
from typing import Optional, List

from core.celery_app import celery_app
from core.database import SessionLocal
from models import Note, Image, NoteChunk, ImageChunk
from embeddings import generate_embedding
from rag.chunking import chunk_note_content, chunk_image_analysis, ChunkResult
from sqlalchemy import select, delete

logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks_rag.generate_note_chunks",
    bind=True,
    max_retries=3,
    default_retry_delay=30
)
def generate_note_chunks_task(self, note_id: int, generate_embeddings: bool = True) -> dict:
    """
    Generate chunks for a note and optionally generate embeddings.

    This task:
    1. Fetches the note content
    2. Chunks it into paragraphs
    3. Stores chunks in note_chunks table
    4. Optionally generates embeddings for each chunk

    Args:
        note_id: ID of the note to chunk
        generate_embeddings: Whether to generate embeddings for chunks

    Returns:
        dict with status and chunk count
    """
    db = SessionLocal()

    try:
        logger.info(f"Starting chunk generation for note {note_id}")

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

        if not note.content or not note.content.strip():
            logger.warning(f"Note {note_id} has no content, skipping chunking")
            return {
                "status": "skipped",
                "note_id": note_id,
                "reason": "No content"
            }

        # Delete existing chunks for this note (re-chunking)
        delete_stmt = delete(NoteChunk).where(NoteChunk.note_id == note_id)
        db.execute(delete_stmt)
        db.commit()

        # Generate chunks
        chunks = chunk_note_content(note.content, note_id)

        if not chunks:
            logger.warning(f"No chunks generated for note {note_id}")
            return {
                "status": "skipped",
                "note_id": note_id,
                "reason": "No chunks generated"
            }

        # Store chunks
        chunks_created = 0
        embeddings_generated = 0

        for chunk in chunks:
            db_chunk = NoteChunk(
                note_id=note_id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                chunk_type=chunk.chunk_type,
                char_start=chunk.char_start,
                char_end=chunk.char_end,
                embedding=None
            )

            # Generate embedding if requested
            if generate_embeddings:
                try:
                    embedding = generate_embedding(chunk.content)
                    if embedding:
                        db_chunk.embedding = embedding
                        embeddings_generated += 1
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for chunk: {e}")

            db.add(db_chunk)
            chunks_created += 1

        db.commit()

        logger.info(
            f"Created {chunks_created} chunks for note {note_id} "
            f"({embeddings_generated} embeddings generated)"
        )

        return {
            "status": "success",
            "note_id": note_id,
            "chunks_created": chunks_created,
            "embeddings_generated": embeddings_generated
        }

    except Exception as e:
        logger.error(f"Error chunking note {note_id}: {str(e)}", exc_info=True)
        db.rollback()

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying chunk generation for note {note_id}")
            raise self.retry(exc=e)
        else:
            return {
                "status": "failed",
                "note_id": note_id,
                "error": str(e)
            }

    finally:
        db.close()


@celery_app.task(
    name="tasks_rag.generate_image_chunks",
    bind=True,
    max_retries=3,
    default_retry_delay=30
)
def generate_image_chunks_task(self, image_id: int, generate_embeddings: bool = True) -> dict:
    """
    Generate chunks for an image's AI analysis and optionally generate embeddings.

    This task:
    1. Fetches the image's AI analysis result
    2. Chunks it into sections
    3. Stores chunks in image_chunks table
    4. Optionally generates embeddings for each chunk

    Args:
        image_id: ID of the image to chunk
        generate_embeddings: Whether to generate embeddings for chunks

    Returns:
        dict with status and chunk count
    """
    db = SessionLocal()

    try:
        logger.info(f"Starting chunk generation for image {image_id}")

        # Fetch the image
        stmt = select(Image).where(Image.id == image_id)
        result = db.execute(stmt)
        image = result.scalar_one_or_none()

        if not image:
            logger.error(f"Image {image_id} not found")
            return {
                "status": "error",
                "image_id": image_id,
                "error": "Image not found"
            }

        if not image.ai_analysis_result or not image.ai_analysis_result.strip():
            logger.warning(f"Image {image_id} has no AI analysis, skipping chunking")
            return {
                "status": "skipped",
                "image_id": image_id,
                "reason": "No AI analysis"
            }

        # Delete existing chunks for this image (re-chunking)
        delete_stmt = delete(ImageChunk).where(ImageChunk.image_id == image_id)
        db.execute(delete_stmt)
        db.commit()

        # Generate chunks
        chunks = chunk_image_analysis(image.ai_analysis_result, image_id)

        if not chunks:
            logger.warning(f"No chunks generated for image {image_id}")
            return {
                "status": "skipped",
                "image_id": image_id,
                "reason": "No chunks generated"
            }

        # Store chunks
        chunks_created = 0
        embeddings_generated = 0

        for chunk in chunks:
            db_chunk = ImageChunk(
                image_id=image_id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                embedding=None
            )

            # Generate embedding if requested
            if generate_embeddings:
                try:
                    embedding = generate_embedding(chunk.content)
                    if embedding:
                        db_chunk.embedding = embedding
                        embeddings_generated += 1
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for image chunk: {e}")

            db.add(db_chunk)
            chunks_created += 1

        db.commit()

        logger.info(
            f"Created {chunks_created} chunks for image {image_id} "
            f"({embeddings_generated} embeddings generated)"
        )

        return {
            "status": "success",
            "image_id": image_id,
            "chunks_created": chunks_created,
            "embeddings_generated": embeddings_generated
        }

    except Exception as e:
        logger.error(f"Error chunking image {image_id}: {str(e)}", exc_info=True)
        db.rollback()

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying chunk generation for image {image_id}")
            raise self.retry(exc=e)
        else:
            return {
                "status": "failed",
                "image_id": image_id,
                "error": str(e)
            }

    finally:
        db.close()


@celery_app.task(
    name="tasks_rag.backfill_note_chunks",
    bind=True
)
def backfill_note_chunks_task(self, owner_id: Optional[int] = None) -> dict:
    """
    Backfill chunks for all existing notes.

    This batch task queues individual chunk generation tasks for all notes.
    Useful for initial population after migration.

    Args:
        owner_id: If provided, only process this user's notes

    Returns:
        dict with count of queued tasks
    """
    db = SessionLocal()

    try:
        logger.info("Starting note chunks backfill")

        # Query all notes
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
                generate_note_chunks_task.delay(note_id, generate_embeddings=True)
                queued += 1
            except Exception as e:
                logger.error(f"Failed to queue task for note {note_id}: {e}")
                failed += 1

        logger.info(f"Note chunks backfill: {queued} queued, {failed} failed")

        return {
            "status": "completed",
            "total_notes": len(note_ids),
            "queued": queued,
            "failed": failed,
            "owner_id": owner_id
        }

    except Exception as e:
        logger.error(f"Error in note chunks backfill: {str(e)}", exc_info=True)
        raise

    finally:
        db.close()


@celery_app.task(
    name="tasks_rag.backfill_image_chunks",
    bind=True
)
def backfill_image_chunks_task(self, owner_id: Optional[int] = None) -> dict:
    """
    Backfill chunks for all existing images with AI analysis.

    This batch task queues individual chunk generation tasks for all images
    that have completed AI analysis.

    Args:
        owner_id: If provided, only process this user's images

    Returns:
        dict with count of queued tasks
    """
    db = SessionLocal()

    try:
        logger.info("Starting image chunks backfill")

        # Query all images with completed AI analysis
        stmt = select(Image.id).where(
            Image.ai_analysis_status == "completed",
            Image.ai_analysis_result.isnot(None)
        )
        if owner_id:
            stmt = stmt.where(Image.owner_id == owner_id)
            logger.info(f"Filtering images for owner_id={owner_id}")

        result = db.execute(stmt)
        image_ids = [row[0] for row in result.fetchall()]

        logger.info(f"Found {len(image_ids)} images to process")

        # Queue individual tasks
        queued = 0
        failed = 0

        for image_id in image_ids:
            try:
                generate_image_chunks_task.delay(image_id, generate_embeddings=True)
                queued += 1
            except Exception as e:
                logger.error(f"Failed to queue task for image {image_id}: {e}")
                failed += 1

        logger.info(f"Image chunks backfill: {queued} queued, {failed} failed")

        return {
            "status": "completed",
            "total_images": len(image_ids),
            "queued": queued,
            "failed": failed,
            "owner_id": owner_id
        }

    except Exception as e:
        logger.error(f"Error in image chunks backfill: {str(e)}", exc_info=True)
        raise

    finally:
        db.close()


@celery_app.task(
    name="tasks_rag.backfill_all_chunks",
    bind=True
)
def backfill_all_chunks_task(self, owner_id: Optional[int] = None) -> dict:
    """
    Backfill chunks for all existing notes and images.

    Convenience task that triggers both note and image backfill tasks.

    Args:
        owner_id: If provided, only process this user's content

    Returns:
        dict with task IDs for both backfill operations
    """
    logger.info(f"Starting full chunks backfill (owner_id={owner_id})")

    # Queue both backfill tasks
    notes_task = backfill_note_chunks_task.delay(owner_id)
    images_task = backfill_image_chunks_task.delay(owner_id)

    return {
        "status": "queued",
        "notes_task_id": notes_task.id,
        "images_task_id": images_task.id,
        "owner_id": owner_id
    }
