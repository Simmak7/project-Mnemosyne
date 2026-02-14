"""
Migration: Add AI usage tracking table.

Tracks token usage and estimated costs for cloud AI providers.
"""

import logging
from sqlalchemy import text
from core.database import engine

logger = logging.getLogger(__name__)


def upgrade():
    """Run the AI usage tracking migration."""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_usage_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                provider VARCHAR(20) NOT NULL,
                model VARCHAR(100) NOT NULL,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                estimated_cost_usd DECIMAL(10, 6) DEFAULT 0,
                use_case VARCHAR(20),
                conversation_id INTEGER NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        # Index for usage queries
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ai_usage_user_date
            ON ai_usage_logs(user_id, created_at)
        """))

        conn.commit()
        logger.info("AI usage tracking migration completed")
