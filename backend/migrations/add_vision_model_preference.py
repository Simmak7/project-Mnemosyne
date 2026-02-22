"""
Migration: Add vision_model preference to user_preferences table.

Allows users to select their preferred vision model for image analysis.
"""

from sqlalchemy import text
from core.database import SessionLocal


def upgrade():
    """Add vision_model column to user_preferences table."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'user_preferences' AND column_name = 'vision_model'
        """))
        if result.fetchone():
            print("Column 'vision_model' already exists. Skipping.")
            return

        db.execute(text("""
            ALTER TABLE user_preferences
            ADD COLUMN vision_model VARCHAR(100) DEFAULT NULL
        """))
        db.commit()
        print("Added 'vision_model' column to user_preferences table")

    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    upgrade()
