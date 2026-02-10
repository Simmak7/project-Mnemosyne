"""
Migration: Add AI model preference fields to user_preferences table

This allows users to select their preferred AI models for RAG and Brain features.

Run with: python -c "from migrations.add_model_preferences import run; run()"
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import SessionLocal


def run():
    """Add rag_model and brain_model columns to user_preferences table."""
    db = SessionLocal()
    try:
        # Check if rag_model column already exists
        check_query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'user_preferences' AND column_name = 'rag_model'
        """)
        result = db.execute(check_query)
        if result.fetchone():
            print("Column 'rag_model' already exists in user_preferences table. Skipping.")
        else:
            # Add rag_model column
            alter_query = text("""
                ALTER TABLE user_preferences
                ADD COLUMN rag_model VARCHAR(100) NULL
            """)
            db.execute(alter_query)
            db.commit()
            print("Added 'rag_model' column to user_preferences table")

        # Check if brain_model column already exists
        check_query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'user_preferences' AND column_name = 'brain_model'
        """)
        result = db.execute(check_query)
        if result.fetchone():
            print("Column 'brain_model' already exists in user_preferences table. Skipping.")
        else:
            # Add brain_model column
            alter_query = text("""
                ALTER TABLE user_preferences
                ADD COLUMN brain_model VARCHAR(100) NULL
            """)
            db.execute(alter_query)
            db.commit()
            print("Added 'brain_model' column to user_preferences table")

        print("Migration completed successfully")

    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        db.close()


def rollback():
    """Remove model preference columns from user_preferences table."""
    db = SessionLocal()
    try:
        alter_query = text("""
            ALTER TABLE user_preferences
            DROP COLUMN IF EXISTS rag_model,
            DROP COLUMN IF EXISTS brain_model
        """)
        db.execute(alter_query)
        db.commit()
        print("Removed model preference columns from user_preferences table")

    except Exception as e:
        db.rollback()
        print(f"Rollback failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
