"""
Migration: Add custom_vision_prompt to user_preferences table.

Allows users to override the default system prompt for image analysis.
"""

from sqlalchemy import text
from core.database import SessionLocal


def upgrade():
    """Add custom_vision_prompt column to user_preferences table."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'user_preferences' AND column_name = 'custom_vision_prompt'
        """))
        if result.fetchone():
            print("Column 'custom_vision_prompt' already exists. Skipping.")
            return

        db.execute(text("""
            ALTER TABLE user_preferences
            ADD COLUMN custom_vision_prompt TEXT DEFAULT NULL
        """))
        db.commit()
        print("Added 'custom_vision_prompt' column to user_preferences table")

    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    upgrade()
