"""
RAG Chat Models - Re-exports from main models.py (transitional pattern).

During fractal migration, these models remain in the root models.py because:
1. Other features reference them (search, tasks)
2. SQLAlchemy requires each table be defined once per metadata registry

Models exported:
- Conversation: Multi-turn conversation container
- ChatMessage: Individual messages with role (user/assistant)
- MessageCitation: Source attribution tracking
- NoteChunk: Paragraph-level chunks of notes with embeddings
- ImageChunk: Chunks of image AI analysis with embeddings
"""

from models import (
    Conversation,
    ChatMessage,
    MessageCitation,
    NoteChunk,
    ImageChunk,
)

__all__ = [
    "Conversation",
    "ChatMessage",
    "MessageCitation",
    "NoteChunk",
    "ImageChunk",
]
