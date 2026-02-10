"""
Migration: Add Performance Indexes

Adds composite indexes for common query patterns to improve performance:
1. Notes: (owner_id, is_trashed, created_at DESC) - primary list query
2. Notes: (owner_id, is_favorite) partial - favorites query
3. Images: (owner_id, is_trashed, uploaded_at DESC) - primary list query
4. Conversations: (owner_id, created_at DESC) - user's conversations
5. NoteChunks: (note_id) - for batch loading chunks
6. ImageChunks: (image_id) - for batch loading chunks

Run with:
    docker-compose exec backend python migrations/add_performance_indexes.py
"""

import os
import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

logger = logging.getLogger(__name__)


def upgrade():
    """Add performance indexes."""
    with engine.connect() as conn:
        indexes = [
            # Notes: Primary list query (owner's non-trashed notes, newest first)
            (
                "idx_notes_owner_trashed_created",
                """
                CREATE INDEX IF NOT EXISTS idx_notes_owner_trashed_created
                ON notes(owner_id, is_trashed, created_at DESC)
                """
            ),
            # Notes: Favorites query (partial index for efficiency)
            (
                "idx_notes_owner_favorite_partial",
                """
                CREATE INDEX IF NOT EXISTS idx_notes_owner_favorite_partial
                ON notes(owner_id)
                WHERE is_favorite = TRUE AND is_trashed = FALSE
                """
            ),
            # Notes: Review queue (partial index)
            (
                "idx_notes_owner_review_partial",
                """
                CREATE INDEX IF NOT EXISTS idx_notes_owner_review_partial
                ON notes(owner_id, created_at DESC)
                WHERE is_reviewed = FALSE AND is_trashed = FALSE
                """
            ),
            # Images: Primary list query (owner's non-trashed images, newest first)
            (
                "idx_images_owner_trashed_uploaded",
                """
                CREATE INDEX IF NOT EXISTS idx_images_owner_trashed_uploaded
                ON images(owner_id, is_trashed, uploaded_at DESC)
                """
            ),
            # Images: Favorites query (partial index)
            (
                "idx_images_owner_favorite_partial",
                """
                CREATE INDEX IF NOT EXISTS idx_images_owner_favorite_partial
                ON images(owner_id)
                WHERE is_favorite = TRUE AND is_trashed = FALSE
                """
            ),
            # Conversations: User's conversations list
            (
                "idx_conversations_owner_created",
                """
                CREATE INDEX IF NOT EXISTS idx_conversations_owner_created
                ON conversations(owner_id, created_at DESC)
                """
            ),
            # Conversations: Non-archived only (common filter)
            (
                "idx_conversations_owner_active",
                """
                CREATE INDEX IF NOT EXISTS idx_conversations_owner_active
                ON conversations(owner_id, updated_at DESC)
                WHERE is_archived = FALSE
                """
            ),
            # NoteChunks: For batch loading by note
            (
                "idx_note_chunks_note_id",
                """
                CREATE INDEX IF NOT EXISTS idx_note_chunks_note_id
                ON note_chunks(note_id, chunk_index)
                """
            ),
            # ImageChunks: For batch loading by image
            (
                "idx_image_chunks_image_id",
                """
                CREATE INDEX IF NOT EXISTS idx_image_chunks_image_id
                ON image_chunks(image_id, chunk_index)
                """
            ),
            # ChatMessages: For loading conversation history
            (
                "idx_chat_messages_conversation",
                """
                CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation
                ON chat_messages(conversation_id, created_at DESC)
                """
            ),
            # BrainFiles: For loading user's brain files
            (
                "idx_brain_files_owner_key",
                """
                CREATE INDEX IF NOT EXISTS idx_brain_files_owner_key
                ON brain_files(owner_id, file_key)
                """
            ),
        ]

        for index_name, create_sql in indexes:
            try:
                conn.execute(text(create_sql))
                conn.commit()
                logger.info(f"Created index: {index_name}")
            except Exception as e:
                logger.warning(f"Index {index_name} may already exist or failed: {e}")
                conn.rollback()

        logger.info("Performance indexes migration complete")


def downgrade():
    """Remove performance indexes."""
    with engine.connect() as conn:
        indexes = [
            "idx_notes_owner_trashed_created",
            "idx_notes_owner_favorite_partial",
            "idx_notes_owner_review_partial",
            "idx_images_owner_trashed_uploaded",
            "idx_images_owner_favorite_partial",
            "idx_conversations_owner_created",
            "idx_conversations_owner_active",
            "idx_note_chunks_note_id",
            "idx_image_chunks_image_id",
            "idx_chat_messages_conversation",
            "idx_brain_files_owner_key",
        ]

        for index_name in indexes:
            try:
                conn.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
                conn.commit()
                logger.info(f"Dropped index: {index_name}")
            except Exception as e:
                logger.warning(f"Failed to drop index {index_name}: {e}")
                conn.rollback()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upgrade()
    print("Performance indexes migration complete!")
