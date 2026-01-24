"""
Database migration script to add tags and wikilinks support.

This script:
1. Adds slug column to notes table
2. Creates tags table
3. Creates note_tags junction table
4. Creates image_tags junction table
5. Adds appropriate indexes

Run this script with:
    docker-compose exec backend python migrations/add_tags_and_wikilinks.py

Or locally:
    python backend/migrations/add_tags_and_wikilinks.py
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


def run_migration():
    """Execute the migration."""
    logger.info("=" * 80)
    logger.info("Starting tags and wikilinks migration")
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
                # Step 1: Add slug column to notes table
                # ============================================
                logger.info("\n[1/5] Checking notes.slug column...")

                if check_column_exists(inspector, 'notes', 'slug'):
                    logger.info("  ✓ notes.slug column already exists, skipping")
                else:
                    logger.info("  + Adding slug column to notes table")
                    conn.execute(text(
                        "ALTER TABLE notes ADD COLUMN slug VARCHAR"
                    ))
                    logger.info("  + Creating index on notes.slug")
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS ix_notes_slug ON notes(slug)"
                    ))
                    logger.info("  ✓ notes.slug column added successfully")

                # ============================================
                # Step 2: Create tags table
                # ============================================
                logger.info("\n[2/5] Checking tags table...")

                if check_table_exists(inspector, 'tags'):
                    logger.info("  ✓ tags table already exists, skipping")
                else:
                    logger.info("  + Creating tags table")
                    conn.execute(text("""
                        CREATE TABLE tags (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR NOT NULL,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            owner_id INTEGER REFERENCES users(id)
                        )
                    """))
                    logger.info("  + Creating index on tags.name")
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS ix_tags_name ON tags(name)"
                    ))
                    logger.info("  + Creating index on tags.id")
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS ix_tags_id ON tags(id)"
                    ))
                    logger.info("  ✓ tags table created successfully")

                # ============================================
                # Step 3: Create note_tags junction table
                # ============================================
                logger.info("\n[3/5] Checking note_tags junction table...")

                if check_table_exists(inspector, 'note_tags'):
                    logger.info("  ✓ note_tags table already exists, skipping")
                else:
                    logger.info("  + Creating note_tags junction table")
                    conn.execute(text("""
                        CREATE TABLE note_tags (
                            note_id INTEGER REFERENCES notes(id) ON DELETE CASCADE,
                            tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                            PRIMARY KEY (note_id, tag_id)
                        )
                    """))
                    logger.info("  ✓ note_tags table created successfully")

                # ============================================
                # Step 4: Create image_tags junction table
                # ============================================
                logger.info("\n[4/5] Checking image_tags junction table...")

                if check_table_exists(inspector, 'image_tags'):
                    logger.info("  ✓ image_tags table already exists, skipping")
                else:
                    logger.info("  + Creating image_tags junction table")
                    conn.execute(text("""
                        CREATE TABLE image_tags (
                            image_id INTEGER REFERENCES images(id) ON DELETE CASCADE,
                            tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                            PRIMARY KEY (image_id, tag_id)
                        )
                    """))
                    logger.info("  ✓ image_tags table created successfully")

                # ============================================
                # Step 5: Populate slug for existing notes
                # ============================================
                logger.info("\n[5/5] Populating slugs for existing notes...")

                # Check if there are notes without slugs
                result = conn.execute(text(
                    "SELECT COUNT(*) FROM notes WHERE slug IS NULL"
                ))
                null_slug_count = result.scalar()

                if null_slug_count > 0:
                    logger.info(f"  + Found {null_slug_count} notes without slugs")
                    logger.info("  + Generating slugs from titles...")

                    # Use Python to generate slugs (import wikilink_parser)
                    try:
                        from app.wikilink_parser import create_slug

                        # Get all notes without slugs
                        notes_result = conn.execute(text(
                            "SELECT id, title FROM notes WHERE slug IS NULL"
                        ))

                        updated_count = 0
                        for note_id, title in notes_result:
                            if title:
                                slug = create_slug(title)
                                conn.execute(
                                    text("UPDATE notes SET slug = :slug WHERE id = :id"),
                                    {"slug": slug, "id": note_id}
                                )
                                updated_count += 1

                        logger.info(f"  ✓ Generated slugs for {updated_count} notes")
                    except ImportError:
                        logger.warning("  ! Could not import wikilink_parser, skipping slug generation")
                        logger.warning("  ! Slugs will be generated when notes are next updated")
                else:
                    logger.info("  ✓ All notes already have slugs")

                # Commit transaction
                trans.commit()
                logger.info("\n" + "=" * 80)
                logger.info("Migration completed successfully!")
                logger.info("=" * 80)

                # Summary
                logger.info("\nMigration Summary:")
                logger.info("  ✓ notes.slug column ready")
                logger.info("  ✓ tags table ready")
                logger.info("  ✓ note_tags junction table ready")
                logger.info("  ✓ image_tags junction table ready")
                logger.info("\nYou can now:")
                logger.info("  1. Restart the backend service")
                logger.info("  2. Use tag management endpoints (/tags/)")
                logger.info("  3. Use wikilinks in note content [[like this]]")
                logger.info("  4. Access knowledge graph endpoints (/notes-enhanced/)")

            except Exception as e:
                trans.rollback()
                logger.error(f"\n❌ Migration failed: {str(e)}", exc_info=True)
                logger.info("Transaction rolled back, no changes made")
                raise

    except Exception as e:
        logger.error(f"\n❌ Database connection failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    logger.info("Tags and Wikilinks Migration Script")
    logger.info("=" * 80)

    try:
        run_migration()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Migration script failed: {str(e)}")
        sys.exit(1)
