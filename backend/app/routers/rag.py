"""
RAG (Retrieval-Augmented Generation) API endpoints.

Provides citation-aware, explainable AI chat with:
- Multi-source retrieval (semantic, wikilink graph, full-text, images)
- Source citation tracking with relevance scores
- Multi-hop relationship chain explanation
- Hybrid streaming responses (SSE)
"""

import json
import logging
import requests
from typing import List, Optional, AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from slowapi import Limiter
from slowapi.util import get_remote_address

from core import config
from core.database import get_db
from models import User, Note, Image, Conversation, ChatMessage, MessageCitation
from core.auth import get_current_user
from embeddings import generate_embedding
import schemas

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

from rag import (
    # Retrieval
    RetrievalConfig,
    combined_semantic_search,
    semantic_search_notes,
    semantic_search_chunks,
    fulltext_search_notes,
    # Image retrieval
    combined_image_retrieval,
    # Graph retrieval
    GraphTraversalConfig,
    graph_traversal,
    # Ranking
    RankingConfig,
    merge_and_rank,
    get_retrieval_summary,
    # Context building
    ContextConfig,
    build_context,
    sources_to_citation_list,
    extract_citations_from_response,
    # Prompts
    RAGPromptConfig,
    RAG_SYSTEM_PROMPT,
    RAG_SYSTEM_PROMPT_CONCISE,
    format_user_message_with_context,
    format_no_context_message,
    extract_confidence_signals,
    validate_citations,
    detect_query_type,
    get_query_specific_instructions,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])

# Ollama configuration for text generation
OLLAMA_HOST = config.OLLAMA_HOST
RAG_MODEL = config.RAG_MODEL
RAG_TIMEOUT = config.RAG_TIMEOUT
RAG_TEMPERATURE = config.RAG_TEMPERATURE


def call_ollama_generate(
    prompt: str,
    system_prompt: str,
    model: str = RAG_MODEL,
    timeout: int = RAG_TIMEOUT
) -> str:
    """
    Call Ollama API for text generation.

    Args:
        prompt: User prompt with context
        system_prompt: System instructions
        model: Model name to use
        timeout: Request timeout

    Returns:
        Generated response text

    Raises:
        HTTPException: If Ollama call fails
    """
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "think": False,
                "options": {
                    "temperature": RAG_TEMPERATURE,
                    "num_predict": 1024,  # Max tokens to generate
                }
            },
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    except requests.exceptions.Timeout:
        logger.error(f"Ollama timeout after {timeout}s")
        raise HTTPException(503, "AI service timeout. Please try again.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama request failed: {e}")
        raise HTTPException(503, "AI service unavailable. Please try again later.")


def call_ollama_stream(
    prompt: str,
    system_prompt: str,
    model: str = RAG_MODEL
) -> AsyncGenerator[str, None]:
    """
    Stream tokens from Ollama API.

    Args:
        prompt: User prompt with context
        system_prompt: System instructions
        model: Model name to use

    Yields:
        Token strings as they're generated
    """
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": True,
                "think": False,
                "options": {
                    "temperature": RAG_TEMPERATURE,
                    "num_predict": 1024,
                }
            },
            stream=True,
            timeout=RAG_TIMEOUT
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

    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama streaming failed: {e}")
        yield f"[ERROR: AI service unavailable]"


# ============================================
# Stateless RAG Query Endpoints
# ============================================

