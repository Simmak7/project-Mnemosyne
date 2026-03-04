"""
Migration: Add note_collection_documents table for unified collections.

Extends note_collections to also support documents, migrating existing
document_collections data into the unified system.

Run: docker-compose exec backend python -m migrations.add_unified_collections
"""

import logging
from sqlalchemy import text
from core.database import engine

logger = logging.getLogger(__name__)


def upgrade():
    """Create note_collection_documents table and migrate data."""
    with engine.connect() as conn:
        # Check if table already exists
        result = conn.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'note_collection_documents')"
        ))
        if result.scalar():
            logger.info("note_collection_documents table already exists, skipping")
            return

        logger.info("Creating note_collection_documents junction table...")
        conn.execute(text("""
            CREATE TABLE note_collection_documents (
                collection_id INTEGER NOT NULL REFERENCES note_collections(id) ON DELETE CASCADE,
                document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                added_at TIMESTAMPTZ DEFAULT NOW(),
                position INTEGER DEFAULT 0,
                PRIMARY KEY (collection_id, document_id)
            )
        """))

        conn.execute(text(
            "CREATE INDEX ix_ncd_collection_id ON note_collection_documents(collection_id)"
        ))
        conn.execute(text(
            "CREATE INDEX ix_ncd_document_id ON note_collection_documents(document_id)"
        ))

        # Migrate data from document_collections into note_collections
        doc_collections_exist = conn.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'document_collections')"
        )).scalar()

        if doc_collections_exist:
            logger.info("Migrating document_collections into note_collections...")
            rows = conn.execute(text(
                "SELECT id, owner_id, name, description, icon, color, "
                "created_at, updated_at FROM document_collections"
            ))

            for row in rows:
                insert_result = conn.execute(text(
                    "INSERT INTO note_collections "
                    "(owner_id, name, description, icon, color, created_at, updated_at) "
                    "VALUES (:owner_id, :name, :description, :icon, :color, "
                    ":created_at, :updated_at) RETURNING id"
                ), {
                    "owner_id": row.owner_id,
                    "name": row.name,
                    "description": row.description,
                    "icon": row.icon,
                    "color": row.color,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                })
                new_collection_id = insert_result.fetchone()[0]

                # Migrate document links
                doc_links = conn.execute(text(
                    "SELECT document_id, position "
                    "FROM document_collection_documents "
                    "WHERE collection_id = :old_id"
                ), {"old_id": row.id})

                for link in doc_links:
                    conn.execute(text(
                        "INSERT INTO note_collection_documents "
                        "(collection_id, document_id, position) "
                        "VALUES (:collection_id, :document_id, :position)"
                    ), {
                        "collection_id": new_collection_id,
                        "document_id": link.document_id,
                        "position": link.position,
                    })

            logger.info("Data migration from document_collections completed")

        conn.commit()
        logger.info("Unified collections migration completed successfully")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upgrade()
