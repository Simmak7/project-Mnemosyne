"""
Mnemosyne Brain Chat Router.

Endpoints for querying the brain and managing brain conversations.
Combines sub-routers: query, conversations.
"""

from fastapi import APIRouter

# Import sub-routers
from features.mnemosyne_brain.router_chat_query import router as query_router
from features.mnemosyne_brain.router_chat_stream import router as stream_router
from features.mnemosyne_brain.router_chat_conversations import router as conversations_router


def get_brain_chat_router() -> APIRouter:
    """Get the combined brain chat router with all endpoints."""
    combined = APIRouter()

    # Include all sub-routers (they share the "mnemosyne-brain-chat" tag and prefix)
    combined.include_router(query_router)
    combined.include_router(stream_router)
    combined.include_router(conversations_router)

    return combined


# Default export for backward compatibility
router = get_brain_chat_router()
