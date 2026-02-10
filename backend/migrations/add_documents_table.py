"""
Migration: Add documents, document_tags, document_chunks tables.

Run: docker-compose exec backend python -m migrations.add_documents_table
"""

import logging
from sqlalchemy import text
from core.database import engine

logger = logging.getLogger(__name__)


def upgrade():
    """Create documents tables and indexes."""
    with engine.connect() as conn:
        # Check if documents table exists
        result = conn.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'documents')"
        ))
        if result.scalar():
            logger.info("documents table already exists, skipping")
            return

        logger.info("Creating documents table...")
        conn.execute(text("""
            CREATE TABLE documents (
                id SERIAL PRIMARY KEY,
                owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                filename VARCHAR NOT NULL,
                filepath VARCHAR NOT NULL,
                display_name VARCHAR(255),
                file_size INTEGER,
                page_count INTEGER,
                document_type VARCHAR(50),
                thumbnail_path VARCHAR(500),
                blur_hash VARCHAR(32),
                extracted_text TEXT,
                extraction_method VARCHAR(50),
                ai_summary TEXT,
                ai_analysis_status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                ai_analysis_result TEXT,
                suggested_tags JSONB DEFAULT '[]'::jsonb,
                suggested_wikilinks JSONB DEFAULT '[]'::jsonb,
                summary_note_id INTEGER REFERENCES notes(id) ON DELETE SET NULL,
                embedding vector(768),
                is_trashed BOOLEAN DEFAULT FALSE NOT NULL,
                trashed_at TIMESTAMPTZ,
                uploaded_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
                processed_at TIMESTAMPTZ,
                approved_at TIMESTAMPTZ
            )
        """))

        logger.info("Creating document_tags table...")
        conn.execute(text("""
            CREATE TABLE document_tags (
                document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
                PRIMARY KEY (document_id, tag_id)
            )
        """))

        logger.info("Creating document_chunks table...")
        conn.execute(text("""
            CREATE TABLE document_chunks (
                id SERIAL PRIMARY KEY,
                document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_type VARCHAR(20),
                page_number INTEGER,
                char_start INTEGER,
                char_end INTEGER,
                embedding vector(768),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        # Indexes
        conn.execute(text("CREATE INDEX ix_documents_owner_id ON documents(owner_id)"))
        conn.execute(text("CREATE INDEX ix_documents_status ON documents(ai_analysis_status)"))
        conn.execute(text("CREATE INDEX ix_documents_uploaded ON documents(uploaded_at DESC)"))
        conn.execute(text("CREATE INDEX ix_documents_trashed ON documents(is_trashed)"))
        conn.execute(text("CREATE INDEX ix_document_chunks_doc ON document_chunks(document_id)"))

        conn.commit()
        logger.info("Documents migration completed successfully")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upgrade()
