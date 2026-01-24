"""
Migration: Add is_reviewed field to notes table

This adds the is_reviewed boolean column for the review queue feature.
"""

import psycopg2
from psycopg2 import sql
import os


def run_migration():
    """Add is_reviewed column to notes table."""
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/noteai")

    # Parse the database URL
    if database_url.startswith("postgresql://"):
        parts = database_url.replace("postgresql://", "").split("@")
        user_pass = parts[0].split(":")
        host_db = parts[1].split("/")
        host_port = host_db[0].split(":")

        conn_params = {
            "user": user_pass[0],
            "password": user_pass[1] if len(user_pass) > 1 else "",
            "host": host_port[0],
            "port": host_port[1] if len(host_port) > 1 else "5432",
            "database": host_db[1]
        }
    else:
        raise ValueError("Invalid DATABASE_URL format")

    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True
    cur = conn.cursor()

    try:
        # Check if the column already exists
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'notes' AND column_name = 'is_reviewed'
        """)

        if cur.fetchone():
            print("Column 'is_reviewed' already exists in 'notes' table. Skipping migration.")
            return

        # Add the is_reviewed column
        print("Adding 'is_reviewed' column to 'notes' table...")
        cur.execute("""
            ALTER TABLE notes
            ADD COLUMN is_reviewed BOOLEAN NOT NULL DEFAULT FALSE
        """)

        # Create index for performance
        print("Creating index on 'is_reviewed' column...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_notes_is_reviewed ON notes (is_reviewed)
        """)

        print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run_migration()
