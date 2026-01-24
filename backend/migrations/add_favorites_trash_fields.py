"""
Database migration script to add favorites and trash support (Phase 4).

This script:
1. Adds is_favorite column to images table
2. Adds is_trashed column to images table
3. Adds trashed_at column to images table
4. Creates index on is_trashed for faster filtering

Run this script with:
    docker-compose exec backend python migrations/add_favorites_trash_fields.py

Or locally:
    python backend/migrations/add_favorites_trash_fields.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, text, inspect
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
    logger.info(f"Using database: {database_url.split('@')[1] if '@' in database_url else 'default'}")
    return database_url


def check_column_exists(inspector, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    if table_name not in inspector.get_table_names():
        return False
    columns = inspector.get_columns(table_name)
    return any(col['name'] == column_name for col in columns)


def check_index_exists(conn, index_name: str) -> bool:
    """Check if an index exists."""
    result = conn.execute(text(
        "SELECT 1 FROM pg_indexes WHERE indexname = :index_name"
    ), {"index_name": index_name})
    return result.fetchone() is not None


def run_migration():
    """Execute the migration."""
    logger.info("=" * 80)
    logger.info("Starting favorites/trash fields migration (Phase 4)")
    logger.info("=" * 80)

    database_url = get_database_url()

    try:
        engine = create_engine(database_url)
        logger.info("Database connection established")

        inspector = inspect(engine)

        with engine.connect() as conn:
            trans = conn.begin()

            try:
                # ============================================
                # Step 1: Add is_favorite column
                # ============================================
                logger.info("\n[1/4] Checking images.is_favorite column...")

                if check_column_exists(inspector, 'images', 'is_favorite'):
                    logger.info("  ✓ images.is_favorite column already exists, skipping")
                else:
                    logger.info("  + Adding is_favorite column to images table")
                    conn.execute(text(
                        "ALTER TABLE images ADD COLUMN is_favorite BOOLEAN NOT NULL DEFAULT FALSE"
                    ))
                    logger.info("  ✓ images.is_favorite column added successfully")

                # ============================================
                # Step 2: Add is_trashed column
                # ============================================
                logger.info("\n[2/4] Checking images.is_trashed column...")

                if check_column_exists(inspector, 'images', 'is_trashed'):
                    logger.info("  ✓ images.is_trashed column already exists, skipping")
                else:
                    logger.info("  + Adding is_trashed column to images table")
                    conn.execute(text(
                        "ALTER TABLE images ADD COLUMN is_trashed BOOLEAN NOT NULL DEFAULT FALSE"
                    ))
                    logger.info("  ✓ images.is_trashed column added successfully")

                # ============================================
                # Step 3: Add trashed_at column
                # ============================================
                logger.info("\n[3/4] Checking images.trashed_at column...")

                if check_column_exists(inspector, 'images', 'trashed_at'):
                    logger.info("  ✓ images.trashed_at column already exists, skipping")
                else:
                    logger.info("  + Adding trashed_at column to images table")
                    conn.execute(text(
                        "ALTER TABLE images ADD COLUMN trashed_at TIMESTAMP WITH TIME ZONE"
                    ))
                    logger.info("  ✓ images.trashed_at column added successfully")

                # ============================================
                # Step 4: Create index on is_trashed for filtering
                # ============================================
                logger.info("\n[4/4] Checking idx_images_trashed index...")

                if check_index_exists(conn, 'idx_images_trashed'):
                    logger.info("  ✓ idx_images_trashed index already exists, skipping")
                else:
                    logger.info("  + Creating index on is_trashed column")
                    conn.execute(text(
                        "CREATE INDEX idx_images_trashed ON images (is_trashed)"
                    ))
                    logger.info("  ✓ idx_images_trashed index created successfully")

                # Commit transaction
                trans.commit()
                logger.info("\n" + "=" * 80)
                logger.info("Migration completed successfully!")
                logger.info("=" * 80)

                # Summary
                logger.info("\nMigration Summary:")
                logger.info("  ✓ images.is_favorite column ready (BOOLEAN, default FALSE)")
                logger.info("  ✓ images.is_trashed column ready (BOOLEAN, default FALSE)")
                logger.info("  ✓ images.trashed_at column ready (TIMESTAMP WITH TIME ZONE)")
                logger.info("  ✓ idx_images_trashed index created for fast filtering")
                logger.info("\nImages can now be favorited and moved to trash.")

            except Exception as e:
                trans.rollback()
                logger.error(f"\n❌ Migration failed: {str(e)}", exc_info=True)
                logger.info("Transaction rolled back, no changes made")
                raise

    except Exception as e:
        logger.error(f"\n❌ Database connection failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    logger.info("Favorites/Trash Fields Migration Script (Phase 4)")
    logger.info("=" * 80)

    try:
        run_migration()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Migration script failed: {str(e)}")
        sys.exit(1)
