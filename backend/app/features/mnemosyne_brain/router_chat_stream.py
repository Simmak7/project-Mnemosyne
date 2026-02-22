"""
Mnemosyne Brain Chat - Streaming Query Endpoint.

SSE streaming brain query with topic persistence.
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
from core.model_service import get_effective_brain_model, get_effective_context_budget, get_provider_for_user
from core.models_registry import get_model_info
from core.llm.base import LLMMessage
from core.llm.cost_tracker import log_stream_usage
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
    call_ollama_stream,
)

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/mnemosyne", tags=["mnemosyne-brain-chat"])


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
    stale = is_brain_stale(db, current_user.id)

    query = body.query
    user_id = current_user.id
    query_embedding = get_query_embedding(query)

    # Compute dynamic context budget based on user's brain model
    context_budget = get_effective_context_budget(db, user_id)

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

    # Extract previously loaded topics before stream starts
    prev_topics_stream = get_previous_topics(db, user_id, conversation_id)

    async def generate_stream():
        try:
            topic_scores = select_topics(
                db, user_id, query, query_embedding,
                token_budget=context_budget,
                pinned_topics=pinned_topics_list,
                previously_loaded_topics=prev_topics_stream,
            )
            context = assemble_context(
                db, user_id, topic_scores,
                context_budget=context_budget,
                query=query,
            )

            # Emit topics-matched count so frontend can show indicator
            yield f"data: {json.dumps({'type': 'sources_found', 'sources_found': len(context.topics_matched)})}\n\n"

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

            provider, user_model, provider_name = get_provider_for_user(db, user_id, "brain")

            full_response = ""
            stream_input_tokens = 0
            stream_output_tokens = 0
            had_error = False

            if provider_name != "ollama":
                messages = [
                    LLMMessage(role="system", content=context.system_prompt),
                    LLMMessage(role="user", content=prompt),
                ]
                try:
                    for chunk in provider.stream(
                        messages=messages, model=user_model, temperature=0.7, max_tokens=2048,
                    ):
                        if chunk.is_error:
                            had_error = True
                            yield f"data: {json.dumps({'type': 'error', 'content': chunk.content, 'error_type': chunk.error_type})}\n\n"
                            break
                        if chunk.content:
                            full_response += chunk.content
                            yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
                        if chunk.done:
                            stream_input_tokens = chunk.input_tokens
                            stream_output_tokens = chunk.output_tokens
                            break
                    if not had_error:
                        from core.llm.base import ProviderType as PT
                        ptype = {"anthropic": PT.ANTHROPIC, "openai": PT.OPENAI, "custom": PT.CUSTOM}.get(provider_name, PT.OLLAMA)
                        log_stream_usage(db, user_id, ptype, user_model, stream_input_tokens, stream_output_tokens, "brain")
                except Exception as cloud_err:
                    logger.warning(f"Cloud stream failed, falling back to Ollama: {cloud_err}")
                    user_model = get_effective_brain_model(db, user_id)
                    model_info = get_model_info(user_model)
                    ctx_window = model_info.context_length if model_info else 4096
                    for chunk in call_ollama_stream(prompt, context.system_prompt, model=user_model, context_window=ctx_window):
                        if chunk.is_error:
                            had_error = True
                            yield f"data: {json.dumps({'type': 'error', 'content': chunk.content, 'error_type': chunk.error_type})}\n\n"
                            break
                        if chunk.content:
                            full_response += chunk.content
                            yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
                        if chunk.done:
                            break
            else:
                model_info = get_model_info(user_model)
                ctx_window = model_info.context_length if model_info else 4096
                for chunk in call_ollama_stream(prompt, context.system_prompt, model=user_model, context_window=ctx_window):
                    if chunk.is_error:
                        had_error = True
                        yield f"data: {json.dumps({'type': 'error', 'content': chunk.content, 'error_type': chunk.error_type})}\n\n"
                        break
                    if chunk.content:
                        full_response += chunk.content
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
                    if chunk.done:
                        break

            yield f"data: {json.dumps({'type': 'brain_meta', 'brain_files_used': context.brain_files_used, 'topics_matched': context.topics_matched, 'model_used': user_model, 'brain_is_stale': stale})}\n\n"
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
