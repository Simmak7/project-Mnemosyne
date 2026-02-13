"""
Migration: Add compressed_content columns to brain_files table.

Adds:
- compressed_content TEXT NULL: ~100-150 token compressed summary for knowledge map
- compressed_token_count INTEGER DEFAULT 0: token count of compressed version

Run: docker-compose exec backend python -m migrations.add_brain_compressed_content
"""

import logging
from sqlalchemy import text
from core.database import engine

logger = logging.getLogger(__name__)


def upgrade():
    """Add compressed_content and compressed_token_count to brain_files."""
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'brain_files' AND column_name = 'compressed_content'"
        ))
        if result.fetchone():
            logger.info("brain_files.compressed_content already exists, skipping")
            return

        logger.info("Adding compressed_content column to brain_files...")
        conn.execute(text(
            "ALTER TABLE brain_files ADD COLUMN compressed_content TEXT NULL"
        ))

        logger.info("Adding compressed_token_count column to brain_files...")
        conn.execute(text(
            "ALTER TABLE brain_files ADD COLUMN compressed_token_count INTEGER DEFAULT 0"
        ))

        conn.commit()
        logger.info("Brain compressed content migration completed successfully")


if __name__ == "__main__":
    upgrade()
