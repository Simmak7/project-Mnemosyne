"""
Mnemosyne Brain Chat - Query Endpoints.

Streaming and non-streaming brain query endpoints.
"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.database import get_db
from core.auth import get_current_user
from core.model_service import get_effective_brain_model
import models

from features.mnemosyne_brain.models.brain_conversation import (
    BrainConversation,
    BrainMessage,
)
from features.mnemosyne_brain import schemas
from features.mnemosyne_brain.services.topic_selector import select_topics
from features.mnemosyne_brain.services.context_assembler import (
    assemble_context,
    format_conversation_history_tiered,
)
from features.mnemosyne_brain.services.conversation_summarizer import (
    should_update_summary,
    increment_message_counter,
)
from features.mnemosyne_brain.router_chat_helpers import (
    generate_conversation_title,
    check_brain_ready,
    get_query_embedding,
    call_ollama_generate,
    call_ollama_stream,
)

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/mnemosyne", tags=["mnemosyne-brain-chat"])


@router.post("/query", response_model=schemas.BrainQueryResponse)
@limiter.limit("20/minute")
async def brain_query(
    request: Request,
    body: schemas.BrainQueryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Execute a brain-mode query (non-streaming)."""
    check_brain_ready(db, current_user.id)

    query = body.query
    query_embedding = get_query_embedding(query)

    # Get pinned topics from user preferences
    prefs = db.query(models.UserPreferences).filter(
        models.UserPreferences.user_id == current_user.id
    ).first()
    pinned_topics = prefs.pinned_brain_topics if prefs else []

    # Select relevant topics
    topic_scores = select_topics(
        db, current_user.id, query, query_embedding,
        pinned_topics=pinned_topics,
    )

    # Load conversation history with tiered memory
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
                .limit(20)
                .all()
            )
            conv_history = format_conversation_history_tiered(
                [{"role": m.role, "content": m.content} for m in messages],
                conversation_summary=conversation.conversation_summary,
            )

    # Assemble context
    context = assemble_context(db, current_user.id, topic_scores, conv_history)

    # Build prompt
    prompt = query
    if conv_history:
        prompt = f"Conversation so far:\n{conv_history}\n\nUser: {query}"

    # Get user's preferred model
    user_model = get_effective_brain_model(db, current_user.id)

    # Generate response
    answer = call_ollama_generate(prompt, context.system_prompt, model=user_model)

    # Save to conversation
    conversation_id = body.conversation_id
    message_id = None

    try:
        if not conversation and body.auto_create_conversation:
            title = generate_conversation_title(query)
            conversation = BrainConversation(
                owner_id=current_user.id,
                title=title,
                brain_files_used=context.brain_files_used,
            )
            db.add(conversation)
            db.flush()
            conversation_id = conversation.id

        if conversation:
            user_msg = BrainMessage(
                conversation_id=conversation.id,
                role="user",
                content=query,
            )
            db.add(user_msg)

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

            increment_message_counter(db, conversation)
            db.commit()

            if should_update_summary(conversation):
                try:
                    from features.mnemosyne_brain.tasks import update_conversation_summary_task
                    update_conversation_summary_task.delay(conversation.id)
                except Exception as e:
                    logger.warning(f"Failed to queue summary update: {e}")
    except Exception as e:
        logger.error(f"Failed to save brain conversation: {e}")
        db.rollback()

    return schemas.BrainQueryResponse(
        answer=answer,
        brain_files_used=context.brain_files_used,
        topics_matched=context.topics_matched,
        conversation_id=conversation_id,
        message_id=message_id,
        model_used=user_model,
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
    check_brain_ready(db, current_user.id)

    query = body.query
    user_id = current_user.id
    query_embedding = get_query_embedding(query)

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
        title = generate_conversation_title(query)
        conversation = BrainConversation(owner_id=user_id, title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        conversation_id = conversation.id

    # Get pinned topics
    prefs = db.query(models.UserPreferences).filter(
        models.UserPreferences.user_id == user_id
    ).first()
    pinned_topics_list = prefs.pinned_brain_topics if prefs else []

    async def generate_stream():
        try:
            topic_scores = select_topics(
                db, user_id, query, query_embedding,
                pinned_topics=pinned_topics_list,
            )
            context = assemble_context(db, user_id, topic_scores)

            prompt = query
            if conversation:
                messages = (
                    db.query(BrainMessage)
                    .filter(BrainMessage.conversation_id == conversation.id)
                    .order_by(BrainMessage.created_at)
                    .limit(20)
                    .all()
                )
                if messages:
                    history = format_conversation_history_tiered(
                        [{"role": m.role, "content": m.content} for m in messages],
                        conversation_summary=conversation.conversation_summary,
                    )
                    prompt = f"Conversation so far:\n{history}\n\nUser: {query}"

            user_model = get_effective_brain_model(db, user_id)

            full_response = ""
            for token in call_ollama_stream(prompt, context.system_prompt, model=user_model):
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            yield f"data: {json.dumps({'type': 'brain_meta', 'brain_files_used': context.brain_files_used, 'topics_matched': context.topics_matched, 'model_used': user_model})}\n\n"
            yield f"data: {json.dumps({'type': 'metadata', 'metadata': {'conversation_id': conversation_id, 'model_used': user_model}})}\n\n"

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

                    increment_message_counter(db, conversation)
                    db.commit()

                    if should_update_summary(conversation):
                        try:
                            from features.mnemosyne_brain.tasks import update_conversation_summary_task
                            update_conversation_summary_task.delay(conversation.id)
                        except Exception as e:
                            logger.warning(f"Failed to queue summary update: {e}")
                except Exception as e:
                    logger.error(f"Failed to save brain stream conversation: {e}")
                    db.rollback()

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
