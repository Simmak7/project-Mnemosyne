from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Profile fields (Phase 1: Settings)
    display_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Account status (Phase 1: Security)
    is_active = Column(Boolean, default=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)

    # Audit timestamps (Phase 1: Security)
    last_login = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)

    # Soft delete (Phase 2: Account Management)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    scheduled_deletion_at = Column(DateTime(timezone=True), nullable=True)

    images = relationship("Image", back_populates="owner")
    notes = relationship("Note", back_populates="owner")
    tags = relationship("Tag", back_populates="owner")
    two_factor = relationship("User2FA", back_populates="user", uselist=False)

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    filepath = Column(String)
    display_name = Column(String(255), nullable=True)  # User-friendly name for display
    prompt = Column(Text, nullable=True)
    ai_analysis_status = Column(String, default="pending")
    ai_analysis_result = Column(Text, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Blur hash placeholder for instant loading (Phase 3)
    blur_hash = Column(String(32), nullable=True)  # BlurHash string (e.g., "LEHV6nWB2yk8pyo0adR*.7kCMdnj")
    width = Column(Integer, nullable=True)  # Original image width
    height = Column(Integer, nullable=True)  # Original image height
    # Favorites and Trash (Phase 4)
    is_favorite = Column(Boolean, default=False, nullable=False)
    is_trashed = Column(Boolean, default=False, nullable=False)
    trashed_at = Column(DateTime(timezone=True), nullable=True)

    owner = relationship("User", back_populates="images")
    notes = relationship("Note", secondary="image_note_relations", back_populates="images")
    tags = relationship("Tag", secondary="image_tags", back_populates="images")
    albums = relationship("Album", secondary="album_images", back_populates="images")

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    html_content = Column(Text, nullable=True)  # Rich HTML content for rendering
    slug = Column(String, index=True, nullable=True)  # URL-friendly version of title
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_standalone = Column(Boolean, default=True, nullable=False)  # True if note created independently
    embedding = Column(Vector(768), nullable=True)  # Semantic search embedding (768-dim from nomic-embed-text)
    # Favorites, Trash, and Review Status (Notes Section)
    is_favorite = Column(Boolean, default=False, nullable=False, index=True)
    is_trashed = Column(Boolean, default=False, nullable=False, index=True)
    trashed_at = Column(DateTime(timezone=True), nullable=True)
    is_reviewed = Column(Boolean, default=False, nullable=False, index=True)  # For review queue feature
    # Brain Graph: Community clustering (Louvain/Leiden)
    community_id = Column(Integer, nullable=True, index=True)

    owner = relationship("User", back_populates="notes")
    images = relationship("Image", secondary="image_note_relations", back_populates="notes")
    tags = relationship("Tag", secondary="note_tags", back_populates="notes")
    collections = relationship("NoteCollection", secondary="note_collection_notes", back_populates="notes")

class ImageNoteRelation(Base):
    __tablename__ = "image_note_relations"

    image_id = Column(Integer, ForeignKey("images.id"), primary_key=True)
    note_id = Column(Integer, ForeignKey("notes.id"), primary_key=True)


class Tag(Base):
    """Tags for categorizing notes and images."""
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)  # Stored in lowercase
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", back_populates="tags")
    notes = relationship("Note", secondary="note_tags", back_populates="tags")
    images = relationship("Image", secondary="image_tags", back_populates="tags")


class NoteTag(Base):
    """Junction table for note-to-tag many-to-many relationship."""
    __tablename__ = "note_tags"

    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class ImageTag(Base):
    """Junction table for image-to-tag many-to-many relationship."""
    __tablename__ = "image_tags"

    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


# ============================================
# RAG (Retrieval-Augmented Generation) Models
# ============================================

