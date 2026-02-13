"""
Migration: Add NEXUS tables for graph-native adaptive retrieval.

Creates tables:
- nexus_citations: Rich citation tracking with graph metadata
- nexus_navigation_cache: Cached community maps and tag overviews
- nexus_importance_scores: PageRank scores per note
- nexus_link_suggestions: Missing link detection results
- nexus_access_patterns: Co-retrieval tracking

Run: docker-compose exec backend python -m migrations.add_nexus_tables
"""

import logging
from sqlalchemy import text
from core.database import engine

logger = logging.getLogger(__name__)


def _table_exists(conn, table_name: str) -> bool:
    """Check if a table already exists."""
    result = conn.execute(text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_name = :name)"
    ), {"name": table_name})
    return result.scalar()


def upgrade():
    """Create all NEXUS tables."""
    with engine.connect() as conn:
        # 1. nexus_citations
        if not _table_exists(conn, "nexus_citations"):
            logger.info("Creating nexus_citations table...")
            conn.execute(text("""
                CREATE TABLE nexus_citations (
                    id SERIAL PRIMARY KEY,
                    message_id INTEGER REFERENCES chat_messages(id)
                        ON DELETE CASCADE,
                    source_type VARCHAR(20) NOT NULL,
                    source_id INTEGER NOT NULL,
                    citation_index INTEGER NOT NULL,
                    relevance_score FLOAT,
                    retrieval_method VARCHAR(30),
                    origin_type VARCHAR(30),
                    artifact_id INTEGER,
                    community_name VARCHAR(255),
                    community_id INTEGER,
                    tags JSONB DEFAULT '[]',
                    direct_wikilinks JSONB DEFAULT '[]',
                    path_to_other_results JSONB DEFAULT '[]',
                    note_url VARCHAR(500),
                    graph_url VARCHAR(500),
                    artifact_url VARCHAR(500),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_nexus_citations_message "
                "ON nexus_citations (message_id)"
            ))
            logger.info("nexus_citations table created")
        else:
            logger.info("nexus_citations already exists, skipping")

        # 2. nexus_navigation_cache
        if not _table_exists(conn, "nexus_navigation_cache"):
            logger.info("Creating nexus_navigation_cache table...")
            conn.execute(text("""
                CREATE TABLE nexus_navigation_cache (
                    id SERIAL PRIMARY KEY,
                    owner_id INTEGER REFERENCES users(id)
                        ON DELETE CASCADE,
                    cache_type VARCHAR(30) NOT NULL,
                    content TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE (owner_id, cache_type)
                )
            """))
            logger.info("nexus_navigation_cache table created")
        else:
            logger.info("nexus_navigation_cache already exists, skipping")

        # 3. nexus_importance_scores
        if not _table_exists(conn, "nexus_importance_scores"):
            logger.info("Creating nexus_importance_scores table...")
            conn.execute(text("""
                CREATE TABLE nexus_importance_scores (
                    id SERIAL PRIMARY KEY,
                    owner_id INTEGER REFERENCES users(id)
                        ON DELETE CASCADE,
                    note_id INTEGER REFERENCES notes(id)
                        ON DELETE CASCADE,
                    pagerank_score FLOAT DEFAULT 0.0,
                    access_count INTEGER DEFAULT 0,
                    retrieval_count INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE (owner_id, note_id)
                )
            """))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_nexus_importance_owner "
                "ON nexus_importance_scores (owner_id)"
            ))
            logger.info("nexus_importance_scores table created")
        else:
            logger.info("nexus_importance_scores already exists, skipping")

        # 4. nexus_link_suggestions
        if not _table_exists(conn, "nexus_link_suggestions"):
            logger.info("Creating nexus_link_suggestions table...")
            conn.execute(text("""
                CREATE TABLE nexus_link_suggestions (
                    id SERIAL PRIMARY KEY,
                    owner_id INTEGER REFERENCES users(id)
                        ON DELETE CASCADE,
                    source_note_id INTEGER REFERENCES notes(id)
                        ON DELETE CASCADE,
                    target_note_id INTEGER REFERENCES notes(id)
                        ON DELETE CASCADE,
                    similarity_score FLOAT NOT NULL,
                    co_retrieval_count INTEGER DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'pending',
                    suggested_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE (owner_id, source_note_id, target_note_id)
                )
            """))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_nexus_suggestions_owner "
                "ON nexus_link_suggestions (owner_id, status)"
            ))
            logger.info("nexus_link_suggestions table created")
        else:
            logger.info("nexus_link_suggestions already exists, skipping")

        # 5. nexus_access_patterns
        if not _table_exists(conn, "nexus_access_patterns"):
            logger.info("Creating nexus_access_patterns table...")
            conn.execute(text("""
                CREATE TABLE nexus_access_patterns (
                    id SERIAL PRIMARY KEY,
                    owner_id INTEGER REFERENCES users(id)
                        ON DELETE CASCADE,
                    note_id_a INTEGER NOT NULL,
                    note_id_b INTEGER NOT NULL,
                    co_retrieval_count INTEGER DEFAULT 1,
                    last_co_retrieved_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE (owner_id, note_id_a, note_id_b)
                )
            """))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_nexus_access_owner "
                "ON nexus_access_patterns (owner_id)"
            ))
            logger.info("nexus_access_patterns table created")
        else:
            logger.info("nexus_access_patterns already exists, skipping")

        # Add nexus_model column to user_preferences if missing
        col_check = conn.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'user_preferences' AND column_name = 'nexus_model')"
        ))
        if not col_check.scalar():
            conn.execute(text(
                "ALTER TABLE user_preferences ADD COLUMN nexus_model VARCHAR(100)"
            ))
            logger.info("Added nexus_model column to user_preferences")

        conn.commit()
        logger.info("NEXUS tables migration completed successfully")


if __name__ == "__main__":
    upgrade()
