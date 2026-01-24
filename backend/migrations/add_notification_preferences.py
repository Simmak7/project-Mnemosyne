"""
Migration: Add Notification Preferences Table (Phase 5: Settings)

Creates the notification_preferences table for user notification settings.

Run: python -m migrations.add_notification_preferences
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
    """Execute the notification preferences migration."""

    with engine.connect() as conn:
        # ============================================
        # Notification Preferences Table
        # ============================================

        print("Creating notification_preferences table...")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS notification_preferences (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,

                -- Email notifications
                email_security_alerts BOOLEAN NOT NULL DEFAULT TRUE,
                email_weekly_digest BOOLEAN NOT NULL DEFAULT FALSE,
                email_product_updates BOOLEAN NOT NULL DEFAULT TRUE,

                -- Push notifications (future)
                push_enabled BOOLEAN NOT NULL DEFAULT FALSE,

                -- Timestamps
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        # Index for user_id lookup
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_notification_preferences_user_id
            ON notification_preferences(user_id)
        """))

        conn.commit()
        print("  notification_preferences table created successfully")

        print("\n" + "="*50)
        print("Notification preferences migration completed!")
        print("="*50)


def rollback_migration():
    """Rollback the notification preferences migration."""

    with engine.connect() as conn:
        print("Rolling back notification preferences migration...")

        try:
            conn.execute(text("DROP TABLE IF EXISTS notification_preferences CASCADE"))
            print("  Dropped table: notification_preferences")
        except Exception as e:
            print(f"  Error dropping notification_preferences: {e}")

        conn.commit()
        print("\nRollback completed!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Notification preferences migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    args = parser.parse_args()

    if args.rollback:
        rollback_migration()
    else:
        run_migration()
