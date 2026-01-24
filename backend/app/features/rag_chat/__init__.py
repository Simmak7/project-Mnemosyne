"""
RAG Chat Feature - Citation-aware AI Chat with Retrieval-Augmented Generation.

This feature provides:
- Multi-source retrieval (semantic, wikilink graph, full-text, images)
- Source citation tracking with relevance scores
- Multi-hop relationship chain explanation
- Hybrid streaming responses (SSE)
- Conversation management

Components:
- models: SQLAlchemy models (Conversation, ChatMessage, MessageCitation, NoteChunk, ImageChunk)
- schemas: Pydantic validation schemas
- router: FastAPI endpoints
- tasks: Celery background tasks for chunking
- services/: Retrieval, ranking, context building modules
"""

from features.rag_chat.router import router
from features.rag_chat import models
from features.rag_chat import schemas
from features.rag_chat import tasks

__all__ = [
    "router",
    "models",
    "schemas",
    "tasks",
]
