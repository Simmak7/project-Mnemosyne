"""
Migration: Add display_name field to images table

This allows users to rename images with a friendly display name
while keeping the original file storage path unchanged.

Run with: python -c "from migrations.add_display_name import run; run()"
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import SessionLocal


def run():
    """Add display_name column to images table."""
    db = SessionLocal()
    try:
        # Check if column already exists
        check_query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'images' AND column_name = 'display_name'
        """)
        result = db.execute(check_query)
        if result.fetchone():
            print("Column 'display_name' already exists in images table. Skipping.")
            return

        # Add display_name column
        alter_query = text("""
            ALTER TABLE images
            ADD COLUMN display_name VARCHAR(255) NULL
        """)
        db.execute(alter_query)
        db.commit()
        print("✅ Added 'display_name' column to images table")

    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()


def rollback():
    """Remove display_name column from images table."""
    db = SessionLocal()
    try:
        alter_query = text("""
            ALTER TABLE images
            DROP COLUMN IF EXISTS display_name
        """)
        db.execute(alter_query)
        db.commit()
        print("✅ Removed 'display_name' column from images table")

    except Exception as e:
        db.rollback()
        print(f"❌ Rollback failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
