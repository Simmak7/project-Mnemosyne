"""
Migration: Add source field to notes table.

Tracks how a note was created:
- 'manual' (default) - user-created notes
- 'image_analysis' - auto-generated from image AI analysis
- 'document_analysis' - auto-generated from PDF document approval

Run: docker-compose exec backend python -m migrations.add_note_source
"""

import logging
from sqlalchemy import text
from core.database import engine

logger = logging.getLogger(__name__)


def upgrade():
    """Add source column to notes table with smart defaults."""
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'notes' AND column_name = 'source'"
        ))
        if result.fetchone():
            logger.info("notes.source column already exists, skipping")
            return

        logger.info("Adding 'source' column to notes table...")
        conn.execute(text(
            "ALTER TABLE notes ADD COLUMN source VARCHAR NOT NULL DEFAULT 'manual'"
        ))

        logger.info("Creating index on notes.source...")
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_notes_source ON notes (source)"
        ))

        # Backfill: notes linked to images -> 'image_analysis'
        result = conn.execute(text("""
            UPDATE notes SET source = 'image_analysis'
            WHERE id IN (SELECT DISTINCT note_id FROM image_note_relations)
        """))
        logger.info(f"Backfilled {result.rowcount} notes to 'image_analysis'")

        # Backfill: document summary notes -> 'document_analysis'
        result = conn.execute(text("""
            UPDATE notes SET source = 'document_analysis'
            WHERE id IN (
                SELECT summary_note_id FROM documents
                WHERE summary_note_id IS NOT NULL
            )
        """))
        logger.info(f"Backfilled {result.rowcount} notes to 'document_analysis'")

        # Fix is_standalone for AI-generated notes
        result = conn.execute(text("""
            UPDATE notes SET is_standalone = FALSE
            WHERE source IN ('image_analysis', 'document_analysis')
            AND is_standalone = TRUE
        """))
        logger.info(f"Fixed is_standalone for {result.rowcount} AI-generated notes")

        conn.commit()
        logger.info("Note source migration completed successfully")


if __name__ == "__main__":
    upgrade()
