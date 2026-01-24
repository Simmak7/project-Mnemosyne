"""
Migration: Add note_collections tables

Adds tables for grouping notes into collections (similar to Albums for images).
"""

import psycopg2
import os


def run_migration():
    """Create note_collections and note_collection_notes tables."""
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
        # Check if table already exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'note_collections'
            )
        """)
        if cur.fetchone()[0]:
            print("Table 'note_collections' already exists. Skipping migration.")
            return

        # Create note_collections table
        print("Creating 'note_collections' table...")
        cur.execute("""
            CREATE TABLE note_collections (
                id SERIAL PRIMARY KEY,
                owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                icon VARCHAR(50),
                color VARCHAR(20),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # Create indexes
        cur.execute("CREATE INDEX ix_note_collections_owner_id ON note_collections (owner_id)")

        # Create junction table
        print("Creating 'note_collection_notes' table...")
        cur.execute("""
            CREATE TABLE note_collection_notes (
                collection_id INTEGER NOT NULL REFERENCES note_collections(id) ON DELETE CASCADE,
                note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
                added_at TIMESTAMPTZ DEFAULT NOW(),
                position INTEGER DEFAULT 0,
                PRIMARY KEY (collection_id, note_id)
            )
        """)

        # Create indexes for junction table
        cur.execute("CREATE INDEX ix_note_collection_notes_collection_id ON note_collection_notes (collection_id)")
        cur.execute("CREATE INDEX ix_note_collection_notes_note_id ON note_collection_notes (note_id)")

        print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run_migration()
