"""
Images Feature - Search Endpoints

Text and semantic image search.
"""

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from typing import Literal
import logging

from core.database import get_db
from core.auth import get_current_active_user
from core import exceptions
import models

from features.images import schemas
from features.images.service import ImageService

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Image Processing"])


@router.get("/images/search/", response_model=list[schemas.ImageResponse])
@limiter.limit("30/minute")
async def search_images(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query"),
    search_type: Literal["text", "smart"] = Query("text", description="Search type: 'text' for full-text, 'smart' for AI semantic search"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results to return"),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Search images with full image data for gallery display.

    **Search Types:**
    - `text`: Full-text search on filename, description, and AI analysis
    - `smart`: AI-powered semantic search using embeddings (requires Ollama)

    Returns full image data including blur_hash, dimensions, tags, etc.
    for direct use in the gallery grid.

    **Rate Limit:** 30 requests/minute
    """
    logger.info(f"Image search: user={current_user.username}, query='{q}', type={search_type}")

    try:
        if search_type == "smart":
            images = ImageService.search_images_smart(
                db=db,
                owner_id=current_user.id,
                query=q,
                limit=limit
            )
        else:
            images = ImageService.search_images_text(
                db=db,
                owner_id=current_user.id,
                query=q,
                limit=limit
            )

        logger.info(f"Search returned {len(images)} images for query: {q}")
        return [schemas.ImageResponse.model_validate(img) for img in images]

    except Exception as e:
        logger.error(f"Image search failed: {str(e)}", exc_info=True)
        raise exceptions.ProcessingException(f"Search failed: {str(e)}")
