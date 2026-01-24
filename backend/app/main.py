from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Annotated
from pydantic import BaseModel
from datetime import timedelta
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import uuid
import requests
import base64
from pathlib import Path

# Core module imports (new fractal architecture)
from core import config
from core import database
from core import exceptions
from core.logging_config import setup_logging, get_logger
from core.error_handlers import register_exception_handlers
from core.auth import get_current_user, get_current_active_user, get_current_user_optional, create_access_token

# Feature routers (fractal architecture)
from features.auth.router import router as auth_router
from features.auth.router_account import router as auth_account_router
from features.settings.router import router as settings_router
from features.system.router import router as system_router
from features.notes.router import router as notes_router
from features.tags.router import router as tags_router, image_tag_router
from features.graph.router import router as graph_router
from features.graph.router_v2 import router as graph_router_v2
from features.images.router import router as images_router
from features.search.router import router as search_router
from features.buckets.router import router as buckets_router
from features.albums.router import router as albums_router
from features.collections.router import router as collections_router
from features.brain.router import router as brain_router

# Legacy imports (to be migrated to features)
import models
import crud
import schemas
import auth  # Keep for backward compatibility during migration

# Setup logging
setup_logging()
logger = get_logger(__name__)

logger.info("Starting AI Notes Notetaker API")

