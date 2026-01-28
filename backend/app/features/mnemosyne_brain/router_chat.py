"""
Mnemosyne Brain Chat Router.

Endpoints for querying the brain and managing brain conversations.
"""

import json
import logging
from typing import List, Optional
from datetime import datetime

import requests
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.database import get_db
from core.auth import get_current_user
from core import config
import models

from features.mnemosyne_brain.models.brain_file import BrainFile
from features.mnemosyne_brain.models.brain_conversation import (
    BrainConversation,
    BrainMessage,
)
from features.mnemosyne_brain import schemas
from features.mnemosyne_brain.services.topic_selector import select_topics
from features.mnemosyne_brain.services.context_assembler import (
    assemble_context,
    format_conversation_history,
)

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/mnemosyne", tags=["mnemosyne-brain-chat"])

OLLAMA_HOST = config.OLLAMA_HOST


def _generate_conversation_title(query: str, max_length: int = 50) -> str:
    """Generate a conversation title from the query."""
    title = query.strip()
    prefixes = [
        "what do i know about ", "what do you know about ",
        "tell me about ", "can you tell me about ",
        "explain ", "describe ", "how does ", "what is ",
    ]
    lower = title.lower()
    for prefix in prefixes:
        if lower.startswith(prefix):
            title = title[len(prefix):]
            break
    title = title.strip().rstrip("?!.")
    if len(title) > max_length:
        cut = title[:max_length].rfind(" ")
        title = title[:cut] + "..." if cut > 10 else title[:max_length] + "..."
    return title.capitalize() if title else "Brain Chat"


def _check_brain_ready(db: Session, user_id: int):
    """Verify the brain has been built."""
    core_count = (
        db.query(BrainFile)
        .filter(
            BrainFile.owner_id == user_id,
            BrainFile.file_type == "core",
        )
        .count()
    )
    if core_count < 2:
        raise HTTPException(
            status_code=400,
            detail="Brain not built yet. Use POST /mnemosyne/build first.",
        )


def _get_query_embedding(query: str):
    """Generate query embedding, return None on failure."""
    try:
        from embeddings import generate_embedding
        return generate_embedding(query)
    except Exception:
        return None


def _call_ollama_generate(prompt: str, system_prompt: str) -> str:
    """Non-streaming Ollama call for brain."""
    model = getattr(config, "BRAIN_MODEL", "llama3.2:3b")
    temperature = getattr(config, "BRAIN_TEMPERATURE", 0.7)

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": 1024},
            },
            timeout=180,
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        logger.error(f"Ollama brain generate failed: {e}")
        return f"I'm sorry, I couldn't process that right now. ({e})"


def _call_ollama_stream(prompt: str, system_prompt: str):
    """Streaming Ollama call for brain."""
    model = getattr(config, "BRAIN_MODEL", "llama3.2:3b")
    temperature = getattr(config, "BRAIN_TEMPERATURE", 0.7)

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": True,
                "options": {"temperature": temperature, "num_predict": 1024},
            },
            stream=True,
            timeout=180,
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.error(f"Ollama brain stream failed: {e}")
        yield f"[ERROR: {e}]"


# ============================================
# Query Endpoints
# ============================================

