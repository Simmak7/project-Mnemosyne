"""
Database migration script to add full-text search support.

This script:
1. Creates pg_trgm extension for fuzzy text matching
2. Adds search_vector column to notes table (tsvector type)
3. Adds search_vector column to images table (tsvector type)
4. Creates GIN indexes for fast full-text search
5. Creates triggers to auto-update search_vector on INSERT/UPDATE
6. Populates search_vector for existing data

Run this script with:
    docker-compose exec backend python migrations/add_search_support.py

Or locally:
    python backend/migrations/add_search_support.py
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
    logger.info(f"Using database URL: {database_url.split('@')[1] if '@' in database_url else 'default'}")
    return database_url


def check_table_exists(inspector, table_name: str) -> bool:
    """Check if a table exists in the database."""
    return table_name in inspector.get_table_names()


def check_column_exists(inspector, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    if not check_table_exists(inspector, table_name):
        return False

    columns = inspector.get_columns(table_name)
    return any(col['name'] == column_name for col in columns)


def check_extension_exists(conn, extension_name: str) -> bool:
    """Check if a PostgreSQL extension is installed."""
    result = conn.execute(text(
        "SELECT COUNT(*) FROM pg_extension WHERE extname = :ext_name"
    ), {"ext_name": extension_name})
    return result.scalar() > 0


def check_index_exists(conn, index_name: str) -> bool:
    """Check if an index exists."""
    result = conn.execute(text(
        "SELECT COUNT(*) FROM pg_indexes WHERE indexname = :idx_name"
    ), {"idx_name": index_name})
    return result.scalar() > 0


def check_trigger_exists(conn, trigger_name: str, table_name: str) -> bool:
    """Check if a trigger exists on a table."""
    result = conn.execute(text(
        """
        SELECT COUNT(*) FROM pg_trigger t
        JOIN pg_class c ON t.tgrelid = c.oid
        WHERE t.tgname = :trigger_name AND c.relname = :table_name
        """
    ), {"trigger_name": trigger_name, "table_name": table_name})
    return result.scalar() > 0


def run_migration():
    """Execute the migration."""
    logger.info("=" * 80)
    logger.info("Starting full-text search migration")
    logger.info("=" * 80)

    database_url = get_database_url()

    try:
        engine = create_engine(database_url)
        logger.info("Database connection established")

        inspector = inspect(engine)

        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()

            try:
                # ============================================
                # Step 1: Create pg_trgm extension
                # ============================================
                logger.info("\n[1/8] Checking pg_trgm extension...")

                if check_extension_exists(conn, 'pg_trgm'):
                    logger.info("  ✓ pg_trgm extension already exists, skipping")
                else:
                    logger.info("  + Creating pg_trgm extension")
                    conn.execute(text("CREATE EXTENSION pg_trgm"))
                    logger.info("  ✓ pg_trgm extension created successfully")

                # ============================================
                # Step 2: Add search_vector column to notes
                # ============================================
                logger.info("\n[2/8] Checking notes.search_vector column...")

                if check_column_exists(inspector, 'notes', 'search_vector'):
                    logger.info("  ✓ notes.search_vector column already exists, skipping")
                else:
                    logger.info("  + Adding search_vector column to notes table")
                    conn.execute(text(
                        "ALTER TABLE notes ADD COLUMN search_vector tsvector"
                    ))
                    logger.info("  ✓ notes.search_vector column added successfully")

                # ============================================
                # Step 3: Add search_vector column to images
                # ============================================
                logger.info("\n[3/8] Checking images.search_vector column...")

                if check_column_exists(inspector, 'images', 'search_vector'):
                    logger.info("  ✓ images.search_vector column already exists, skipping")
                else:
                    logger.info("  + Adding search_vector column to images table")
                    conn.execute(text(
                        "ALTER TABLE images ADD COLUMN search_vector tsvector"
                    ))
                    logger.info("  ✓ images.search_vector column added successfully")

                # ============================================
                # Step 4: Create GIN index on notes.search_vector
                # ============================================
                logger.info("\n[4/8] Checking notes search index...")

                if check_index_exists(conn, 'idx_notes_search'):
                    logger.info("  ✓ idx_notes_search index already exists, skipping")
                else:
                    logger.info("  + Creating GIN index on notes.search_vector")
                    conn.execute(text(
                        "CREATE INDEX idx_notes_search ON notes USING GIN(search_vector)"
                    ))
                    logger.info("  ✓ idx_notes_search index created successfully")

                # ============================================
                # Step 5: Create GIN index on images.search_vector
                # ============================================
                logger.info("\n[5/8] Checking images search index...")

                if check_index_exists(conn, 'idx_images_search'):
                    logger.info("  ✓ idx_images_search index already exists, skipping")
                else:
                    logger.info("  + Creating GIN index on images.search_vector")
                    conn.execute(text(
                        "CREATE INDEX idx_images_search ON images USING GIN(search_vector)"
                    ))
                    logger.info("  ✓ idx_images_search index created successfully")

                # ============================================
                # Step 6: Create GIN index on tags.name for fuzzy search
                # ============================================
                logger.info("\n[6/8] Checking tags fuzzy search index...")

                if check_index_exists(conn, 'idx_tags_name_trgm'):
                    logger.info("  ✓ idx_tags_name_trgm index already exists, skipping")
                else:
                    logger.info("  + Creating GIN index on tags.name for fuzzy search")
                    conn.execute(text(
                        "CREATE INDEX idx_tags_name_trgm ON tags USING GIN(name gin_trgm_ops)"
                    ))
                    logger.info("  ✓ idx_tags_name_trgm index created successfully")

                # ============================================
                # Step 7: Create triggers to auto-update search_vector
                # ============================================
                logger.info("\n[7/8] Checking auto-update triggers...")

                # Trigger for notes table
                if check_trigger_exists(conn, 'notes_search_vector_update', 'notes'):
                    logger.info("  ✓ notes_search_vector_update trigger already exists, skipping")
                else:
                    logger.info("  + Creating trigger for notes.search_vector auto-update")
                    conn.execute(text("""
                        CREATE TRIGGER notes_search_vector_update
                        BEFORE INSERT OR UPDATE ON notes
                        FOR EACH ROW EXECUTE FUNCTION
                        tsvector_update_trigger(
                            search_vector, 'pg_catalog.english', title, content
                        )
                    """))
                    logger.info("  ✓ notes_search_vector_update trigger created successfully")

                # Trigger for images table
                if check_trigger_exists(conn, 'images_search_vector_update', 'images'):
                    logger.info("  ✓ images_search_vector_update trigger already exists, skipping")
                else:
                    logger.info("  + Creating trigger for images.search_vector auto-update")
                    conn.execute(text("""
                        CREATE TRIGGER images_search_vector_update
                        BEFORE INSERT OR UPDATE ON images
                        FOR EACH ROW EXECUTE FUNCTION
                        tsvector_update_trigger(
                            search_vector, 'pg_catalog.english', filename, prompt, ai_analysis_result
                        )
                    """))
                    logger.info("  ✓ images_search_vector_update trigger created successfully")

                # ============================================
                # Step 8: Populate search_vector for existing data
                # ============================================
                logger.info("\n[8/8] Populating search_vector for existing data...")

                # Count existing notes
                result = conn.execute(text(
                    "SELECT COUNT(*) FROM notes WHERE search_vector IS NULL"
                ))
                null_notes_count = result.scalar()

                if null_notes_count > 0:
                    logger.info(f"  + Found {null_notes_count} notes without search_vector")
                    logger.info("  + Updating notes.search_vector...")

                    conn.execute(text("""
                        UPDATE notes
                        SET search_vector = to_tsvector('pg_catalog.english',
                            COALESCE(title, '') || ' ' || COALESCE(content, '')
                        )
                        WHERE search_vector IS NULL
                    """))
                    logger.info(f"  ✓ Updated search_vector for {null_notes_count} notes")
                else:
                    logger.info("  ✓ All notes already have search_vector populated")

                # Count existing images
                result = conn.execute(text(
                    "SELECT COUNT(*) FROM images WHERE search_vector IS NULL"
                ))
                null_images_count = result.scalar()

                if null_images_count > 0:
                    logger.info(f"  + Found {null_images_count} images without search_vector")
                    logger.info("  + Updating images.search_vector...")

                    conn.execute(text("""
                        UPDATE images
                        SET search_vector = to_tsvector('pg_catalog.english',
                            COALESCE(filename, '') || ' ' ||
                            COALESCE(prompt, '') || ' ' ||
                            COALESCE(ai_analysis_result, '')
                        )
                        WHERE search_vector IS NULL
                    """))
                    logger.info(f"  ✓ Updated search_vector for {null_images_count} images")
                else:
                    logger.info("  ✓ All images already have search_vector populated")

                # Commit transaction
                trans.commit()
                logger.info("\n" + "=" * 80)
                logger.info("Migration completed successfully!")
                logger.info("=" * 80)

                # Summary
                logger.info("\nMigration Summary:")
                logger.info("  ✓ pg_trgm extension enabled")
                logger.info("  ✓ notes.search_vector column ready")
                logger.info("  ✓ images.search_vector column ready")
                logger.info("  ✓ GIN indexes created for fast search")
                logger.info("  ✓ Auto-update triggers configured")
                logger.info(f"  ✓ Populated search data for {null_notes_count} notes")
                logger.info(f"  ✓ Populated search data for {null_images_count} images")
                logger.info("\nYou can now:")
                logger.info("  1. Restart the backend service")
                logger.info("  2. Use full-text search endpoints (/search/fulltext)")
                logger.info("  3. Search across notes, images, and tags")
                logger.info("  4. Expect search response times < 100ms")

            except Exception as e:
                trans.rollback()
                logger.error(f"\n❌ Migration failed: {str(e)}", exc_info=True)
                logger.info("Transaction rolled back, no changes made")
                raise

    except Exception as e:
        logger.error(f"\n❌ Database connection failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    logger.info("Full-Text Search Migration Script")
    logger.info("=" * 80)

    try:
        run_migration()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Migration script failed: {str(e)}")
        sys.exit(1)
