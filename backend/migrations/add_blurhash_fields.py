"""
Database migration script to add blur hash support for instant image loading.

This script:
1. Adds blur_hash column to images table
2. Adds width column to images table
3. Adds height column to images table

Run this script with:
    docker-compose exec backend python migrations/add_blurhash_fields.py

Or locally:
    python backend/migrations/add_blurhash_fields.py
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


def run_migration():
    """Execute the migration."""
    logger.info("=" * 80)
    logger.info("Starting blur hash fields migration (Phase 3)")
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
                # Step 1: Add blur_hash column
                # ============================================
                logger.info("\n[1/3] Checking images.blur_hash column...")

                if check_column_exists(inspector, 'images', 'blur_hash'):
                    logger.info("  ✓ images.blur_hash column already exists, skipping")
                else:
                    logger.info("  + Adding blur_hash column to images table")
                    conn.execute(text(
                        "ALTER TABLE images ADD COLUMN blur_hash VARCHAR(32)"
                    ))
                    logger.info("  ✓ images.blur_hash column added successfully")

                # ============================================
                # Step 2: Add width column
                # ============================================
                logger.info("\n[2/3] Checking images.width column...")

                if check_column_exists(inspector, 'images', 'width'):
                    logger.info("  ✓ images.width column already exists, skipping")
                else:
                    logger.info("  + Adding width column to images table")
                    conn.execute(text(
                        "ALTER TABLE images ADD COLUMN width INTEGER"
                    ))
                    logger.info("  ✓ images.width column added successfully")

                # ============================================
                # Step 3: Add height column
                # ============================================
                logger.info("\n[3/3] Checking images.height column...")

                if check_column_exists(inspector, 'images', 'height'):
                    logger.info("  ✓ images.height column already exists, skipping")
                else:
                    logger.info("  + Adding height column to images table")
                    conn.execute(text(
                        "ALTER TABLE images ADD COLUMN height INTEGER"
                    ))
                    logger.info("  ✓ images.height column added successfully")

                # Commit transaction
                trans.commit()
                logger.info("\n" + "=" * 80)
                logger.info("Migration completed successfully!")
                logger.info("=" * 80)

                # Summary
                logger.info("\nMigration Summary:")
                logger.info("  ✓ images.blur_hash column ready (VARCHAR(32))")
                logger.info("  ✓ images.width column ready (INTEGER)")
                logger.info("  ✓ images.height column ready (INTEGER)")
                logger.info("\nBlur hash placeholders will now be generated for new uploads.")
                logger.info("Existing images will show shimmer placeholder until regenerated.")

            except Exception as e:
                trans.rollback()
                logger.error(f"\n❌ Migration failed: {str(e)}", exc_info=True)
                logger.info("Transaction rolled back, no changes made")
                raise

    except Exception as e:
        logger.error(f"\n❌ Database connection failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    logger.info("Blur Hash Fields Migration Script (Phase 3)")
    logger.info("=" * 80)

    try:
        run_migration()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Migration script failed: {str(e)}")
        sys.exit(1)
