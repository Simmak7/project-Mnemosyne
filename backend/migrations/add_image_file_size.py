"""
Database migration to add file_size column to images table.

This script:
1. Adds file_size (INTEGER) column to images table
2. Backfills existing images by reading file size from disk

Run with:
    docker-compose exec backend python migrations/add_image_file_size.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, text, inspect
import logging

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
    logger.info(f"Using database: {database_url.split('@')[1] if '@' in database_url else 'default'}")
    return database_url


def check_column_exists(inspector, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    if table_name not in inspector.get_table_names():
        return False
    columns = inspector.get_columns(table_name)
    return any(col['name'] == column_name for col in columns)


def run_migration():
    """Execute the migration."""
    logger.info("=" * 80)
    logger.info("Starting file_size column migration")
    logger.info("=" * 80)

    database_url = get_database_url()

    try:
        engine = create_engine(database_url)
        logger.info("Database connection established")

        inspector = inspect(engine)

        with engine.connect() as conn:
            trans = conn.begin()

            try:
                # Step 1: Add file_size column
                logger.info("\n[1/2] Checking images.file_size column...")

                if check_column_exists(inspector, 'images', 'file_size'):
                    logger.info("  images.file_size column already exists, skipping")
                else:
                    logger.info("  + Adding file_size column to images table")
                    conn.execute(text(
                        "ALTER TABLE images ADD COLUMN file_size INTEGER"
                    ))
                    logger.info("  images.file_size column added successfully")

                # Step 2: Backfill from disk
                logger.info("\n[2/2] Backfilling file_size from disk...")

                rows = conn.execute(text(
                    "SELECT id, filepath FROM images WHERE file_size IS NULL"
                )).fetchall()

                updated = 0
                skipped = 0
                for row in rows:
                    image_id, filepath = row[0], row[1]
                    if filepath and os.path.exists(filepath):
                        size = os.path.getsize(filepath)
                        conn.execute(
                            text("UPDATE images SET file_size = :size WHERE id = :id"),
                            {"size": size, "id": image_id}
                        )
                        updated += 1
                    else:
                        skipped += 1

                logger.info(f"  Backfilled {updated} images, skipped {skipped} (file not found)")

                trans.commit()
                logger.info("\n" + "=" * 80)
                logger.info("Migration completed successfully!")
                logger.info("=" * 80)

            except Exception as e:
                trans.rollback()
                logger.error(f"\nMigration failed: {str(e)}", exc_info=True)
                logger.info("Transaction rolled back, no changes made")
                raise

    except Exception as e:
        logger.error(f"\nDatabase connection failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    logger.info("Image File Size Migration Script")
    logger.info("=" * 80)

    try:
        run_migration()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Migration script failed: {str(e)}")
        sys.exit(1)
