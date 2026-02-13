"""
Conversation management endpoints for RAG Chat.

Provides CRUD operations for conversations and message history.
"""

import logging
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.database import get_db
from core.auth import get_current_user
from models import User, Note, Image

from features.rag_chat.models import Conversation, ChatMessage, MessageCitation
from features.rag_chat import schemas
from features.nexus.models import NexusCitation
from features.nexus.schemas import NexusRichCitation
from features.nexus.services.context_helpers import (
    build_connections,
    build_exploration_suggestions,
)

logger = logging.getLogger(__name__)


def _resolve_title(db: Session, source_type: str, source_id: int) -> str:
    """Resolve a human-readable title for a citation source."""
    if source_type == "note":
        note = db.query(Note).filter(Note.id == source_id).first()
        return note.title if note else "Deleted Note"
    elif source_type == "image":
        image = db.query(Image).filter(Image.id == source_id).first()
        return image.filename if image else "Deleted Image"
    return "Unknown"

router = APIRouter(prefix="/rag", tags=["rag"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/conversations", response_model=schemas.ConversationResponse)
@limiter.limit("20/minute")
async def create_conversation(
    request: Request,
    data: schemas.ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new RAG conversation.

    **Rate limit:** 20 requests/minute
    """
    conversation = Conversation(
        owner_id=current_user.id,
        title=data.title or "New Conversation"
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return schemas.ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        summary=conversation.summary,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=0
    )


@router.get("/conversations", response_model=List[schemas.ConversationResponse])
@limiter.limit("30/minute")
async def list_conversations(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List user's RAG conversations.

    **Rate limit:** 30 requests/minute
    """
    conversations = db.query(Conversation).filter(
        Conversation.owner_id == current_user.id
    ).order_by(
        Conversation.updated_at.desc().nullsfirst()
    ).offset(skip).limit(limit).all()

    results = []
    for conv in conversations:
        msg_count = db.query(func.count(ChatMessage.id)).filter(
            ChatMessage.conversation_id == conv.id
        ).scalar() or 0

        results.append(schemas.ConversationResponse(
            id=conv.id,
            title=conv.title,
            summary=conv.summary,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=msg_count
        ))

    return results


@router.get("/conversations/{conversation_id}", response_model=schemas.ConversationWithMessages)
@limiter.limit("30/minute")
async def get_conversation(
    request: Request,
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a conversation with full message history and citations.

    **Rate limit:** 30 requests/minute
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.owner_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(404, "Conversation not found")

    messages = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_id
    ).order_by(ChatMessage.created_at).all()

    message_responses = []
    for msg in messages:
        citations = []
        if msg.role == "assistant":
            nexus_cits = db.query(NexusCitation).filter(
                NexusCitation.message_id == msg.id
            ).all()

            if nexus_cits:
                for c in nexus_cits:
                    title = _resolve_title(db, c.source_type, c.source_id)
                    citations.append(schemas.CitationSource(
                        index=c.citation_index,
                        source_type=c.source_type,
                        source_id=c.source_id,
                        title=title,
                        content_preview=c.community_name or "",
                        relevance_score=c.relevance_score or 0,
                        retrieval_method=c.retrieval_method or "nexus",
                        hop_count=0,
                        relationship_chain=None,
                        origin_type=c.origin_type,
                        artifact_id=c.artifact_id,
                        artifact_url=c.artifact_url,
                        community_name=c.community_name,
                        community_id=c.community_id,
                        tags=c.tags or [],
                        direct_wikilinks=c.direct_wikilinks or [],
                        path_to_other_results=c.path_to_other_results or [],
                        note_url=c.note_url,
                        graph_url=c.graph_url,
                    ))
            else:
                db_citations = db.query(MessageCitation).filter(
                    MessageCitation.message_id == msg.id
                ).all()
                for c in db_citations:
                    title = _resolve_title(db, c.source_type, c.source_id)
                    citations.append(schemas.CitationSource(
                        index=c.citation_index,
                        source_type=c.source_type,
                        source_id=c.source_id,
                        title=title,
                        content_preview="",
                        relevance_score=c.relevance_score,
                        retrieval_method=c.retrieval_method,
                        hop_count=c.hop_count or 0,
                        relationship_chain=None,
                    ))

        message_responses.append(schemas.MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at,
            confidence_score=msg.confidence_score,
            retrieval_metadata=None,
            citations=citations
        ))

    # Rebuild NEXUS insights from the last assistant message's citations
    connection_insights = []
    exploration_suggestions = []
    last_assistant = next(
        (m for m in reversed(message_responses)
         if m.role == "assistant" and any(c.origin_type is not None or c.community_id is not None for c in m.citations)),
        None,
    )
    if last_assistant:
        rich_cits = [
            NexusRichCitation(
                index=c.index, source_type=c.source_type, source_id=c.source_id,
                title=c.title, content_preview=c.content_preview,
                relevance_score=c.relevance_score, retrieval_method=c.retrieval_method,
                origin_type=c.origin_type, artifact_id=c.artifact_id,
                community_name=c.community_name, community_id=c.community_id,
                tags=c.tags, direct_wikilinks=c.direct_wikilinks,
                path_to_other_results=c.path_to_other_results,
                note_url=c.note_url, graph_url=c.graph_url, artifact_url=c.artifact_url,
            )
            for c in last_assistant.citations
        ]
        _, conn_objects = build_connections(rich_cits, max_connection_chars=2000)
        connection_insights = [ci.model_dump() for ci in conn_objects]
        sugg_objects = build_exploration_suggestions(rich_cits)
        exploration_suggestions = [s.model_dump() for s in sugg_objects]

    return schemas.ConversationWithMessages(
        id=conversation.id,
        title=conversation.title,
        summary=conversation.summary,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=message_responses,
        connection_insights=connection_insights,
        exploration_suggestions=exploration_suggestions,
    )


@router.put("/conversations/{conversation_id}", response_model=schemas.ConversationResponse)
@limiter.limit("20/minute")
async def update_conversation(
    request: Request,
    conversation_id: int,
    data: schemas.ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a conversation's title or summary.

    **Rate limit:** 20 requests/minute
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.owner_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(404, "Conversation not found")

    if data.title is not None:
        conversation.title = data.title
    if data.summary is not None:
        conversation.summary = data.summary

    conversation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(conversation)

    msg_count = db.query(func.count(ChatMessage.id)).filter(
        ChatMessage.conversation_id == conversation.id
    ).scalar() or 0

    return schemas.ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        summary=conversation.summary,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=msg_count
    )


@router.delete("/conversations/{conversation_id}")
@limiter.limit("20/minute")
async def delete_conversation(
    request: Request,
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a conversation and all its messages.

    **Rate limit:** 20 requests/minute
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.owner_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(404, "Conversation not found")

    db.delete(conversation)
    db.commit()

    return {"message": "Conversation deleted", "id": conversation_id}
