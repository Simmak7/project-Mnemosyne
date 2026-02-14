"""
RAG Query endpoints for citation-aware AI responses.

Provides stateless and streaming RAG query endpoints.
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
from core.model_service import get_effective_rag_model, get_provider_for_user
from core.auth import get_current_user
from core.llm.base import LLMMessage, ProviderType
from core.llm.cost_tracker import log_token_usage, log_stream_usage
from models import User
from embeddings import generate_embedding

from features.rag_chat.models import Conversation, ChatMessage, MessageCitation
from features.rag_chat import schemas
from features.rag_chat.services import (
    RAGPromptConfig,
    RAG_SYSTEM_PROMPT,
    RAG_SYSTEM_PROMPT_CONCISE,
    format_user_message_with_context,
    format_no_context_message,
    extract_confidence_signals,
    extract_citations_from_response,
    detect_query_type,
    get_query_specific_instructions,
    ContextConfig,
    build_context,
    RankingConfig,
    merge_and_rank,
    get_retrieval_summary,
    RetrievalConfig,
    semantic_search_notes,
    semantic_search_chunks,
    fulltext_search_notes,
    combined_image_retrieval,
    GraphTraversalConfig,
    graph_traversal,
)
from features.rag_chat.services.ollama_client import call_ollama_generate, call_ollama_stream
from features.rag_chat.services.title_generator import generate_conversation_title
from features.rag_chat.services.query_executor import (
    QueryExecutionConfig,
    execute_query,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])
limiter = Limiter(key_func=get_remote_address)


def _build_citations(assembled_context) -> list:
    """Build citation list from assembled context."""
    return [
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


def _save_conversation(
    db: Session,
    conversation: Conversation,
    query: str,
    answer: str,
    citations: list,
    confidence: dict
) -> int:
    """Save messages and citations to conversation. Returns message_id."""
    user_msg = ChatMessage(conversation_id=conversation.id, role="user", content=query)
    db.add(user_msg)
    db.flush()

    assistant_msg = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        confidence_score=confidence['confidence_score']
    )
    db.add(assistant_msg)
    db.flush()
    message_id = assistant_msg.id

    for citation in citations:
        db_citation = MessageCitation(
            message_id=message_id,
            source_type=citation.source_type,
            source_id=citation.source_id,
            citation_index=citation.index,
            relevance_score=citation.relevance_score,
            retrieval_method=citation.retrieval_method,
            hop_count=citation.hop_count
        )
        db.add(db_citation)

    conversation.updated_at = datetime.utcnow()
    db.commit()
    return message_id


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

    **Rate limit:** 20 requests/minute
    """
    query = body.query
    logger.info(f"RAG query: user={current_user.id}, query='{query[:50]}...'")

    try:
        # Execute query pipeline
        config = QueryExecutionConfig(
            min_similarity=body.min_similarity,
            max_sources=body.max_sources,
            include_images=body.include_images,
            include_graph=body.include_graph
        )
        result = execute_query(db, query, current_user.id, config, body.conversation_id)

        # Prepare LLM prompt
        if not result.assembled_context.sources:
            user_message = format_no_context_message(query)
            system_prompt = RAG_SYSTEM_PROMPT_CONCISE
        else:
            user_message = format_user_message_with_context(
                query=query,
                context=result.assembled_context.formatted_context,
                source_count=len(result.assembled_context.sources),
                config=RAGPromptConfig(require_citations=True, allow_no_context_response=True)
            )
            query_type = detect_query_type(query)
            system_prompt = f"{RAG_SYSTEM_PROMPT}\n\n{get_query_specific_instructions(query_type)}"

        if result.conversation_context:
            user_message = result.conversation_context + user_message

        # Generate response (cloud-aware)
        provider, user_model, provider_name = get_provider_for_user(db, current_user.id, "rag")

        if provider_name != "ollama":
            # Cloud provider path
            messages = [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_message),
            ]
            try:
                llm_response = provider.generate(
                    messages=messages, model=user_model, temperature=0.3, max_tokens=2048,
                )
                answer = llm_response.content
                log_token_usage(db, current_user.id, llm_response, "rag")
            except Exception as cloud_err:
                logger.warning(f"Cloud provider {provider_name} failed, falling back to Ollama: {cloud_err}")
                user_model = get_effective_rag_model(db, current_user.id)
                answer = call_ollama_generate(prompt=user_message, system_prompt=system_prompt, model=user_model)
        else:
            answer = call_ollama_generate(prompt=user_message, system_prompt=system_prompt, model=user_model)

        # Analyze response
        confidence = extract_confidence_signals(answer)
        used_indices = extract_citations_from_response(answer, result.assembled_context.sources)
        citations = _build_citations(result.assembled_context)

        # Build metadata
        retrieval_metadata = schemas.RetrievalMetadata(
            total_sources_searched=result.retrieval_summary['total_sources_searched'],
            sources_used=len(result.assembled_context.sources),
            retrieval_methods_used=result.retrieval_summary['retrieval_methods_used'],
            avg_relevance_score=result.retrieval_summary['avg_relevance_score'],
            source_type_breakdown=result.retrieval_summary['source_type_breakdown'],
            query_type=detect_query_type(query),
            context_tokens_approx=result.assembled_context.total_tokens_approx,
            context_truncated=result.assembled_context.truncated
        )

        # Handle conversation persistence
        message_id = None
        conversation_id = body.conversation_id
        conversation = None

        try:
            if body.conversation_id:
                conversation = db.query(Conversation).filter(
                    Conversation.id == body.conversation_id,
                    Conversation.owner_id == current_user.id
                ).first()
                if not conversation:
                    conversation_id = None

            if not conversation and body.auto_create_conversation:
                title = generate_conversation_title(query)
                conversation = Conversation(owner_id=current_user.id, title=title)
                db.add(conversation)
                db.flush()
                conversation_id = conversation.id

            if conversation:
                message_id = _save_conversation(db, conversation, query, answer, citations, confidence)

        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            db.rollback()
            conversation_id = body.conversation_id

        return schemas.RAGQueryResponse(
            answer=answer,
            citations=citations,
            used_citation_indices=used_indices,
            retrieval_metadata=retrieval_metadata,
            confidence_score=confidence['confidence_score'],
            confidence_level=confidence['confidence_level'],
            conversation_id=conversation_id,
            message_id=message_id,
            model_used=user_model
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
    Execute a streaming RAG query with SSE.

    **Rate limit:** 20 requests/minute
    """
    query = body.query
    user_id = current_user.id

    # Handle conversation before streaming
    conversation_id = body.conversation_id
    conversation = None

    if body.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == body.conversation_id,
            Conversation.owner_id == user_id
        ).first()
        if not conversation:
            conversation_id = None

    if not conversation and body.auto_create_conversation:
        title = generate_conversation_title(query)
        conversation = Conversation(owner_id=user_id, title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        conversation_id = conversation.id

    async def generate_stream():
        try:
            query_embedding = generate_embedding(query)
            if not query_embedding:
                yield f"data: {json.dumps({'type': 'error', 'content': 'Failed to generate embedding'})}\n\n"
                return

            # Retrieval
            retrieval_config = RetrievalConfig(
                min_similarity=body.min_similarity,
                max_results=body.max_sources,
                include_notes=True, include_chunks=True, include_images=body.include_images
            )

            semantic_results = semantic_search_notes(db, query_embedding, user_id, retrieval_config)
            chunk_results = semantic_search_chunks(db, query_embedding, user_id, retrieval_config)
            fulltext_results = fulltext_search_notes(db, query, user_id, limit=5)

            image_results = []
            if body.include_images:
                note_ids = [r.source_id for r in semantic_results if r.source_type == 'note']
                image_results = combined_image_retrieval(db, query, user_id, note_ids, limit=5)

            graph_results = []
            if body.include_graph and semantic_results:
                seed_ids = [r.source_id for r in semantic_results[:3] if r.source_type == 'note']
                if seed_ids:
                    graph_results = graph_traversal(db, seed_ids, user_id, GraphTraversalConfig(max_hops=2, max_results_per_hop=3))

            ranked_results = merge_and_rank(
                semantic_results=semantic_results, chunk_results=chunk_results,
                graph_results=graph_results, fulltext_results=fulltext_results,
                image_results=image_results, config=RankingConfig(max_results=body.max_sources), query=query
            )

            assembled_context = build_context(ranked_results, ContextConfig())

            # Prepare prompt
            if not assembled_context.sources:
                user_message = format_no_context_message(query)
                system_prompt = RAG_SYSTEM_PROMPT_CONCISE
            else:
                user_message = format_user_message_with_context(
                    query=query, context=assembled_context.formatted_context,
                    source_count=len(assembled_context.sources)
                )
                system_prompt = f"{RAG_SYSTEM_PROMPT}\n\n{get_query_specific_instructions(detect_query_type(query))}"

            provider, user_model, provider_name = get_provider_for_user(db, user_id, "rag")

            # Stream tokens (cloud-aware)
            full_response = ""
            stream_input_tokens = 0
            stream_output_tokens = 0

            if provider_name != "ollama":
                messages = [
                    LLMMessage(role="system", content=system_prompt),
                    LLMMessage(role="user", content=user_message),
                ]
                try:
                    for chunk in provider.stream(
                        messages=messages, model=user_model, temperature=0.3, max_tokens=2048,
                    ):
                        if chunk.content:
                            full_response += chunk.content
                            yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
                        if chunk.done:
                            stream_input_tokens = chunk.input_tokens
                            stream_output_tokens = chunk.output_tokens
                            break
                    # Log cloud usage
                    from core.llm.base import ProviderType as PT
                    ptype = {"anthropic": PT.ANTHROPIC, "openai": PT.OPENAI, "custom": PT.CUSTOM}.get(provider_name, PT.OLLAMA)
                    log_stream_usage(db, user_id, ptype, user_model, stream_input_tokens, stream_output_tokens, "rag")
                except Exception as cloud_err:
                    logger.warning(f"Cloud stream failed, falling back to Ollama: {cloud_err}")
                    user_model = get_effective_rag_model(db, user_id)
                    for token in call_ollama_stream(user_message, system_prompt, model=user_model):
                        full_response += token
                        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            else:
                for token in call_ollama_stream(user_message, system_prompt, model=user_model):
                    full_response += token
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # Post-process
            confidence = extract_confidence_signals(full_response)
            used_indices = extract_citations_from_response(full_response, assembled_context.sources)
            retrieval_summary = get_retrieval_summary(ranked_results)

            citations = [
                {'index': s.index, 'source_type': s.source_type, 'source_id': s.source_id,
                 'title': s.title, 'content_preview': s.content[:200], 'relevance_score': s.relevance_score,
                 'retrieval_method': s.retrieval_method, 'hop_count': s.hop_count, 'relationship_chain': s.relationship_chain}
                for s in assembled_context.sources
            ]

            yield f"data: {json.dumps({'type': 'citations', 'citations': citations, 'used_indices': used_indices})}\n\n"

            # Save conversation
            message_id = None
            if conversation:
                try:
                    user_msg = ChatMessage(conversation_id=conversation.id, role="user", content=query)
                    db.add(user_msg)
                    db.flush()

                    assistant_msg = ChatMessage(
                        conversation_id=conversation.id, role="assistant",
                        content=full_response, confidence_score=confidence['confidence_score']
                    )
                    db.add(assistant_msg)
                    db.flush()
                    message_id = assistant_msg.id

                    for c in citations:
                        db.add(MessageCitation(
                            message_id=message_id, source_type=c['source_type'], source_id=c['source_id'],
                            citation_index=c['index'], relevance_score=c['relevance_score'],
                            retrieval_method=c['retrieval_method'], hop_count=c['hop_count'] or 0
                        ))

                    conversation.updated_at = datetime.utcnow()
                    db.commit()
                except Exception as e:
                    logger.error(f"Failed to save streaming conversation: {e}")
                    db.rollback()

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
                'confidence_level': confidence['confidence_level'],
                'conversation_id': conversation_id,
                'message_id': message_id,
                'model_used': user_model
            }
            yield f"data: {json.dumps({'type': 'metadata', 'metadata': metadata})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.exception(f"Streaming RAG query failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )
