"""
Mnemosyne Brain Chat - Conversation CRUD Endpoints.

Create, list, get, update, delete brain conversations.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.database import get_db
from core.auth import get_current_user
import models

from features.mnemosyne_brain.models.brain_conversation import BrainConversation
from features.mnemosyne_brain import schemas

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/mnemosyne", tags=["mnemosyne-brain-chat"])


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
