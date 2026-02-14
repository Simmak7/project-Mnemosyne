"""
RAG (Retrieval-Augmented Generation) API router.

Combines all RAG sub-routers:
- Query endpoints (stateless and streaming RAG queries)
- Conversation endpoints (CRUD for chat history)
- Health endpoint (system status)
"""

import logging

from fastapi import APIRouter, Depends
import requests

from core import config
from core.database import get_db
from core.auth import get_current_user
from sqlalchemy.orm import Session
import models

# Import sub-routers
from features.rag_chat.router_query import router as query_router
from features.rag_chat.router_conversations import router as conversations_router
from features.rag_chat.services.ollama_client import check_ollama_health

logger = logging.getLogger(__name__)

# Main router - combines all sub-routers
router = APIRouter(prefix="/rag", tags=["rag"])

# Include sub-routers (they have their own /rag prefix, so we strip it)
# We need to include the routes directly since they already have /rag prefix
# Instead, we create a new combined approach

# Create the main router that will be exported
main_router = APIRouter(tags=["rag"])


@main_router.get("/rag/health")
async def rag_health():
    """
    Check RAG system health.

    Returns status of:
    - Ollama connectivity
    - Required models availability
    """
    health = check_ollama_health()

    return {
        "status": "healthy" if health.get("healthy") else "degraded",
        "ollama": {
            "connected": health.get("connected", False),
            "rag_model": health.get("rag_model", "unknown"),
            "rag_model_available": health.get("rag_model_available", False),
            "embedding_model_available": health.get("embedding_model_available", False)
        },
        "available_models": health.get("available_models", [])
    }


@main_router.post("/rag/backfill-chunks")
async def backfill_chunks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Trigger chunk backfill for all of the current user's notes.
    One-time operation to generate chunks for existing notes.
    """
    try:
        from features.rag_chat.tasks import backfill_all_chunks_task
        result = backfill_all_chunks_task.delay(owner_id=current_user.id)
        return {
            "status": "queued",
            "task_id": str(result.id),
            "message": "Chunk backfill started for all your notes.",
        }
    except Exception as e:
        logger.error(f"Failed to queue chunk backfill: {e}")
        return {"status": "error", "message": str(e)}


@main_router.post("/rag/backfill-embeddings")
async def backfill_embeddings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Generate embeddings for notes that are missing them.
    Only queues tasks for notes with content but no embedding.
    """
    try:
        from sqlalchemy import text
        from features.search.tasks import generate_note_embedding_task

        result = db.execute(text("""
            SELECT id FROM notes
            WHERE owner_id = :owner_id
              AND embedding IS NULL
              AND is_trashed = false
              AND LENGTH(TRIM(COALESCE(content, ''))) > 10
        """), {"owner_id": current_user.id})

        note_ids = [row.id for row in result]

        queued = 0
        for note_id in note_ids:
            generate_note_embedding_task.delay(note_id)
            queued += 1

        logger.info(f"Backfill-embeddings: queued {queued} notes for user {current_user.id}")
        return {
            "status": "queued",
            "notes_queued": queued,
            "message": f"Embedding generation queued for {queued} notes missing embeddings.",
        }
    except Exception as e:
        logger.error(f"Failed to queue embedding backfill: {e}")
        return {"status": "error", "message": str(e)}


# Re-export combined router
# The sub-routers already have /rag prefix, so include them at root
def get_rag_router() -> APIRouter:
    """Get the combined RAG router with all endpoints."""
    combined = APIRouter()

    # Include query routes (POST /rag/query, POST /rag/query/stream)
    combined.include_router(query_router)

    # Include conversation routes (CRUD /rag/conversations)
    combined.include_router(conversations_router)

    # Include health route
    combined.include_router(main_router)

    return combined


# Default export for backward compatibility
router = get_rag_router()
