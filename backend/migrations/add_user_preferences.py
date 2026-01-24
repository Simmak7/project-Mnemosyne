"""
Migration: Add User Preferences Table for Phase 3

Creates:
- user_preferences table for appearance and UI customization

Run: python -m migrations.add_user_preferences
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

# Try both import paths (for running inside container vs outside)
try:
    from core.database import engine
except ImportError:
    from app.core.database import engine


def run_migration():
    """Execute the user preferences migration."""

    with engine.connect() as conn:
        # ============================================
        # User Preferences Table
        # ============================================

        print("Creating user_preferences table...")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                theme VARCHAR(20) DEFAULT 'dark' NOT NULL,
                accent_color VARCHAR(20) DEFAULT 'blue' NOT NULL,
                ui_density VARCHAR(20) DEFAULT 'comfortable' NOT NULL,
                font_size VARCHAR(20) DEFAULT 'medium' NOT NULL,
                sidebar_collapsed BOOLEAN DEFAULT FALSE NOT NULL,
                default_view VARCHAR(50) DEFAULT 'notes' NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        # Index for user lookup
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id
            ON user_preferences(user_id)
        """))

        conn.commit()
        print("  user_preferences table created successfully")

        print("\n" + "="*50)
        print("User preferences migration completed!")
        print("="*50)


def rollback_migration():
    """Rollback the user preferences migration."""

    with engine.connect() as conn:
        print("Rolling back user preferences migration...")

        try:
            conn.execute(text("DROP TABLE IF EXISTS user_preferences CASCADE"))
            print("  Dropped table: user_preferences")
        except Exception as e:
            print(f"  Error dropping user_preferences: {e}")

        conn.commit()
        print("\nRollback completed!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="User preferences migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    args = parser.parse_args()

    if args.rollback:
        rollback_migration()
    else:
        run_migration()
