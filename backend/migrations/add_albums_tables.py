"""
Database migration script to add albums support (Phase 5).

This script:
1. Creates albums table
2. Creates album_images junction table
3. Creates indexes for faster queries

Run this script with:
    docker-compose exec backend python migrations/add_albums_tables.py

Or locally:
    python backend/migrations/add_albums_tables.py
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


def check_table_exists(inspector, table_name: str) -> bool:
    """Check if a table exists."""
    return table_name in inspector.get_table_names()


def check_index_exists(conn, index_name: str) -> bool:
    """Check if an index exists."""
    result = conn.execute(text(
        "SELECT 1 FROM pg_indexes WHERE indexname = :index_name"
    ), {"index_name": index_name})
    return result.fetchone() is not None


def run_migration():
    """Execute the migration."""
    logger.info("=" * 80)
    logger.info("Starting albums tables migration (Phase 5)")
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
                # Step 1: Create albums table
                # ============================================
                logger.info("\n[1/4] Checking albums table...")

                if check_table_exists(inspector, 'albums'):
                    logger.info("  ✓ albums table already exists, skipping")
                else:
                    logger.info("  + Creating albums table")
                    conn.execute(text("""
                        CREATE TABLE albums (
                            id SERIAL PRIMARY KEY,
                            owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            name VARCHAR(255) NOT NULL,
                            description TEXT,
                            cover_image_id INTEGER REFERENCES images(id) ON DELETE SET NULL,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        )
                    """))
                    logger.info("  ✓ albums table created successfully")

                # ============================================
                # Step 2: Create album_images junction table
                # ============================================
                logger.info("\n[2/4] Checking album_images table...")

                if check_table_exists(inspector, 'album_images'):
                    logger.info("  ✓ album_images table already exists, skipping")
                else:
                    logger.info("  + Creating album_images junction table")
                    conn.execute(text("""
                        CREATE TABLE album_images (
                            album_id INTEGER NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
                            image_id INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
                            added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            position INTEGER DEFAULT 0,
                            PRIMARY KEY (album_id, image_id)
                        )
                    """))
                    logger.info("  ✓ album_images table created successfully")

                # ============================================
                # Step 3: Create index on albums.owner_id
                # ============================================
                logger.info("\n[3/4] Checking idx_albums_owner index...")

                if check_index_exists(conn, 'idx_albums_owner'):
                    logger.info("  ✓ idx_albums_owner index already exists, skipping")
                else:
                    logger.info("  + Creating index on albums.owner_id")
                    conn.execute(text(
                        "CREATE INDEX idx_albums_owner ON albums (owner_id)"
                    ))
                    logger.info("  ✓ idx_albums_owner index created successfully")

                # ============================================
                # Step 4: Create index on album_images.image_id
                # ============================================
                logger.info("\n[4/4] Checking idx_album_images_image index...")

                if check_index_exists(conn, 'idx_album_images_image'):
                    logger.info("  ✓ idx_album_images_image index already exists, skipping")
                else:
                    logger.info("  + Creating index on album_images.image_id")
                    conn.execute(text(
                        "CREATE INDEX idx_album_images_image ON album_images (image_id)"
                    ))
                    logger.info("  ✓ idx_album_images_image index created successfully")

                # Commit transaction
                trans.commit()
                logger.info("\n" + "=" * 80)
                logger.info("Migration completed successfully!")
                logger.info("=" * 80)

                # Summary
                logger.info("\nMigration Summary:")
                logger.info("  ✓ albums table created (id, owner_id, name, description, cover_image_id, timestamps)")
                logger.info("  ✓ album_images junction table created (album_id, image_id, added_at, position)")
                logger.info("  ✓ idx_albums_owner index created for fast owner filtering")
                logger.info("  ✓ idx_album_images_image index created for fast image lookups")
                logger.info("\nAlbums feature is now ready to use.")

            except Exception as e:
                trans.rollback()
                logger.error(f"\n❌ Migration failed: {str(e)}", exc_info=True)
                logger.info("Transaction rolled back, no changes made")
                raise

    except Exception as e:
        logger.error(f"\n❌ Database connection failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    logger.info("Albums Tables Migration Script (Phase 5)")
    logger.info("=" * 80)

    try:
        run_migration()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Migration script failed: {str(e)}")
        sys.exit(1)