class Conversation(Base):
    """Multi-turn conversation for RAG chat."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_archived = Column(Boolean, default=False)
    # metadata stored as JSONB - contains model settings, context preferences, etc.

    owner = relationship("User", backref="conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Individual message in a RAG conversation with retrieval metadata."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # retrieval_metadata: JSONB - stores retrieval config used (weights, thresholds, etc.)
    # generation_metadata: JSONB - stores model info, tokens used, timing
    confidence_score = Column(Float, nullable=True)  # AI confidence in response (0.0-1.0)

    conversation = relationship("Conversation", back_populates="messages")
    citations = relationship("MessageCitation", back_populates="message", cascade="all, delete-orphan")


class MessageCitation(Base):
    """Source citation for a RAG response - tracks which notes/images informed the answer."""
    __tablename__ = "message_citations"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False)
    source_type = Column(String(20), nullable=False)  # 'note', 'chunk', 'image'
    source_id = Column(Integer, nullable=False)  # ID of the note, chunk, or image
    citation_index = Column(Integer, nullable=False)  # [1], [2], [3]...
    relevance_score = Column(Float, nullable=False)  # Cosine similarity score (0.0-1.0)
    retrieval_method = Column(String(50), nullable=True)  # 'semantic', 'wikilink', 'fulltext', 'image_tag'
    used_content = Column(Text, nullable=True)  # The actual text snippet used
    # relationship_chain: JSONB - stores multi-hop path [{type, from, to}, ...]
    hop_count = Column(Integer, default=0)  # 0 = direct, 1 = one hop, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    message = relationship("ChatMessage", back_populates="citations")


class NoteChunk(Base):
    """Paragraph-level chunk of a note for precise RAG retrieval."""
    __tablename__ = "note_chunks"

    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # 0, 1, 2...
    chunk_type = Column(String(20), nullable=True)  # 'paragraph', 'heading', 'list', 'code'
    char_start = Column(Integer, nullable=False)  # Start position in original note
    char_end = Column(Integer, nullable=False)  # End position in original note
    embedding = Column(Vector(768), nullable=True)  # Chunk-level embedding
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    note = relationship("Note", backref="chunks")


class ImageChunk(Base):
    """Chunk of AI analysis content from an image for RAG retrieval."""
    __tablename__ = "image_chunks"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)  # Extracted from ai_analysis_result
    chunk_index = Column(Integer, nullable=False)  # 0, 1, 2...
    embedding = Column(Vector(768), nullable=True)  # Chunk-level embedding
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    image = relationship("Image", backref="chunks")


# ============================================
# Albums (Phase 5)
# ============================================

class Album(Base):
    """User-created album/collection of images."""
    __tablename__ = "albums"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cover_image_id = Column(Integer, ForeignKey("images.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", backref="albums")
    cover_image = relationship("Image", foreign_keys=[cover_image_id])
    images = relationship("Image", secondary="album_images", back_populates="albums")


class AlbumImage(Base):
    """Junction table for album-to-image many-to-many relationship."""
    __tablename__ = "album_images"

    album_id = Column(Integer, ForeignKey("albums.id", ondelete="CASCADE"), primary_key=True)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), primary_key=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    position = Column(Integer, default=0)  # For manual ordering within album


# ============================================
# Note Collections (Grouping Notes)
# ============================================

class NoteCollection(Base):
    """User-created collection/folder for grouping notes."""
    __tablename__ = "note_collections"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # Emoji or icon identifier
    color = Column(String(20), nullable=True)  # Hex color for visual distinction
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", backref="note_collections")
    notes = relationship("Note", secondary="note_collection_notes", back_populates="collections")


class NoteCollectionNote(Base):
    """Junction table for note-to-collection many-to-many relationship."""
    __tablename__ = "note_collection_notes"

    collection_id = Column(Integer, ForeignKey("note_collections.id", ondelete="CASCADE"), primary_key=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    position = Column(Integer, default=0)  # For manual ordering within collection


# ============================================
# Security Models (Phase 1: Settings)
# ============================================

class PasswordResetToken(Base):
    """Token for password reset functionality."""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="password_reset_tokens")


class User2FA(Base):
    """Two-factor authentication settings for a user."""
    __tablename__ = "user_2fa"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    secret_key = Column(String(32), nullable=False)  # TOTP secret
    is_enabled = Column(Boolean, default=False, nullable=False)
    backup_codes = Column(Text, nullable=True)  # JSON array of hashed backup codes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="two_factor")


class LoginAttempt(Base):
    """Track login attempts for security and account lockout."""
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    username = Column(String(255), nullable=True)  # Store even if user not found
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="login_attempts")


class UserSession(Base):
    """Active user sessions for session management."""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False, index=True)
    device_info = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    last_active = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="sessions")


class EmailChangeToken(Base):
    """Token for email change verification (Phase 2)."""
    __tablename__ = "email_change_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    new_email = Column(String(255), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="email_change_tokens")


class UserPreferences(Base):
    """User preferences for appearance and UI customization (Phase 3)."""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    theme = Column(String(20), default="dark", nullable=False)
    accent_color = Column(String(20), default="blue", nullable=False)
    ui_density = Column(String(20), default="comfortable", nullable=False)
    font_size = Column(String(20), default="medium", nullable=False)
    sidebar_collapsed = Column(Boolean, default=False, nullable=False)
    default_view = Column(String(50), default="notes", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", backref="preferences")


class DataExportJob(Base):
    """Data export job tracking (Phase 4)."""
    __tablename__ = "data_export_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(36), unique=True, nullable=False, index=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    file_path = Column(String(500), nullable=True)  # Path to generated ZIP
    file_size = Column(Integer, nullable=True)  # File size in bytes
    include_notes = Column(Boolean, default=True)
    include_images = Column(Boolean, default=True)
    include_tags = Column(Boolean, default=True)
    include_activity = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", backref="export_jobs")


class NotificationPreferences(Base):
    """User notification preferences (Phase 5: Settings)."""
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Email notifications
    email_security_alerts = Column(Boolean, default=True, nullable=False)
    email_weekly_digest = Column(Boolean, default=False, nullable=False)
    email_product_updates = Column(Boolean, default=True, nullable=False)

    # Push notifications (future)
    push_enabled = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", backref="notification_preferences")


# ============================================
# Mnemosyne Brain Models
# ============================================
# Import so Base.metadata.create_all picks them up
from features.mnemosyne_brain.models import (  # noqa: E402, F401
    BrainFile,
    BrainBuildLog,
    BrainConversation,
    BrainMessage,
)
