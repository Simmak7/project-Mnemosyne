"""Migration: Add Brain feature tables.

Tables created:
- brain_training_samples: Training samples for LoRA fine-tuning
- brain_condensed_facts: Extracted facts from user content
- brain_adapters: LoRA adapter versions
- brain_indexing_runs: Indexing run history

Run with:
    docker-compose exec backend python migrations/add_brain_tables.py
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine


def run_migration():
    """Create brain feature tables."""
    with engine.connect() as conn:
        # Check if tables already exist
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_name IN (
                'brain_training_samples',
                'brain_condensed_facts',
                'brain_adapters',
                'brain_indexing_runs'
            )
        """))
        existing_tables = {row[0] for row in result.fetchall()}

        if existing_tables:
            print(f"Tables already exist: {existing_tables}")

        # Create memory_type enum if not exists
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE memory_type AS ENUM ('episodic', 'semantic', 'preference');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))

        # Create brain_training_samples table
        if 'brain_training_samples' not in existing_tables:
            print("Creating brain_training_samples table...")
            conn.execute(text("""
                CREATE TABLE brain_training_samples (
                    id SERIAL PRIMARY KEY,
                    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

                    -- Sample content
                    instruction TEXT NOT NULL,
                    input_text TEXT,
                    output TEXT NOT NULL,

                    -- Classification
                    sample_type VARCHAR(50) NOT NULL,
                    memory_type memory_type NOT NULL DEFAULT 'semantic',

                    -- Provenance
                    source_note_ids JSONB DEFAULT '[]'::jsonb,
                    source_image_ids JSONB DEFAULT '[]'::jsonb,
                    source_chunk_ids JSONB DEFAULT '[]'::jsonb,

                    -- Quality signals
                    confidence FLOAT DEFAULT 0.7,
                    recurrence INTEGER DEFAULT 1,
                    stability_score FLOAT DEFAULT 0.5,
                    centrality_score FLOAT DEFAULT 0.0,

                    -- Training metadata
                    is_trained VARCHAR(20) DEFAULT 'pending',
                    adapter_version INTEGER,

                    -- Timestamps
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                CREATE INDEX idx_brain_samples_owner ON brain_training_samples(owner_id);
                CREATE INDEX idx_brain_samples_type ON brain_training_samples(sample_type);
                CREATE INDEX idx_brain_samples_trained ON brain_training_samples(is_trained);
            """))
            print("Created brain_training_samples table")

        # Create brain_condensed_facts table
        if 'brain_condensed_facts' not in existing_tables:
            print("Creating brain_condensed_facts table...")
            conn.execute(text("""
                CREATE TABLE brain_condensed_facts (
                    id SERIAL PRIMARY KEY,
                    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

                    -- Fact content
                    fact_text TEXT NOT NULL,
                    concept VARCHAR(255) NOT NULL,

                    -- Source tracking
                    source_note_id INTEGER REFERENCES notes(id) ON DELETE SET NULL,
                    source_chunk_id INTEGER,

                    -- Classification
                    fact_type VARCHAR(50) NOT NULL,
                    memory_type memory_type NOT NULL DEFAULT 'semantic',

                    -- Quality signals
                    confidence FLOAT DEFAULT 0.7,
                    recurrence INTEGER DEFAULT 1,
                    stability_score FLOAT DEFAULT 0.5,

                    -- Timestamps
                    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                CREATE INDEX idx_brain_facts_owner ON brain_condensed_facts(owner_id);
                CREATE INDEX idx_brain_facts_concept ON brain_condensed_facts(concept);
                CREATE INDEX idx_brain_facts_type ON brain_condensed_facts(fact_type);
            """))
            print("Created brain_condensed_facts table")

        # Create brain_adapters table
        if 'brain_adapters' not in existing_tables:
            print("Creating brain_adapters table...")
            conn.execute(text("""
                CREATE TABLE brain_adapters (
                    id SERIAL PRIMARY KEY,
                    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

                    -- Version info
                    version INTEGER NOT NULL,
                    parent_version INTEGER,
                    base_model VARCHAR(100) NOT NULL,

                    -- Training stats
                    dataset_size INTEGER DEFAULT 0,
                    notes_covered INTEGER DEFAULT 0,
                    images_covered INTEGER DEFAULT 0,
                    journal_days INTEGER DEFAULT 0,

                    -- Config
                    training_config JSONB DEFAULT '{}'::jsonb,
                    adapter_path VARCHAR(500),

                    -- Status
                    status VARCHAR(20) DEFAULT 'created',
                    is_active BOOLEAN DEFAULT FALSE,
                    error_message TEXT,

                    -- Timestamps
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    training_started_at TIMESTAMP WITH TIME ZONE,
                    training_completed_at TIMESTAMP WITH TIME ZONE
                );

                CREATE INDEX idx_brain_adapters_owner ON brain_adapters(owner_id);
                CREATE INDEX idx_brain_adapters_active ON brain_adapters(is_active) WHERE is_active = TRUE;
                CREATE UNIQUE INDEX idx_brain_adapters_version ON brain_adapters(owner_id, version);
            """))
            print("Created brain_adapters table")

        # Create brain_indexing_runs table
        if 'brain_indexing_runs' not in existing_tables:
            print("Creating brain_indexing_runs table...")
            conn.execute(text("""
                CREATE TABLE brain_indexing_runs (
                    id SERIAL PRIMARY KEY,
                    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

                    -- Stats
                    notes_processed INTEGER DEFAULT 0,
                    images_processed INTEGER DEFAULT 0,
                    facts_extracted INTEGER DEFAULT 0,
                    samples_generated INTEGER DEFAULT 0,
                    notes_changed INTEGER DEFAULT 0,
                    last_note_updated TIMESTAMP WITH TIME ZONE,

                    -- Status
                    status VARCHAR(20) DEFAULT 'running',
                    error_message TEXT,

                    -- Timing
                    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    completed_at TIMESTAMP WITH TIME ZONE,
                    duration_seconds INTEGER
                );

                CREATE INDEX idx_brain_runs_owner ON brain_indexing_runs(owner_id);
                CREATE INDEX idx_brain_runs_status ON brain_indexing_runs(status);
            """))
            print("Created brain_indexing_runs table")

        conn.commit()
        print("Brain feature migration completed successfully!")


def rollback_migration():
    """Drop brain feature tables (use with caution)."""
    with engine.connect() as conn:
        print("Rolling back brain feature tables...")
        conn.execute(text("""
            DROP TABLE IF EXISTS brain_indexing_runs CASCADE;
            DROP TABLE IF EXISTS brain_adapters CASCADE;
            DROP TABLE IF EXISTS brain_condensed_facts CASCADE;
            DROP TABLE IF EXISTS brain_training_samples CASCADE;
            DROP TYPE IF EXISTS memory_type CASCADE;
        """))
        conn.commit()
        print("Rollback completed")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Brain feature migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    args = parser.parse_args()

    if args.rollback:
        rollback_migration()
    else:
        run_migration()
