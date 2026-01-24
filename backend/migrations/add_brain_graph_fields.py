"""
Migration: Add Brain Graph fields for typed graph visualization

Phase 0 of Brain Graph Transformation:
- Adds community_id to notes table (for Louvain/Leiden clustering)
- Creates semantic_edges table (for embedding-based similarity links)
- Creates graph_positions table (for stable Map view positions)
"""

import psycopg2
import os


def run_migration():
    """Add brain graph fields and tables."""
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
        # ============================================
        # 1. Add community_id to notes table
        # ============================================
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'notes' AND column_name = 'community_id'
        """)

        if not cur.fetchone():
            print("Adding 'community_id' column to 'notes' table...")
            cur.execute("""
                ALTER TABLE notes
                ADD COLUMN community_id INTEGER DEFAULT NULL
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS ix_notes_community_id ON notes (community_id)
            """)
            print("Added 'community_id' column successfully.")
        else:
            print("Column 'community_id' already exists. Skipping.")

        # ============================================
        # 2. Create semantic_edges table
        # ============================================
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'semantic_edges'
        """)

        if not cur.fetchone():
            print("Creating 'semantic_edges' table...")
            cur.execute("""
                CREATE TABLE semantic_edges (
                    id SERIAL PRIMARY KEY,
                    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    source_type VARCHAR(20) NOT NULL,
                    source_id INTEGER NOT NULL,
                    target_type VARCHAR(20) NOT NULL,
                    target_id INTEGER NOT NULL,
                    similarity_score FLOAT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    CONSTRAINT unique_semantic_edge UNIQUE (owner_id, source_type, source_id, target_type, target_id)
                )
            """)
            # Indexes for efficient queries
            cur.execute("""
                CREATE INDEX ix_semantic_edges_owner ON semantic_edges (owner_id)
            """)
            cur.execute("""
                CREATE INDEX ix_semantic_edges_source ON semantic_edges (source_type, source_id)
            """)
            cur.execute("""
                CREATE INDEX ix_semantic_edges_target ON semantic_edges (target_type, target_id)
            """)
            cur.execute("""
                CREATE INDEX ix_semantic_edges_score ON semantic_edges (similarity_score DESC)
            """)
            print("Created 'semantic_edges' table successfully.")
        else:
            print("Table 'semantic_edges' already exists. Skipping.")

        # ============================================
        # 3. Create graph_positions table
        # ============================================
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'graph_positions'
        """)

        if not cur.fetchone():
            print("Creating 'graph_positions' table...")
            cur.execute("""
                CREATE TABLE graph_positions (
                    id SERIAL PRIMARY KEY,
                    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    node_type VARCHAR(20) NOT NULL,
                    node_id INTEGER NOT NULL,
                    x FLOAT NOT NULL DEFAULT 0.0,
                    y FLOAT NOT NULL DEFAULT 0.0,
                    is_pinned BOOLEAN DEFAULT FALSE,
                    view_type VARCHAR(20) DEFAULT 'map',
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    CONSTRAINT unique_graph_position UNIQUE (owner_id, node_type, node_id, view_type)
                )
            """)
            cur.execute("""
                CREATE INDEX ix_graph_positions_owner ON graph_positions (owner_id)
            """)
            cur.execute("""
                CREATE INDEX ix_graph_positions_node ON graph_positions (node_type, node_id)
            """)
            print("Created 'graph_positions' table successfully.")
        else:
            print("Table 'graph_positions' already exists. Skipping.")

        # ============================================
        # 4. Create community_metadata table
        # ============================================
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'community_metadata'
        """)

        if not cur.fetchone():
            print("Creating 'community_metadata' table...")
            cur.execute("""
                CREATE TABLE community_metadata (
                    id SERIAL PRIMARY KEY,
                    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    community_id INTEGER NOT NULL,
                    label VARCHAR(255),
                    node_count INTEGER DEFAULT 0,
                    top_terms TEXT,
                    center_x FLOAT DEFAULT 0.0,
                    center_y FLOAT DEFAULT 0.0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    CONSTRAINT unique_community UNIQUE (owner_id, community_id)
                )
            """)
            cur.execute("""
                CREATE INDEX ix_community_metadata_owner ON community_metadata (owner_id)
            """)
            print("Created 'community_metadata' table successfully.")
        else:
            print("Table 'community_metadata' already exists. Skipping.")

        print("\n=== Brain Graph Migration completed successfully! ===")

    except Exception as e:
        print(f"Migration failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run_migration()
