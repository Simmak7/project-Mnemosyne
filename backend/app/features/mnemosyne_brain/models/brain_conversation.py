"""Brain conversation and message models - separate from RAG conversations."""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class BrainConversation(Base):
    """A conversation in brain mode (separate from RAG conversations)."""
    __tablename__ = "brain_conversations"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    brain_files_used = Column(JSONB, nullable=True)  # ["soul", "topic_0", ...]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_archived = Column(Boolean, default=False)

    messages = relationship(
        "BrainMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="BrainMessage.created_at",
    )


class BrainMessage(Base):
    """A message within a brain conversation."""
    __tablename__ = "brain_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("brain_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(String(10), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    brain_files_loaded = Column(JSONB, nullable=True)  # ["soul", "mnemosyne", "topic_2"]
    topics_matched = Column(JSONB, nullable=True)  # [{"key": "topic_0", "score": 0.85}]
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("BrainConversation", back_populates="messages")
