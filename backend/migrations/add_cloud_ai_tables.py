"""
Migration: Add Cloud AI tables.

Creates user_api_keys table and adds cloud AI preference columns
to user_preferences.
"""

import logging
from sqlalchemy import text
from core.database import engine

logger = logging.getLogger(__name__)


def upgrade():
    """Run the cloud AI migration."""
    with engine.connect() as conn:
        # Create user_api_keys table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_api_keys (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                provider VARCHAR(20) NOT NULL,
                encrypted_key TEXT NOT NULL,
                key_hint VARCHAR(12),
                is_valid BOOLEAN DEFAULT TRUE,
                base_url VARCHAR(500) NULL,
                last_validated_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(user_id, provider)
            )
        """))
        logger.info("Created user_api_keys table")

        # Add cloud AI columns to user_preferences
        cols = {
            "cloud_ai_enabled": "BOOLEAN DEFAULT FALSE",
            "cloud_ai_provider": "VARCHAR(20) NULL",
            "cloud_rag_model": "VARCHAR(100) NULL",
            "cloud_brain_model": "VARCHAR(100) NULL",
        }

        for col_name, col_def in cols.items():
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'user_preferences'
                AND column_name = :col
            """), {"col": col_name})
            if not result.fetchone():
                conn.execute(text(
                    f"ALTER TABLE user_preferences ADD COLUMN {col_name} {col_def}"
                ))
                logger.info(f"Added column {col_name} to user_preferences")

        conn.commit()
        logger.info("Cloud AI migration completed")
