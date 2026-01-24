"""
Migration: Add Data Export Jobs Table for Phase 4

Creates:
- data_export_jobs table for tracking GDPR data exports

Run: python -m migrations.add_data_export_jobs
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
    """Execute the data export jobs migration."""

    with engine.connect() as conn:
        # ============================================
        # Data Export Jobs Table
        # ============================================

        print("Creating data_export_jobs table...")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS data_export_jobs (
                id SERIAL PRIMARY KEY,
                job_id VARCHAR(36) UNIQUE NOT NULL,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                progress INTEGER DEFAULT 0,
                file_path VARCHAR(500),
                file_size INTEGER,
                include_notes BOOLEAN DEFAULT TRUE,
                include_images BOOLEAN DEFAULT TRUE,
                include_tags BOOLEAN DEFAULT TRUE,
                include_activity BOOLEAN DEFAULT FALSE,
                error_message TEXT,
                expires_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                completed_at TIMESTAMP WITH TIME ZONE
            )
        """))

        # Index for job_id lookup
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_data_export_jobs_job_id
            ON data_export_jobs(job_id)
        """))

        # Index for user's jobs
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_data_export_jobs_user_id
            ON data_export_jobs(user_id)
        """))

        # Index for cleanup query (find expired jobs)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_data_export_jobs_expires
            ON data_export_jobs(expires_at)
            WHERE status = 'completed'
        """))

        conn.commit()
        print("  data_export_jobs table created successfully")

        print("\n" + "="*50)
        print("Data export jobs migration completed!")
        print("="*50)


def rollback_migration():
    """Rollback the data export jobs migration."""

    with engine.connect() as conn:
        print("Rolling back data export jobs migration...")

        try:
            conn.execute(text("DROP TABLE IF EXISTS data_export_jobs CASCADE"))
            print("  Dropped table: data_export_jobs")
        except Exception as e:
            print(f"  Error dropping data_export_jobs: {e}")

        conn.commit()
        print("\nRollback completed!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Data export jobs migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    args = parser.parse_args()

    if args.rollback:
        rollback_migration()
    else:
        run_migration()