@router.post("/query", response_model=schemas.BrainQueryResponse)
@limiter.limit("20/minute")
async def brain_query(
    request: Request,
    body: schemas.BrainQueryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Execute a brain-mode query (non-streaming)."""
    _check_brain_ready(db, current_user.id)

    query = body.query
    query_embedding = _get_query_embedding(query)

    # Select relevant topics
    topic_scores = select_topics(db, current_user.id, query, query_embedding)

    # Load conversation history
    conv_history = ""
    conversation = None
    if body.conversation_id:
        conversation = (
            db.query(BrainConversation)
            .filter(
                BrainConversation.id == body.conversation_id,
                BrainConversation.owner_id == current_user.id,
            )
            .first()
        )
        if conversation:
            messages = (
                db.query(BrainMessage)
                .filter(BrainMessage.conversation_id == conversation.id)
                .order_by(BrainMessage.created_at)
                .all()
            )
            conv_history = format_conversation_history(
                [{"role": m.role, "content": m.content} for m in messages]
            )

    # Assemble context
    context = assemble_context(db, current_user.id, topic_scores, conv_history)

    # Build prompt
    prompt = query
    if conv_history:
        prompt = f"Conversation so far:\n{conv_history}\n\nUser: {query}"

    # Generate response
    answer = _call_ollama_generate(prompt, context.system_prompt)

    # Save to conversation
    conversation_id = body.conversation_id
    message_id = None

    try:
        if not conversation and body.auto_create_conversation:
            title = _generate_conversation_title(query)
            conversation = BrainConversation(
                owner_id=current_user.id,
                title=title,
                brain_files_used=context.brain_files_used,
            )
            db.add(conversation)
            db.flush()
            conversation_id = conversation.id

        if conversation:
            # Save user message
            user_msg = BrainMessage(
                conversation_id=conversation.id,
                role="user",
                content=query,
            )
            db.add(user_msg)

            # Save assistant message
            assistant_msg = BrainMessage(
                conversation_id=conversation.id,
                role="assistant",
                content=answer,
                brain_files_loaded=context.brain_files_used,
                topics_matched=context.topics_matched,
            )
            db.add(assistant_msg)
            db.flush()
            message_id = assistant_msg.id

            conversation.brain_files_used = context.brain_files_used
            conversation.updated_at = datetime.utcnow()
            db.commit()
    except Exception as e:
        logger.error(f"Failed to save brain conversation: {e}")
        db.rollback()

    return schemas.BrainQueryResponse(
        answer=answer,
        brain_files_used=context.brain_files_used,
        topics_matched=context.topics_matched,
        conversation_id=conversation_id,
        message_id=message_id,
    )


@router.post("/query/stream")
@limiter.limit("20/minute")
async def brain_query_stream(
    request: Request,
    body: schemas.BrainQueryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Execute a streaming brain-mode query (SSE)."""
    _check_brain_ready(db, current_user.id)

    query = body.query
    user_id = current_user.id
    query_embedding = _get_query_embedding(query)

    # Handle conversation
    conversation = None
    conversation_id = body.conversation_id
    if body.conversation_id:
        conversation = (
            db.query(BrainConversation)
            .filter(
                BrainConversation.id == body.conversation_id,
                BrainConversation.owner_id == user_id,
            )
            .first()
        )
        if not conversation:
            conversation_id = None

    if not conversation and body.auto_create_conversation:
        title = _generate_conversation_title(query)
        conversation = BrainConversation(owner_id=user_id, title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        conversation_id = conversation.id

    async def generate_stream():
        try:
            topic_scores = select_topics(db, user_id, query, query_embedding)
            context = assemble_context(db, user_id, topic_scores)

            prompt = query
            if conversation:
                messages = (
                    db.query(BrainMessage)
                    .filter(BrainMessage.conversation_id == conversation.id)
                    .order_by(BrainMessage.created_at)
                    .all()
                )
                if messages:
                    history = format_conversation_history(
                        [{"role": m.role, "content": m.content} for m in messages]
                    )
                    prompt = f"Conversation so far:\n{history}\n\nUser: {query}"

            # Stream tokens
            full_response = ""
            for token in _call_ollama_stream(prompt, context.system_prompt):
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # Send brain metadata
            yield f"data: {json.dumps({'type': 'brain_meta', 'brain_files_used': context.brain_files_used, 'topics_matched': context.topics_matched})}\n\n"

            # Send metadata with conversation ID
            yield f"data: {json.dumps({'type': 'metadata', 'metadata': {'conversation_id': conversation_id}})}\n\n"

            # Save to conversation
            if conversation:
                try:
                    user_msg = BrainMessage(
                        conversation_id=conversation.id,
                        role="user",
                        content=query,
                    )
                    db.add(user_msg)

                    assistant_msg = BrainMessage(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=full_response,
                        brain_files_loaded=context.brain_files_used,
                        topics_matched=context.topics_matched,
                    )
                    db.add(assistant_msg)

                    conversation.brain_files_used = context.brain_files_used
                    conversation.updated_at = datetime.utcnow()
                    db.commit()
                except Exception as e:
                    logger.error(f"Failed to save brain stream conversation: {e}")
                    db.rollback()

            # Queue memory evolution
            try:
                if conversation:
                    from features.mnemosyne_brain.tasks import evolve_memory_task
                    evolve_memory_task.delay(user_id, conversation.id)
            except Exception as e:
                logger.warning(f"Failed to queue memory evolution: {e}")

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.exception(f"Brain stream failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================
# Conversation CRUD
# ============================================

@router.post("/conversations", response_model=schemas.BrainConversationResponse)
@limiter.limit("20/minute")
async def create_conversation(
    request: Request,
    body: schemas.BrainConversationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create a new brain conversation."""
    conversation = BrainConversation(
        owner_id=current_user.id,
        title=body.title or "New Brain Chat",
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/conversations", response_model=List[schemas.BrainConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = Query(default=50, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List brain conversations."""
    convos = (
        db.query(BrainConversation)
        .filter(
            BrainConversation.owner_id == current_user.id,
            BrainConversation.is_archived == False,  # noqa: E712
        )
        .order_by(BrainConversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return convos


@router.get(
    "/conversations/{conversation_id}",
    response_model=schemas.BrainConversationWithMessages,
)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get a brain conversation with messages."""
    conversation = (
        db.query(BrainConversation)
        .filter(
            BrainConversation.id == conversation_id,
            BrainConversation.owner_id == current_user.id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.put(
    "/conversations/{conversation_id}",
    response_model=schemas.BrainConversationResponse,
)
async def update_conversation(
    conversation_id: int,
    body: schemas.BrainConversationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update a brain conversation."""
    conversation = (
        db.query(BrainConversation)
        .filter(
            BrainConversation.id == conversation_id,
            BrainConversation.owner_id == current_user.id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if body.title is not None:
        conversation.title = body.title
    if body.is_archived is not None:
        conversation.is_archived = body.is_archived

    db.commit()
    db.refresh(conversation)
    return conversation


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a brain conversation."""
    conversation = (
        db.query(BrainConversation)
        .filter(
            BrainConversation.id == conversation_id,
            BrainConversation.owner_id == current_user.id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.delete(conversation)
    db.commit()
    return {"detail": "Conversation deleted"}
