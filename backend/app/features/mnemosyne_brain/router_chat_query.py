"""
Mnemosyne Brain Chat - Non-Streaming Query Endpoint.

Synchronous brain query with topic persistence.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.database import get_db
from core.auth import get_current_user
from core.model_service import get_effective_brain_model, get_effective_context_budget, get_provider_for_user
from core.models_registry import get_model_info
from core.llm.base import LLMMessage
from core.llm.cost_tracker import log_token_usage
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
    is_brain_stale,
    get_query_embedding,
    get_previous_topics,
    call_ollama_generate,
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
    stale = is_brain_stale(db, current_user.id)

    query = body.query
    query_embedding = get_query_embedding(query)

    # Compute dynamic context budget based on user's brain model
    context_budget = get_effective_context_budget(db, current_user.id)

    # Get pinned topics from user preferences
    prefs = db.query(models.UserPreferences).filter(
        models.UserPreferences.user_id == current_user.id
    ).first()
    pinned_topics = prefs.pinned_brain_topics if prefs else []

    # Extract previously loaded topics for conversation persistence
    prev_topics = get_previous_topics(db, current_user.id, body.conversation_id)

    # Select relevant topics (budget scales max_topics automatically)
    topic_scores = select_topics(
        db, current_user.id, query, query_embedding,
        token_budget=context_budget,
        pinned_topics=pinned_topics,
        previously_loaded_topics=prev_topics,
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

    # Assemble context (budget scales core/topic proportionally)
    context = assemble_context(
        db, current_user.id, topic_scores, conv_history,
        context_budget=context_budget,
        query=query,
    )

    # Build prompt
    prompt = query
    if conv_history:
        prompt = f"Conversation so far:\n{conv_history}\n\nUser: {query}"

    # Generate response (cloud-aware)
    provider, user_model, provider_name = get_provider_for_user(db, current_user.id, "brain")

    if provider_name != "ollama":
        # Cloud provider path
        messages = [
            LLMMessage(role="system", content=context.system_prompt),
            LLMMessage(role="user", content=prompt),
        ]
        try:
            llm_response = provider.generate(
                messages=messages, model=user_model, temperature=0.7, max_tokens=2048,
            )
            answer = llm_response.content
            log_token_usage(db, current_user.id, llm_response, "brain")
        except Exception as cloud_err:
            logger.warning(f"Cloud provider {provider_name} failed, falling back to Ollama: {cloud_err}")
            user_model = get_effective_brain_model(db, current_user.id)
            model_info = get_model_info(user_model)
            ctx_window = model_info.context_length if model_info else 4096
            answer = call_ollama_generate(prompt, context.system_prompt, model=user_model, context_window=ctx_window)
    else:
        model_info = get_model_info(user_model)
        ctx_window = model_info.context_length if model_info else 4096
        answer = call_ollama_generate(prompt, context.system_prompt, model=user_model, context_window=ctx_window)

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
        brain_is_stale=stale,
    )
