"""
Database migration script to add RAG (Retrieval-Augmented Generation) tables.

This script:
1. Creates conversations table for multi-turn chat
2. Creates chat_messages table for message history with RAG metadata
3. Creates message_citations table for tracking source attribution
4. Creates note_chunks table for paragraph-level retrieval
5. Creates image_chunks table for AI analysis content retrieval
6. Creates necessary indexes for efficient retrieval

Run this script with:
    docker-compose exec backend python migrations/add_rag_tables.py

Or locally:
    python backend/migrations/add_rag_tables.py
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


def check_index_exists(conn, index_name: str) -> bool:
    """Check if an index exists."""
    result = conn.execute(text(
        "SELECT COUNT(*) FROM pg_indexes WHERE indexname = :idx_name"
    ), {"idx_name": index_name})
    return result.scalar() > 0


def run_migration():
    """Execute the migration."""
    logger.info("=" * 80)
    logger.info("Starting RAG (Retrieval-Augmented Generation) tables migration")
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
                # Step 1: Create conversations table
                # ============================================
                logger.info("\n[1/7] Creating conversations table...")

                if check_table_exists(inspector, 'conversations'):
                    logger.info("  ✓ conversations table already exists, skipping")
                else:
                    logger.info("  + Creating conversations table")
                    conn.execute(text("""
                        CREATE TABLE conversations (
                            id SERIAL PRIMARY KEY,
                            owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                            title VARCHAR(255),
                            summary TEXT,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            is_archived BOOLEAN DEFAULT FALSE,
                            metadata JSONB DEFAULT '{}'
                        )
                    """))
                    conn.execute(text(
                        "CREATE INDEX idx_conversations_owner ON conversations(owner_id)"
                    ))
                    conn.execute(text(
                        "CREATE INDEX idx_conversations_updated ON conversations(updated_at DESC)"
                    ))
                    logger.info("  ✓ conversations table created successfully")

                # ============================================
                # Step 2: Create chat_messages table
                # ============================================
                logger.info("\n[2/7] Creating chat_messages table...")

                if check_table_exists(inspector, 'chat_messages'):
                    logger.info("  ✓ chat_messages table already exists, skipping")
                else:
                    logger.info("  + Creating chat_messages table")
                    conn.execute(text("""
                        CREATE TABLE chat_messages (
                            id SERIAL PRIMARY KEY,
                            conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
                            role VARCHAR(20) NOT NULL,
                            content TEXT NOT NULL,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            retrieval_metadata JSONB,
                            generation_metadata JSONB,
                            confidence_score FLOAT
                        )
                    """))
                    conn.execute(text(
                        "CREATE INDEX idx_chat_messages_conversation ON chat_messages(conversation_id)"
                    ))
                    conn.execute(text(
                        "CREATE INDEX idx_chat_messages_created ON chat_messages(created_at DESC)"
                    ))
                    logger.info("  ✓ chat_messages table created successfully")

                # ============================================
                # Step 3: Create message_citations table
                # ============================================
                logger.info("\n[3/7] Creating message_citations table...")

                if check_table_exists(inspector, 'message_citations'):
                    logger.info("  ✓ message_citations table already exists, skipping")
                else:
                    logger.info("  + Creating message_citations table")
                    conn.execute(text("""
                        CREATE TABLE message_citations (
                            id SERIAL PRIMARY KEY,
                            message_id INTEGER REFERENCES chat_messages(id) ON DELETE CASCADE,
                            source_type VARCHAR(20) NOT NULL,
                            source_id INTEGER NOT NULL,
                            citation_index INTEGER NOT NULL,
                            relevance_score FLOAT NOT NULL,
                            retrieval_method VARCHAR(50),
                            used_content TEXT,
                            relationship_chain JSONB,
                            hop_count INTEGER DEFAULT 0,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        )
                    """))
                    conn.execute(text(
                        "CREATE INDEX idx_message_citations_message ON message_citations(message_id)"
                    ))
                    conn.execute(text(
                        "CREATE INDEX idx_message_citations_source ON message_citations(source_type, source_id)"
                    ))
                    logger.info("  ✓ message_citations table created successfully")

                # ============================================
                # Step 4: Create note_chunks table
                # ============================================
                logger.info("\n[4/7] Creating note_chunks table...")

                if check_table_exists(inspector, 'note_chunks'):
                    logger.info("  ✓ note_chunks table already exists, skipping")
                else:
                    logger.info("  + Creating note_chunks table")
                    conn.execute(text("""
                        CREATE TABLE note_chunks (
                            id SERIAL PRIMARY KEY,
                            note_id INTEGER REFERENCES notes(id) ON DELETE CASCADE,
                            content TEXT NOT NULL,
                            chunk_index INTEGER NOT NULL,
                            chunk_type VARCHAR(20),
                            char_start INTEGER NOT NULL,
                            char_end INTEGER NOT NULL,
                            embedding vector(768),
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        )
                    """))
                    conn.execute(text(
                        "CREATE INDEX idx_note_chunks_note ON note_chunks(note_id)"
                    ))
                    logger.info("  ✓ note_chunks table created successfully")

                # ============================================
                # Step 5: Create image_chunks table
                # ============================================
                logger.info("\n[5/7] Creating image_chunks table...")

                if check_table_exists(inspector, 'image_chunks'):
                    logger.info("  ✓ image_chunks table already exists, skipping")
                else:
                    logger.info("  + Creating image_chunks table")
                    conn.execute(text("""
                        CREATE TABLE image_chunks (
                            id SERIAL PRIMARY KEY,
                            image_id INTEGER REFERENCES images(id) ON DELETE CASCADE,
                            content TEXT NOT NULL,
                            chunk_index INTEGER NOT NULL,
                            embedding vector(768),
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        )
                    """))
                    conn.execute(text(
                        "CREATE INDEX idx_image_chunks_image ON image_chunks(image_id)"
                    ))
                    logger.info("  ✓ image_chunks table created successfully")

                # ============================================
                # Step 6: Create vector indexes for chunk embeddings
                # ============================================
                logger.info("\n[6/7] Creating vector indexes for chunk embeddings...")

                if check_index_exists(conn, 'idx_note_chunks_embedding'):
                    logger.info("  ✓ idx_note_chunks_embedding index already exists, skipping")
                else:
                    logger.info("  + Creating IVFFlat index on note_chunks.embedding")
                    conn.execute(text("""
                        CREATE INDEX idx_note_chunks_embedding
                        ON note_chunks USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100)
                    """))
                    logger.info("  ✓ idx_note_chunks_embedding index created successfully")

                if check_index_exists(conn, 'idx_image_chunks_embedding'):
                    logger.info("  ✓ idx_image_chunks_embedding index already exists, skipping")
                else:
                    logger.info("  + Creating IVFFlat index on image_chunks.embedding")
                    conn.execute(text("""
                        CREATE INDEX idx_image_chunks_embedding
                        ON image_chunks USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100)
                    """))
                    logger.info("  ✓ idx_image_chunks_embedding index created successfully")

                # ============================================
                # Step 7: Verify table creation
                # ============================================
                logger.info("\n[7/7] Verifying table creation...")

                # Refresh inspector to see new tables
                inspector = inspect(engine)

                tables_to_check = [
                    'conversations',
                    'chat_messages',
                    'message_citations',
                    'note_chunks',
                    'image_chunks'
                ]

                all_exist = True
                for table in tables_to_check:
                    if check_table_exists(inspector, table):
                        logger.info(f"  ✓ {table} table exists")
                    else:
                        logger.warning(f"  ✗ {table} table NOT found")
                        all_exist = False

                if not all_exist:
                    raise Exception("Some tables were not created successfully")

                # Commit transaction
                trans.commit()
                logger.info("\n" + "=" * 80)
                logger.info("Migration completed successfully!")
                logger.info("=" * 80)

                # Summary
                logger.info("\nMigration Summary:")
                logger.info("  ✓ conversations table created (multi-turn chat)")
                logger.info("  ✓ chat_messages table created (message history)")
                logger.info("  ✓ message_citations table created (source tracking)")
                logger.info("  ✓ note_chunks table created (paragraph-level retrieval)")
                logger.info("  ✓ image_chunks table created (image content retrieval)")
                logger.info("  ✓ Vector indexes created for chunk embeddings")
                logger.info("\nNext steps:")
                logger.info("  1. Restart the backend service")
                logger.info("  2. Run chunk generation for existing notes/images")
                logger.info("  3. Generate embeddings for chunks")
                logger.info("  4. Deploy RAG endpoints")

            except Exception as e:
                trans.rollback()
                logger.error(f"\n Migration failed: {str(e)}", exc_info=True)
                logger.info("Transaction rolled back, no changes made")
                raise

    except Exception as e:
        logger.error(f"\n Database connection failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    logger.info("RAG Tables Migration Script")
    logger.info("=" * 80)

    try:
        run_migration()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Migration script failed: {str(e)}")
        sys.exit(1)
