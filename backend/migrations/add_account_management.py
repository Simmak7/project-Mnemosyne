"""
Migration: Add Account Management Tables for Phase 2

User table additions:
- deleted_at: Soft delete timestamp
- scheduled_deletion_at: When permanent deletion will occur

Tables created:
- email_change_tokens: For email change verification

Run: python -m migrations.add_account_management
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
    """Execute the account management migration."""

    with engine.connect() as conn:
        # ============================================
        # User Table Additions for Soft Delete
        # ============================================

        print("Adding soft delete columns to users table...")

        user_columns = [
            ("deleted_at", "TIMESTAMP WITH TIME ZONE"),
            ("scheduled_deletion_at", "TIMESTAMP WITH TIME ZONE"),
        ]

        for col_name, col_type in user_columns:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                print(f"  Added column: users.{col_name}")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"  Column already exists: users.{col_name}")
                else:
                    print(f"  Error adding users.{col_name}: {e}")

        conn.commit()

        # ============================================
        # Email Change Tokens Table
        # ============================================

        print("\nCreating email_change_tokens table...")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS email_change_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                new_email VARCHAR(255) NOT NULL,
                token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        # Index for token lookup
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_email_change_tokens_token
            ON email_change_tokens(token)
        """))

        # Index for user's pending tokens
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_email_change_tokens_user_id
            ON email_change_tokens(user_id)
        """))

        conn.commit()
        print("  email_change_tokens table created successfully")

        # ============================================
        # Index for soft-deleted users cleanup
        # ============================================

        print("\nCreating index for soft-deleted users...")

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_scheduled_deletion
            ON users(scheduled_deletion_at)
            WHERE deleted_at IS NOT NULL
        """))

        conn.commit()
        print("  Index created successfully")

        print("\n" + "="*50)
        print("Account management migration completed!")
        print("="*50)


def rollback_migration():
    """Rollback the account management migration."""

    with engine.connect() as conn:
        print("Rolling back account management migration...")

        # Drop table
        try:
            conn.execute(text("DROP TABLE IF EXISTS email_change_tokens CASCADE"))
            print("  Dropped table: email_change_tokens")
        except Exception as e:
            print(f"  Error dropping email_change_tokens: {e}")

        # Drop index
        try:
            conn.execute(text("DROP INDEX IF EXISTS idx_users_scheduled_deletion"))
            print("  Dropped index: idx_users_scheduled_deletion")
        except Exception as e:
            print(f"  Error dropping index: {e}")

        # Remove user columns
        user_columns = ["deleted_at", "scheduled_deletion_at"]

        for col in user_columns:
            try:
                conn.execute(text(f"ALTER TABLE users DROP COLUMN IF EXISTS {col}"))
                print(f"  Dropped column: users.{col}")
            except Exception as e:
                print(f"  Error dropping users.{col}: {e}")

        conn.commit()
        print("\nRollback completed!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Account management migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    args = parser.parse_args()

    if args.rollback:
        rollback_migration()
    else:
        run_migration()
