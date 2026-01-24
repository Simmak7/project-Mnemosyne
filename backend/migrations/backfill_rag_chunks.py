"""
Backfill script for RAG chunks.

This script generates chunks and embeddings for all existing notes and images.
Run this after the add_rag_tables.py migration to populate chunk data.

Run this script with:
    docker-compose exec backend python migrations/backfill_rag_chunks.py

Or locally:
    python backend/migrations/backfill_rag_chunks.py

Options:
    --notes-only    Only backfill note chunks
    --images-only   Only backfill image chunks
    --no-embeddings Skip embedding generation (faster, but no semantic search)
    --user-id <id>  Only process content for specific user
    --dry-run       Show what would be done without making changes
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, text, select, delete
from sqlalchemy.orm import sessionmaker
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL from environment or use default."""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/ai_notes_db"
    )
    return database_url


def backfill_note_chunks(session, generate_embeddings: bool = True, user_id: int = None, dry_run: bool = False):
    """
    Backfill chunks for all notes.

    Args:
        session: Database session
        generate_embeddings: Whether to generate embeddings
        user_id: Optional user ID to filter
        dry_run: If True, don't make changes
    """
    from models import Note, NoteChunk
    from rag.chunking import chunk_note_content
    from embeddings import generate_embedding

    logger.info("=" * 60)
    logger.info("Backfilling note chunks")
    logger.info("=" * 60)

    # Query all notes
    stmt = select(Note)
    if user_id:
        stmt = stmt.where(Note.owner_id == user_id)

    result = session.execute(stmt)
    notes = result.scalars().all()

    logger.info(f"Found {len(notes)} notes to process")

    if dry_run:
        logger.info("[DRY RUN] Would process the following notes:")
        for note in notes[:10]:  # Show first 10
            logger.info(f"  - Note {note.id}: {note.title[:50] if note.title else 'Untitled'}...")
        if len(notes) > 10:
            logger.info(f"  ... and {len(notes) - 10} more")
        return {"notes_processed": 0, "chunks_created": 0, "dry_run": True}

    total_chunks = 0
    notes_processed = 0
    errors = 0

    for note in notes:
        try:
            if not note.content or not note.content.strip():
                logger.debug(f"Skipping note {note.id} - no content")
                continue

            # Delete existing chunks
            delete_stmt = delete(NoteChunk).where(NoteChunk.note_id == note.id)
            session.execute(delete_stmt)

            # Generate chunks
            chunks = chunk_note_content(note.content, note.id)

            if not chunks:
                logger.debug(f"No chunks for note {note.id}")
                continue

            # Store chunks
            for chunk in chunks:
                db_chunk = NoteChunk(
                    note_id=note.id,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    chunk_type=chunk.chunk_type,
                    char_start=chunk.char_start,
                    char_end=chunk.char_end,
                    embedding=None
                )

                if generate_embeddings:
                    try:
                        embedding = generate_embedding(chunk.content)
                        if embedding:
                            db_chunk.embedding = embedding
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding: {e}")

                session.add(db_chunk)
                total_chunks += 1

            notes_processed += 1

            # Commit in batches
            if notes_processed % 10 == 0:
                session.commit()
                logger.info(f"Processed {notes_processed}/{len(notes)} notes ({total_chunks} chunks)")

        except Exception as e:
            logger.error(f"Error processing note {note.id}: {e}")
            errors += 1
            session.rollback()

    session.commit()

    logger.info(f"\nNote chunks backfill complete:")
    logger.info(f"  Notes processed: {notes_processed}")
    logger.info(f"  Chunks created: {total_chunks}")
    logger.info(f"  Errors: {errors}")

    return {
        "notes_processed": notes_processed,
        "chunks_created": total_chunks,
        "errors": errors
    }