# Create database tables
try:
    models.Base.metadata.create_all(bind=database.engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.critical(f"Failed to create database tables: {str(e)}", exc_info=True)
    raise

# Simple migrations for new columns (without Alembic)
def run_simple_migrations():
    """Add new columns to existing tables if they don't exist."""
    with database.engine.connect() as conn:
        # Check if html_content column exists in notes table
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'notes' AND column_name = 'html_content'
        """))
        if not result.fetchone():
            logger.info("Adding html_content column to notes table...")
            conn.execute(text("ALTER TABLE notes ADD COLUMN html_content TEXT"))
            conn.commit()
            logger.info("html_content column added successfully")
        else:
            logger.debug("html_content column already exists")

try:
    run_simple_migrations()
    logger.info("Database migrations completed")
except Exception as e:
    logger.error(f"Migration failed (non-critical): {str(e)}", exc_info=True)

# Rate limiting configuration
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title=config.API_TITLE, version=config.API_VERSION)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Register exception handlers
register_exception_handlers(app)

# Include feature routers (fractal architecture)
app.include_router(auth_router)
app.include_router(auth_account_router)  # Phase 2: Account management endpoints
app.include_router(settings_router)  # Phase 3: User preferences endpoints
app.include_router(system_router)
app.include_router(notes_router)
app.include_router(tags_router)
app.include_router(image_tag_router)  # Image-tag association endpoints
app.include_router(graph_router)  # Knowledge graph and wikilink endpoints
app.include_router(graph_router_v2)  # Typed graph endpoints (Brain Graph - Phase 1)
app.include_router(images_router)  # Image upload and AI analysis endpoints
app.include_router(albums_router)  # Album CRUD and image management endpoints
app.include_router(collections_router)  # Note collection (groups) endpoints
app.include_router(search_router)  # Search endpoints (fulltext, semantic, embeddings)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency - use core's get_db
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create upload directory
try:
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    logger.info(f"Upload directory ready: {config.UPLOAD_DIR}")
except Exception as e:
    logger.error(f"Failed to create upload directory: {str(e)}", exc_info=True)
    raise

class ChatRequest(BaseModel):
    text: str

class AnalyzeRequest(BaseModel):
    prompt: str = "Describe this image in detail"

# System endpoints moved to features/system/router.py
# - GET / (root)
# - GET /health

# Auth endpoints moved to features/auth/router.py
# - POST /register
# - POST /login
# - GET /me

# Image Processing endpoints moved to features/images/router.py
# - POST /upload-image/
# - POST /retry-image/{image_id}
# - DELETE /images/{image_id}
# - GET /task-status/{task_id}
# - GET /images/
# - GET /image/{image_id}

@app.post("/chat-with-ai/", tags=["AI Integration"], deprecated=True)
@limiter.limit("30/minute")
async def chat_with_ai(
    request: Request,
    chat_request: ChatRequest,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    DEPRECATED: Use POST /rag/query or POST /rag/query/stream instead.

    This endpoint provides basic AI chat without citations or explainability.
    The new RAG endpoints offer:
    - Source citations with relevance scores
    - Multi-hop wikilink graph traversal
    - Semantic search across notes and images
    - Streaming responses with SSE
    - Conversation history management

    This endpoint will be removed in a future version.
    """
    logger.warning(f"DEPRECATED: /chat-with-ai/ called by user {current_user.username}. Use /rag/query instead.")

    # Validate chat request
    if not chat_request.text or len(chat_request.text.strip()) == 0:
        logger.warning("Chat request rejected: empty message")
        raise exceptions.ValidationException("Chat message cannot be empty")

    if len(chat_request.text) > 5000:
        logger.warning(f"Chat request rejected: message too long ({len(chat_request.text)} chars)")
        raise exceptions.ValidationException("Chat message too long (max 5000 characters)")

    try:
        # Get only the current user's notes for context
        notes = crud.get_notes_by_user(db, owner_id=current_user.id)
        context = "\n\n".join([f"Note: {note.title}\n{note.content[:200]}" for note in notes])
        logger.debug(f"Chat using context from {len(notes)} notes")

        full_prompt = f"Context (recent notes):\n{context}\n\nUser question: {chat_request.text}\n\nPlease answer based on the context if relevant, or provide general assistance."

        logger.debug("Sending chat request to Ollama")
        response = requests.post(
            f"{config.OLLAMA_HOST}/api/generate",
            json={
                "model": "llama3.2-vision:11b",
                "prompt": full_prompt,
                "stream": False
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("response", "I couldn't generate a response.")
            logger.info(f"Chat response generated successfully for user {current_user.username}")
            return {
                "response": ai_response,
                "deprecated": True,
                "migration_notice": "This endpoint is deprecated. Use POST /rag/query for citation-aware responses."
            }
        else:
            logger.error(f"Ollama API returned status {response.status_code}")
            raise exceptions.OllamaServiceException("AI service unavailable")

    except requests.exceptions.Timeout:
        logger.error("Ollama API timeout during chat")
        raise exceptions.OllamaServiceException("AI response timeout - please try again")
    except requests.exceptions.ConnectionError:
        logger.error("Connection error to Ollama service during chat")
        raise exceptions.OllamaServiceException("Could not connect to AI service")
    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during chat: {str(e)}", exc_info=True)
        raise exceptions.OllamaServiceException(f"Chat failed: {str(e)}")

# Notes CRUD endpoints moved to features/notes/router.py
# - GET /notes/
# - GET /notes/{note_id}
# - POST /notes/
# - PUT /notes/{note_id}
# - DELETE /notes/{note_id}


# ============================================
# Tag Management Endpoints
# ============================================
# Moved to features/tags/router.py:
# - GET /tags/
# - POST /tags/
# - POST /images/{image_id}/tags/{tag_name}
# - DELETE /images/{image_id}/tags/{tag_id}
#
# Note-specific tag endpoints are in features/notes/router.py:
# - POST /notes/{note_id}/tags/{tag_name}
# - DELETE /notes/{note_id}/tags/{tag_id}


# ============================================
# Wikilinks and Knowledge Graph Endpoints
# ============================================
# Moved to features/notes/router.py:
# - GET /notes-enhanced/
# - GET /notes/{note_id}/enhanced
# - GET /notes/{note_id}/graph
# - GET /graph/data
# - GET /notes/{note_id}/backlinks
# - GET /notes/orphaned/list
# - GET /notes/most-linked/


# Search endpoints moved to features/search/router.py
# - GET /search/fulltext
# - GET /search/notes
# - GET /search/images
# - GET /search/tags
# - GET /search/by-tag/{tag_name}
# - GET /search/semantic
# - GET /search/notes/{note_id}/similar
# - GET /search/notes/{note_id}/unlinked-mentions
# - GET /search/embeddings/coverage
# - POST /search/notes/{note_id}/regenerate-embedding

# ============================================================================
# PHASE 3: AI CLUSTERING & RAG ROUTERS
# ============================================================================

# Import RAG from feature module (migrated to fractal architecture)
from features.rag_chat import router as rag_router

# Register Buckets router (migrated to features)
app.include_router(
    buckets_router,
    tags=["Smart Buckets"]
)

app.include_router(
    rag_router,
    tags=["RAG Chat"]
)

app.include_router(
    brain_router,
    tags=["Brain Indexer"]
)

logger.info("Phase 3 routers registered: buckets (feature), rag_chat (feature)")
logger.info("Phase 4 routers registered: brain (semantic condensation)")
