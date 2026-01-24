"""
Migration: Add Security Tables for Phase 1

Tables created:
- password_reset_tokens: For password reset functionality
- user_2fa: Two-factor authentication secrets and backup codes
- login_attempts: Track failed/successful logins for account lockout

User table additions:
- display_name, avatar_url: Profile settings
- is_active, is_locked, locked_until: Account status
- failed_login_attempts: Lockout counter
- last_login, password_changed_at: Audit timestamps

Run: python -m migrations.add_security_tables
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
    """Execute the security tables migration."""

    with engine.connect() as conn:
        # ============================================
        # User Table Additions
        # ============================================

        print("Adding new columns to users table...")

        user_columns = [
            ("display_name", "VARCHAR(100)"),
            ("avatar_url", "VARCHAR(500)"),
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("is_locked", "BOOLEAN DEFAULT FALSE"),
            ("locked_until", "TIMESTAMP WITH TIME ZONE"),
            ("failed_login_attempts", "INTEGER DEFAULT 0"),
            ("last_login", "TIMESTAMP WITH TIME ZONE"),
            ("password_changed_at", "TIMESTAMP WITH TIME ZONE"),
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
        # Password Reset Tokens Table
        # ============================================

        print("\nCreating password_reset_tokens table...")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        # Index for token lookup
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token
            ON password_reset_tokens(token)
        """))

        # Index for cleanup query (find expired tokens)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires
            ON password_reset_tokens(expires_at)
        """))

        conn.commit()
        print("  password_reset_tokens table created successfully")

        # ============================================
        # User 2FA Table
        # ============================================

        print("\nCreating user_2fa table...")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_2fa (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                secret_key VARCHAR(32) NOT NULL,
                is_enabled BOOLEAN DEFAULT FALSE,
                backup_codes TEXT[],
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        conn.commit()
        print("  user_2fa table created successfully")

        # ============================================
        # Login Attempts Table
        # ============================================

        print("\nCreating login_attempts table...")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                username VARCHAR(255),
                ip_address VARCHAR(45),
                user_agent TEXT,
                success BOOLEAN NOT NULL,
                failure_reason VARCHAR(100),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        # Index for user login history
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_login_attempts_user_id
            ON login_attempts(user_id)
        """))

        # Index for recent attempts query (lockout check)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_login_attempts_created
            ON login_attempts(created_at DESC)
        """))

        # Composite index for lockout check (user + recent + failed)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_login_attempts_lockout
            ON login_attempts(user_id, created_at DESC)
            WHERE success = FALSE
        """))

        conn.commit()
        print("  login_attempts table created successfully")

        # ============================================
        # User Sessions Table (for session management)
        # ============================================

        print("\nCreating user_sessions table...")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_hash VARCHAR(255) NOT NULL,
                device_info TEXT,
                ip_address VARCHAR(45),
                last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                is_revoked BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        # Index for user's sessions
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id
            ON user_sessions(user_id)
        """))

        # Index for token validation
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_sessions_token_hash
            ON user_sessions(token_hash)
        """))

        conn.commit()
        print("  user_sessions table created successfully")

        print("\n" + "="*50)
        print("Security tables migration completed successfully!")
        print("="*50)


def rollback_migration():
    """Rollback the security tables migration."""

    with engine.connect() as conn:
        print("Rolling back security tables migration...")

        # Drop tables in reverse order (dependencies)
        tables = [
            "user_sessions",
            "login_attempts",
            "user_2fa",
            "password_reset_tokens"
        ]

        for table in tables:
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"  Dropped table: {table}")
            except Exception as e:
                print(f"  Error dropping {table}: {e}")

        # Remove user columns
        user_columns = [
            "display_name",
            "avatar_url",
            "is_active",
            "is_locked",
            "locked_until",
            "failed_login_attempts",
            "last_login",
            "password_changed_at"
        ]

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

    parser = argparse.ArgumentParser(description="Security tables migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()

    if args.rollback:
        rollback_migration()
    else:
        run_migration()