def backfill_image_chunks(session, generate_embeddings: bool = True, user_id: int = None, dry_run: bool = False):
    """
    Backfill chunks for all images with AI analysis.

    Args:
        session: Database session
        generate_embeddings: Whether to generate embeddings
        user_id: Optional user ID to filter
        dry_run: If True, don't make changes
    """
    from models import Image, ImageChunk
    from rag.chunking import chunk_image_analysis
    from embeddings import generate_embedding

    logger.info("=" * 60)
    logger.info("Backfilling image chunks")
    logger.info("=" * 60)

    # Query all images with completed analysis
    stmt = select(Image).where(
        Image.ai_analysis_status == "completed",
        Image.ai_analysis_result.isnot(None)
    )
    if user_id:
        stmt = stmt.where(Image.owner_id == user_id)

    result = session.execute(stmt)
    images = result.scalars().all()

    logger.info(f"Found {len(images)} images to process")

    if dry_run:
        logger.info("[DRY RUN] Would process the following images:")
        for image in images[:10]:
            logger.info(f"  - Image {image.id}: {image.filename}")
        if len(images) > 10:
            logger.info(f"  ... and {len(images) - 10} more")
        return {"images_processed": 0, "chunks_created": 0, "dry_run": True}

    total_chunks = 0
    images_processed = 0
    errors = 0

    for image in images:
        try:
            if not image.ai_analysis_result or not image.ai_analysis_result.strip():
                logger.debug(f"Skipping image {image.id} - no analysis")
                continue

            # Delete existing chunks
            delete_stmt = delete(ImageChunk).where(ImageChunk.image_id == image.id)
            session.execute(delete_stmt)

            # Generate chunks
            chunks = chunk_image_analysis(image.ai_analysis_result, image.id)

            if not chunks:
                logger.debug(f"No chunks for image {image.id}")
                continue

            # Store chunks
            for chunk in chunks:
                db_chunk = ImageChunk(
                    image_id=image.id,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    embedding=None
                )

                if generate_embeddings:
                    try:
                        embedding = generate_embedding(chunk.content)
                        if embedding:
                            db_chunk.embedding = embedding
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding: {e}")

                session.add(db_chunk)
                total_chunks += 1

            images_processed += 1

            # Commit in batches
            if images_processed % 10 == 0:
                session.commit()
                logger.info(f"Processed {images_processed}/{len(images)} images ({total_chunks} chunks)")

        except Exception as e:
            logger.error(f"Error processing image {image.id}: {e}")
            errors += 1
            session.rollback()

    session.commit()

    logger.info(f"\nImage chunks backfill complete:")
    logger.info(f"  Images processed: {images_processed}")
    logger.info(f"  Chunks created: {total_chunks}")
    logger.info(f"  Errors: {errors}")

    return {
        "images_processed": images_processed,
        "chunks_created": total_chunks,
        "errors": errors
    }


def main():
    parser = argparse.ArgumentParser(description="Backfill RAG chunks for existing content")
    parser.add_argument("--notes-only", action="store_true", help="Only backfill note chunks")
    parser.add_argument("--images-only", action="store_true", help="Only backfill image chunks")
    parser.add_argument("--no-embeddings", action="store_true", help="Skip embedding generation")
    parser.add_argument("--user-id", type=int, help="Only process content for specific user")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")

    args = parser.parse_args()

    logger.info("RAG Chunks Backfill Script")
    logger.info("=" * 60)

    database_url = get_database_url()
    logger.info(f"Connecting to database...")

    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        generate_embeddings = not args.no_embeddings

        results = {
            "notes": None,
            "images": None
        }

        # Backfill notes
        if not args.images_only:
            results["notes"] = backfill_note_chunks(
                session,
                generate_embeddings=generate_embeddings,
                user_id=args.user_id,
                dry_run=args.dry_run
            )

        # Backfill images
        if not args.notes_only:
            results["images"] = backfill_image_chunks(
                session,
                generate_embeddings=generate_embeddings,
                user_id=args.user_id,
                dry_run=args.dry_run
            )

        logger.info("\n" + "=" * 60)
        logger.info("BACKFILL COMPLETE")
        logger.info("=" * 60)

        if results["notes"]:
            logger.info(f"Notes: {results['notes']['chunks_created']} chunks created")
        if results["images"]:
            logger.info(f"Images: {results['images']['chunks_created']} chunks created")

        if args.dry_run:
            logger.info("\n[DRY RUN] No changes were made")

        session.close()
        sys.exit(0)

    except Exception as e:
        logger.error(f"Backfill failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
