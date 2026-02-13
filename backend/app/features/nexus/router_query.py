"""
NEXUS Query Endpoints

POST /nexus/query       - Execute NEXUS query (blocking)
POST /nexus/query/stream - Execute NEXUS query (SSE streaming)
"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.database import get_db
from core.model_service import get_effective_nexus_model
from core import config
from core.auth import get_current_user
from models import User
from features.rag_chat.models import Conversation, ChatMessage
from features.rag_chat.services.prompts import extract_confidence_signals
from features.rag_chat.services.context_builder import extract_citations_from_response
from features.rag_chat.services.title_generator import generate_conversation_title

from features.nexus import schemas
from features.nexus.services.query_router import route_query
from features.nexus.services.response_generator import (
    generate_nexus_response,
    stream_nexus_response,
)
from features.nexus.services.pipeline import (
    run_nexus_pipeline,
    get_conversation_history,
    save_nexus_citations,
    persist_conversation,
    type_breakdown,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nexus", tags=["nexus"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/query", response_model=schemas.NexusQueryResponse)
@limiter.limit("20/minute")
async def nexus_query(
    request: Request,
    body: schemas.NexusQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute a NEXUS query with rich citations and graph insights."""
    query = body.query
    owner_id = current_user.id
    logger.info(f"NEXUS query: user={owner_id}, q='{query[:50]}...'")

    try:
        # Stage 1: Route
        mode_str = body.mode.value if body.mode != schemas.QueryMode.AUTO else None
        route = route_query(query, mode_str)

        # Stage 2: Retrieve + Expand
        ranked_results, context, strategies = run_nexus_pipeline(
            db, query, owner_id, body, route
        )

        # Stage 3: Generate
        conversation_history = get_conversation_history(
            db, body.conversation_id, owner_id
        )
        user_model = get_effective_nexus_model(db, owner_id)
        fallback = config.RAG_MODEL if user_model != config.RAG_MODEL else None
        result = generate_nexus_response(
            query, context, user_model, conversation_history,
            fallback_model=fallback,
        )

        metadata = schemas.NexusRetrievalMetadata(
            mode=route.mode,
            mode_auto_detected=route.auto_detected,
            intent=route.intent,
            strategies_used=strategies,
            total_sources_searched=len(ranked_results),
            sources_used=len(context.rich_citations),
            avg_relevance_score=round(
                sum(c.relevance_score for c in context.rich_citations)
                / max(len(context.rich_citations), 1), 3
            ),
            source_type_breakdown=type_breakdown(context.rich_citations),
            context_tokens_approx=context.total_tokens_approx,
            context_truncated=context.truncated,
        )

        # Conversation persistence
        message_id, conversation_id = persist_conversation(
            db, body, owner_id, query, result["answer"],
            context.rich_citations, result["confidence"]
        )

        return schemas.NexusQueryResponse(
            answer=result["answer"],
            rich_citations=context.rich_citations,
            used_citation_indices=result["used_indices"],
            connection_insights=context.connection_insights,
            exploration_suggestions=context.exploration_suggestions,
            retrieval_metadata=metadata,
            confidence_score=result["confidence"]["confidence_score"],
            confidence_level=result["confidence"]["confidence_level"],
            conversation_id=conversation_id,
            message_id=message_id,
            model_used=user_model,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"NEXUS query failed: {e}")
        raise HTTPException(500, f"NEXUS query failed: {str(e)}")


@router.post("/query/stream")
@limiter.limit("20/minute")
async def nexus_query_stream(
    request: Request,
    body: schemas.NexusQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute a streaming NEXUS query with SSE."""
    query = body.query
    owner_id = current_user.id

    # Prepare conversation before streaming
    conversation_id = body.conversation_id
    conversation = None
    if body.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == body.conversation_id,
            Conversation.owner_id == owner_id,
        ).first()
        if not conversation:
            conversation_id = None

    if not conversation and body.auto_create_conversation:
        title = generate_conversation_title(query)
        conversation = Conversation(owner_id=owner_id, title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        conversation_id = conversation.id

    async def generate_stream():
        try:
            mode_str = body.mode.value if body.mode != schemas.QueryMode.AUTO else None
            route = route_query(query, mode_str)

            ranked_results, context, strategies = run_nexus_pipeline(
                db, query, owner_id, body, route
            )

            conversation_history = get_conversation_history(
                db, conversation_id, owner_id
            )
            user_model = get_effective_nexus_model(db, owner_id)
            fallback = config.RAG_MODEL if user_model != config.RAG_MODEL else None
            full_response = ""

            for token in stream_nexus_response(
                query, context, user_model, conversation_history,
                fallback_model=fallback,
            ):
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            confidence = extract_confidence_signals(full_response)
            used_indices = extract_citations_from_response(
                full_response,
                [type('S', (), {'index': c.index})() for c in context.rich_citations],
            )

            citations_data = [c.model_dump() for c in context.rich_citations]
            yield f"data: {json.dumps({'type': 'citations', 'citations': citations_data, 'used_indices': used_indices})}\n\n"

            if context.connection_insights:
                connections_data = [c.model_dump() for c in context.connection_insights]
                yield f"data: {json.dumps({'type': 'connections', 'connections': connections_data})}\n\n"

            if context.exploration_suggestions:
                suggestions_data = [s.model_dump() for s in context.exploration_suggestions]
                yield f"data: {json.dumps({'type': 'suggestions', 'suggestions': suggestions_data})}\n\n"

            message_id = None
            if conversation:
                try:
                    user_msg = ChatMessage(
                        conversation_id=conversation.id, role="user", content=query
                    )
                    db.add(user_msg)
                    db.flush()

                    assistant_msg = ChatMessage(
                        conversation_id=conversation.id, role="assistant",
                        content=full_response,
                        confidence_score=confidence["confidence_score"],
                    )
                    db.add(assistant_msg)
                    db.flush()
                    message_id = assistant_msg.id

                    save_nexus_citations(db, message_id, context.rich_citations)
                    conversation.updated_at = datetime.utcnow()
                    db.commit()
                except Exception as e:
                    logger.error(f"Failed to save NEXUS conversation: {e}")
                    db.rollback()

            meta = {
                "mode": route.mode,
                "mode_auto_detected": route.auto_detected,
                "intent": route.intent,
                "strategies_used": strategies,
                "sources_used": len(context.rich_citations),
                "confidence_score": confidence["confidence_score"],
                "confidence_level": confidence["confidence_level"],
                "conversation_id": conversation_id,
                "message_id": message_id,
                "model_used": user_model,
            }
            yield f"data: {json.dumps({'type': 'metadata', 'metadata': meta})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.exception(f"NEXUS streaming failed: {e}")
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
