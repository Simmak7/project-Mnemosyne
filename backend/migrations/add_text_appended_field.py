"""
Migration: Add text_appended_to_note column to documents table.

Run: docker-compose exec backend python -m migrations.add_text_appended_field
"""

import logging
from sqlalchemy import text
from core.database import engine

logger = logging.getLogger(__name__)


def upgrade():
    """Add text_appended_to_note boolean column."""
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.columns "
            "  WHERE table_name = 'documents' AND column_name = 'text_appended_to_note'"
            ")"
        ))
        if result.scalar():
            logger.info("text_appended_to_note column already exists, skipping")
            return

        logger.info("Adding text_appended_to_note column...")
        conn.execute(text(
            "ALTER TABLE documents "
            "ADD COLUMN text_appended_to_note BOOLEAN DEFAULT FALSE NOT NULL"
        ))

        conn.commit()
        logger.info("Migration completed: text_appended_to_note added")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upgrade()
