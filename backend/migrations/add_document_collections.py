"""
Migration: Add document_collections and document_collection_documents tables.

Run: docker-compose exec backend python -m migrations.add_document_collections
"""

import logging
from sqlalchemy import text
from core.database import engine

logger = logging.getLogger(__name__)


def upgrade():
    """Create document collections tables and indexes."""
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'document_collections')"
        ))
        if result.scalar():
            logger.info("document_collections table already exists, skipping")
            return

        logger.info("Creating document_collections table...")
        conn.execute(text("""
            CREATE TABLE document_collections (
                id SERIAL PRIMARY KEY,
                owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                icon VARCHAR(50),
                color VARCHAR(20),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        logger.info("Creating document_collection_documents junction table...")
        conn.execute(text("""
            CREATE TABLE document_collection_documents (
                collection_id INTEGER NOT NULL REFERENCES document_collections(id) ON DELETE CASCADE,
                document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                added_at TIMESTAMPTZ DEFAULT NOW(),
                position INTEGER DEFAULT 0,
                PRIMARY KEY (collection_id, document_id)
            )
        """))

        conn.execute(text("CREATE INDEX ix_doc_collections_owner_id ON document_collections(owner_id)"))
        conn.execute(text("CREATE INDEX ix_dcd_collection_id ON document_collection_documents(collection_id)"))
        conn.execute(text("CREATE INDEX ix_dcd_document_id ON document_collection_documents(document_id)"))

        conn.commit()
        logger.info("Document collections migration completed successfully")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upgrade()