@router.post("/query", response_model=schemas.RAGQueryResponse)
@limiter.limit("20/minute")
async def rag_query(
    request: Request,
    body: schemas.RAGQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute a RAG query with citation tracking.

    This endpoint:
    1. Retrieves relevant sources from notes, chunks, images, and wikilink graph
    2. Ranks and merges results using Reciprocal Rank Fusion
    3. Builds context with citation markers
    4. Generates response using LLM with strict citation requirements
    5. Returns response with source citations and explainability metadata

    **Rate limit:** 20 requests/minute

    **Example:**
    ```json
    POST /rag/query
    {
        "query": "What are the key concepts in machine learning?",
        "max_sources": 10,
        "include_images": true,
        "include_graph": true
    }
    ```
    """
    query = body.query
    logger.info(
        f"RAG query: user={current_user.id}, query='{query[:50]}...', "
        f"max_sources={body.max_sources}"
    )

    # Generate query embedding
    query_embedding = generate_embedding(query)
    if not query_embedding:
        raise HTTPException(
            status_code=503,
            detail="Failed to generate query embedding. AI service may be unavailable."
        )

    # Configure retrieval
    retrieval_config = RetrievalConfig(
        min_similarity=body.min_similarity,
        max_results=body.max_sources,
        include_notes=True,
        include_chunks=True,
        include_images=body.include_images
    )

    # Perform multi-source retrieval
    try:
        # Semantic search on notes and chunks
        semantic_results = semantic_search_notes(
            db, query_embedding, current_user.id, retrieval_config
        )
        chunk_results = semantic_search_chunks(
            db, query_embedding, current_user.id, retrieval_config
        )

        # Full-text search as backup
        fulltext_results = fulltext_search_notes(
            db, query, current_user.id, limit=5
        )

        # Image retrieval
        image_results = []
        if body.include_images:
            # Get note IDs from semantic results for linked image search
            semantic_note_ids = [r.source_id for r in semantic_results if r.source_type == 'note']
            image_results = combined_image_retrieval(
                db, query, current_user.id, semantic_note_ids, limit=5
            )

        # Graph traversal
        graph_results = []
        if body.include_graph and semantic_results:
            # Use top semantic matches as seeds for graph traversal
            seed_ids = [r.source_id for r in semantic_results[:3] if r.source_type == 'note']
            if seed_ids:
                graph_config = GraphTraversalConfig(
                    max_hops=2,
                    max_results_per_hop=3,
                    relevance_decay=0.5,
                    include_backlinks=True
                )
                graph_results = graph_traversal(
                    db, seed_ids, current_user.id, graph_config
                )

        # Merge and rank all results using RRF
        ranking_config = RankingConfig(max_results=body.max_sources)
        ranked_results = merge_and_rank(
            semantic_results=semantic_results,
            chunk_results=chunk_results,
            graph_results=graph_results,
            fulltext_results=fulltext_results,
            image_results=image_results,
            config=ranking_config
        )

        # Build context with citations
        context_config = ContextConfig(
            max_tokens=4000,
            max_content_per_source=800,
            include_metadata=True,
            include_relationship_info=True
        )
        assembled_context = build_context(ranked_results, context_config)

        # Generate LLM response
        if not assembled_context.sources:
            # No relevant context found
            user_message = format_no_context_message(query)
            system_prompt = RAG_SYSTEM_PROMPT_CONCISE
        else:
            user_message = format_user_message_with_context(
                query=query,
                context=assembled_context.formatted_context,
                source_count=len(assembled_context.sources),
                config=RAGPromptConfig(
                    require_citations=True,
                    allow_no_context_response=True,
                    suggest_follow_ups=True,
                    confidence_instruction=True
                )
            )
            # Add query-specific instructions
            query_type = detect_query_type(query)
            extra_instructions = get_query_specific_instructions(query_type)
            system_prompt = f"{RAG_SYSTEM_PROMPT}\n\n{extra_instructions}"

        # Call LLM
        answer = call_ollama_generate(
            prompt=user_message,
            system_prompt=system_prompt
        )

        # Analyze response
        confidence = extract_confidence_signals(answer)
        citation_validation = validate_citations(answer, len(assembled_context.sources))
        used_indices = extract_citations_from_response(answer, assembled_context.sources)

        # Build retrieval metadata
        retrieval_summary = get_retrieval_summary(ranked_results)
        retrieval_metadata = schemas.RetrievalMetadata(
            total_sources_searched=retrieval_summary['total_sources_searched'],
            sources_used=len(assembled_context.sources),
            retrieval_methods_used=retrieval_summary['retrieval_methods_used'],
            avg_relevance_score=retrieval_summary['avg_relevance_score'],
            source_type_breakdown=retrieval_summary['source_type_breakdown'],
            query_type=detect_query_type(query),
            context_tokens_approx=assembled_context.total_tokens_approx,
            context_truncated=assembled_context.truncated
        )

        # Convert sources to citation list
        citations = [
            schemas.CitationSource(
                index=s.index,
                source_type=s.source_type,
                source_id=s.source_id,
                title=s.title,
                content_preview=s.content[:200] if len(s.content) > 200 else s.content,
                relevance_score=s.relevance_score,
                retrieval_method=s.retrieval_method,
                hop_count=s.hop_count,
                relationship_chain=s.relationship_chain if s.relationship_chain else None
            )
            for s in assembled_context.sources
        ]

        # Save to conversation if conversation_id provided
        message_id = None
        if body.conversation_id:
            try:
                # Verify conversation belongs to user
                conversation = db.query(Conversation).filter(
                    Conversation.id == body.conversation_id,
                    Conversation.owner_id == current_user.id
                ).first()

                if conversation:
                    # Save user message
                    user_msg = ChatMessage(
                        conversation_id=conversation.id,
                        role="user",
                        content=query
                    )
                    db.add(user_msg)
                    db.flush()

                    # Save assistant message
                    assistant_msg = ChatMessage(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=answer,
                        confidence_score=confidence['confidence_score'],
                        retrieval_metadata=retrieval_summary
                    )
                    db.add(assistant_msg)
                    db.flush()
                    message_id = assistant_msg.id

                    # Save citations
                    for citation in citations:
                        db_citation = MessageCitation(
                            message_id=message_id,
                            source_type=citation.source_type,
                            source_id=citation.source_id,
                            citation_index=citation.index,
                            relevance_score=citation.relevance_score,
                            retrieval_method=citation.retrieval_method,
                            hop_count=citation.hop_count,
                            relationship_chain=citation.relationship_chain
                        )
                        db.add(db_citation)

                    # Update conversation
                    conversation.updated_at = datetime.utcnow()
                    db.commit()

            except Exception as e:
                logger.error(f"Failed to save conversation: {e}")
                db.rollback()

        return schemas.RAGQueryResponse(
            answer=answer,
            citations=citations,
            used_citation_indices=used_indices,
            retrieval_metadata=retrieval_metadata,
            confidence_score=confidence['confidence_score'],
            confidence_level=confidence['confidence_level'],
            conversation_id=body.conversation_id,
            message_id=message_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"RAG query failed: {e}")
        raise HTTPException(500, f"RAG query failed: {str(e)}")


@router.post("/query/stream")
@limiter.limit("20/minute")
async def rag_query_stream(
    request: Request,
    body: schemas.RAGQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute a streaming RAG query with SSE (Server-Sent Events).

    Hybrid streaming approach:
    1. Retrieval phase (instant) - Get sources and build context
    2. Token streaming - Stream LLM tokens as they're generated
    3. Metadata append - Send citations and metadata after completion

    **Rate limit:** 20 requests/minute

    **SSE Event Types:**
    - `token`: LLM token chunk
    - `citations`: Citation list after completion
    - `metadata`: Retrieval metadata
    - `error`: Error message
    - `done`: Stream complete

    **Example:**
    ```
    POST /rag/query/stream
    Content-Type: application/json

    {"query": "What is machine learning?"}

    Response (SSE):
    data: {"type": "token", "content": "Machine"}
    data: {"type": "token", "content": " learning"}
    data: {"type": "token", "content": " is"}
    ...
    data: {"type": "citations", "citations": [...]}
    data: {"type": "metadata", "metadata": {...}}
    data: {"type": "done"}
    ```
    """
    query = body.query

    async def generate_stream():
        try:
            # Generate query embedding
            query_embedding = generate_embedding(query)
            if not query_embedding:
                yield f"data: {json.dumps({'type': 'error', 'content': 'Failed to generate embedding'})}\n\n"
                return

            # Configure retrieval
            retrieval_config = RetrievalConfig(
                min_similarity=body.min_similarity,
                max_results=body.max_sources,
                include_notes=True,
                include_chunks=True,
                include_images=body.include_images
            )

            # Perform retrieval (fast)
            semantic_results = semantic_search_notes(
                db, query_embedding, current_user.id, retrieval_config
            )
            chunk_results = semantic_search_chunks(
                db, query_embedding, current_user.id, retrieval_config
            )
            fulltext_results = fulltext_search_notes(db, query, current_user.id, limit=5)

            image_results = []
            if body.include_images:
                semantic_note_ids = [r.source_id for r in semantic_results if r.source_type == 'note']
                image_results = combined_image_retrieval(
                    db, query, current_user.id, semantic_note_ids, limit=5
                )

            graph_results = []
            if body.include_graph and semantic_results:
                seed_ids = [r.source_id for r in semantic_results[:3] if r.source_type == 'note']
                if seed_ids:
                    graph_results = graph_traversal(
                        db, seed_ids, current_user.id,
                        GraphTraversalConfig(max_hops=2, max_results_per_hop=3)
                    )

            # Merge and rank
            ranked_results = merge_and_rank(
                semantic_results=semantic_results,
                chunk_results=chunk_results,
                graph_results=graph_results,
                fulltext_results=fulltext_results,
                image_results=image_results,
                config=RankingConfig(max_results=body.max_sources)
            )

            # Build context
            assembled_context = build_context(ranked_results, ContextConfig())

            # Prepare prompt
            if not assembled_context.sources:
                user_message = format_no_context_message(query)
                system_prompt = RAG_SYSTEM_PROMPT_CONCISE
            else:
                user_message = format_user_message_with_context(
                    query=query,
                    context=assembled_context.formatted_context,
                    source_count=len(assembled_context.sources)
                )
                query_type = detect_query_type(query)
                extra_instructions = get_query_specific_instructions(query_type)
                system_prompt = f"{RAG_SYSTEM_PROMPT}\n\n{extra_instructions}"

            # Stream tokens
            full_response = ""
            for token in call_ollama_stream(user_message, system_prompt):
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # Analyze response
            confidence = extract_confidence_signals(full_response)
            used_indices = extract_citations_from_response(full_response, assembled_context.sources)
            retrieval_summary = get_retrieval_summary(ranked_results)

            # Build citations
            citations = [
                {
                    'index': s.index,
                    'source_type': s.source_type,
                    'source_id': s.source_id,
                    'title': s.title,
                    'content_preview': s.content[:200],
                    'relevance_score': s.relevance_score,
                    'retrieval_method': s.retrieval_method,
                    'hop_count': s.hop_count,
                    'relationship_chain': s.relationship_chain
                }
                for s in assembled_context.sources
            ]

            # Send citations
            yield f"data: {json.dumps({'type': 'citations', 'citations': citations, 'used_indices': used_indices})}\n\n"

            # Send metadata
            metadata = {
                'total_sources_searched': retrieval_summary['total_sources_searched'],
                'sources_used': len(assembled_context.sources),
                'retrieval_methods_used': retrieval_summary['retrieval_methods_used'],
                'avg_relevance_score': retrieval_summary['avg_relevance_score'],
                'source_type_breakdown': retrieval_summary['source_type_breakdown'],
                'query_type': detect_query_type(query),
                'context_tokens_approx': assembled_context.total_tokens_approx,
                'context_truncated': assembled_context.truncated,
                'confidence_score': confidence['confidence_score'],
                'confidence_level': confidence['confidence_level']
            }
            yield f"data: {json.dumps({'type': 'metadata', 'metadata': metadata})}\n\n"

            # Done
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.exception(f"Streaming RAG query failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


# ============================================
# Conversation Management Endpoints
# ============================================

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

    # Fetch messages with citations
    messages = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_id
    ).order_by(ChatMessage.created_at).all()

    message_responses = []
    for msg in messages:
        citations = []
        if msg.role == "assistant":
            db_citations = db.query(MessageCitation).filter(
                MessageCitation.message_id == msg.id
            ).all()

            for c in db_citations:
                # Get source title
                title = "Unknown"
                if c.source_type == "note":
                    note = db.query(Note).filter(Note.id == c.source_id).first()
                    title = note.title if note else "Deleted Note"
                elif c.source_type == "image":
                    image = db.query(Image).filter(Image.id == c.source_id).first()
                    title = image.filename if image else "Deleted Image"

                citations.append(schemas.CitationSource(
                    index=c.citation_index,
                    source_type=c.source_type,
                    source_id=c.source_id,
                    title=title,
                    content_preview="",  # Not stored
                    relevance_score=c.relevance_score,
                    retrieval_method=c.retrieval_method,
                    hop_count=c.hop_count or 0,
                    relationship_chain=c.relationship_chain
                ))

        message_responses.append(schemas.MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at,
            confidence_score=msg.confidence_score,
            retrieval_metadata=msg.retrieval_metadata,
            citations=citations
        ))

    return schemas.ConversationWithMessages(
        id=conversation.id,
        title=conversation.title,
        summary=conversation.summary,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=message_responses
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

    # Delete messages and citations (cascades)
    db.delete(conversation)
    db.commit()

    return {"message": "Conversation deleted", "id": conversation_id}


# ============================================
# Health & Status Endpoints
# ============================================

@router.get("/health")
async def rag_health():
    """
    Check RAG system health.

    Returns status of:
    - Ollama connectivity
    - Required models availability
    - Database connectivity
    """
    try:
        # Check Ollama
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        ollama_healthy = response.status_code == 200

        models = []
        if ollama_healthy:
            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]

        has_rag_model = any(RAG_MODEL in m for m in models)
        has_embedding_model = any("nomic-embed" in m for m in models)

        return {
            "status": "healthy" if (ollama_healthy and has_rag_model and has_embedding_model) else "degraded",
            "ollama": {
                "connected": ollama_healthy,
                "rag_model": RAG_MODEL,
                "rag_model_available": has_rag_model,
                "embedding_model_available": has_embedding_model
            },
            "available_models": models
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "ollama": {"connected": False}
        }
