"""
FastAPI router for Buckets feature.

Provides endpoints for:
- AI Clusters (K-means clustering on note embeddings)
- Orphan notes (notes with no wikilinks)
- Inbox (recently created notes)
- Daily notes (get/create daily notes)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, date
import logging

from core.database import get_db
from core.auth import get_current_user
from models import User

from features.buckets import schemas
from features.buckets.service import (
    ClusterService,
    OrphanService,
    InboxService,
    DailyNoteService
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/buckets", tags=["smart-buckets"])


# ============================================================================
# Cluster Endpoints
# ============================================================================

@router.get("/clusters", response_model=schemas.ClusterListResponse)
async def get_ai_clusters(
    k: int = Query(5, ge=2, le=20, description="Number of clusters"),
    force_refresh: bool = Query(False, description="Force regeneration (skip cache)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered note clusters.

    Uses K-means clustering on note embeddings to automatically organize notes
    into semantic groups. Results are cached for 1 hour.

    **Rate limit:** 10 requests/minute

    **Example:**
    ```
    GET /buckets/clusters?k=5
    ```

    Returns 5 clusters with labels, keywords, and note IDs.
    """
    logger.info(f"Get AI clusters: user={current_user.id}, k={k}, force={force_refresh}")

    try:
        result = ClusterService.get_clusters(
            db=db,
            owner_id=current_user.id,
            k=k,
            force_refresh=force_refresh
        )

        return schemas.ClusterListResponse(
            clusters=[schemas.ClusterInfo(**c) for c in result["clusters"]],
            total_clusters=result["total_clusters"],
            total_notes=result["total_notes"],
            average_cluster_size=result["average_cluster_size"],
            cached=result.get("cached", False)
        )

    except ValueError as e:
        logger.warning(f"Clustering failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Clustering failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate clusters: {str(e)}")


@router.get("/clusters/{cluster_id}/notes", response_model=schemas.ClusterNotesResponse)
async def get_cluster_notes(
    cluster_id: int,
    k: int = Query(5, ge=2, le=20, description="Number of clusters (must match cluster generation)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all notes in a specific cluster.

    **Rate limit:** 30 requests/minute

    **Example:**
    ```
    GET /buckets/clusters/0/notes?k=5
    ```

    Returns all notes in cluster #0.
    """
    logger.info(f"Get cluster notes: user={current_user.id}, cluster={cluster_id}, k={k}")

    try:
        result = ClusterService.get_cluster_notes(
            db=db,
            owner_id=current_user.id,
            cluster_id=cluster_id,
            k=k
        )

        # Convert notes to schema format
        note_infos = [
            schemas.NoteBasicInfo(
                id=note.id,
                title=note.title,
                content=note.content,
                created_at=note.created_at.isoformat() if note.created_at else "",
                updated_at=note.updated_at.isoformat() if note.updated_at else None
            )
            for note in result["notes"]
        ]

        return schemas.ClusterNotesResponse(
            cluster_id=cluster_id,
            label=result["label"],
            keywords=result["keywords"],
            notes=note_infos,
            total=result["total"]
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Get cluster notes failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get cluster notes: {str(e)}")


@router.post("/clusters/invalidate-cache", response_model=schemas.CacheInvalidateResponse)
async def invalidate_cluster_cache(
    current_user: User = Depends(get_current_user)
):
    """
    Invalidate cached cluster results for the current user.

    Useful after making significant changes to notes or their embeddings.

    **Rate limit:** 5 requests/minute

    **Example:**
    ```
    POST /buckets/clusters/invalidate-cache
    ```
    """
    logger.info(f"Invalidate cluster cache: user={current_user.id}")

    try:
        result = ClusterService.invalidate_cache(current_user.id)
        return schemas.CacheInvalidateResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Cache invalidation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")


# ============================================================================
# Orphan Endpoints
# ============================================================================

@router.get("/orphans", response_model=schemas.OrphansResponse)
async def get_orphan_notes(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get orphan notes - notes with no wikilinks (incoming or outgoing).

    These notes are isolated in the knowledge graph and might benefit from
    linking to other notes.

    **Rate limit:** 30 requests/minute

    **Example:**
    ```
    GET /buckets/orphans?limit=20
    ```

    Returns up to 20 orphan notes.
    """
    logger.info(f"Get orphan notes: user={current_user.id}, limit={limit}")

    try:
        notes = OrphanService.get_orphan_notes(
            db=db,
            owner_id=current_user.id,
            limit=limit
        )

        note_infos = [
            schemas.NoteBasicInfo(
                id=note.id,
                title=note.title,
                content=note.content,
                created_at=note.created_at.isoformat() if note.created_at else "",
                updated_at=note.updated_at.isoformat() if note.updated_at else None
            )
            for note in notes
        ]

        return schemas.OrphansResponse(
            notes=note_infos,
            total=len(note_infos)
        )

    except Exception as e:
        logger.error(f"Get orphan notes failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get orphan notes: {str(e)}")


# ============================================================================
# Inbox Endpoints
# ============================================================================

@router.get("/inbox", response_model=schemas.InboxResponse)
async def get_inbox_notes(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get inbox notes - recently created notes.

    **Rate limit:** 30 requests/minute

    **Example:**
    ```
    GET /buckets/inbox?days=7&limit=20
    ```

    Returns notes created in the last 7 days.
    """
    logger.info(f"Get inbox notes: user={current_user.id}, days={days}, limit={limit}")

    try:
        notes = InboxService.get_inbox_notes(
            db=db,
            owner_id=current_user.id,
            days=days,
            limit=limit
        )

        note_infos = [
            schemas.NoteBasicInfo(**note)
            for note in notes
        ]

        return schemas.InboxResponse(
            notes=note_infos,
            total=len(note_infos)
        )

    except Exception as e:
        logger.error(f"Get inbox notes failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get inbox notes: {str(e)}")


# ============================================================================
# Daily Note Endpoints
# ============================================================================

@router.get("/daily", response_model=schemas.DailyNotesListResponse)
async def get_daily_notes(
    days: int = Query(30, ge=1, le=90, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all daily notes.

    **Rate limit:** 30 requests/minute

    **Example:**
    ```
    GET /buckets/daily?days=30
    ```

    Returns daily notes from the last 30 days.
    """
    logger.info(f"Get daily notes: user={current_user.id}, days={days}")

    try:
        notes = DailyNoteService.get_daily_notes(
            db=db,
            owner_id=current_user.id,
            days=days
        )

        daily_notes = []
        for note in notes:
            # Extract date from title
            note_date = ""
            if note.title and note.title.startswith("Daily Note -"):
                try:
                    date_str = note.title.replace("Daily Note - ", "").strip()
                    note_date = date_str
                except:
                    note_date = note.created_at.date().isoformat() if note.created_at else ""
            else:
                note_date = note.created_at.date().isoformat() if note.created_at else ""

            daily_notes.append(schemas.DailyNoteResponse(
                id=note.id,
                title=note.title,
                content=note.content,
                date=note_date,
                created_at=note.created_at.isoformat() if note.created_at else "",
                updated_at=note.updated_at.isoformat() if note.updated_at else None,
                is_new=False
            ))

        return schemas.DailyNotesListResponse(
            notes=daily_notes,
            total=len(daily_notes)
        )

    except Exception as e:
        logger.error(f"Get daily notes failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get daily notes: {str(e)}")


@router.post("/daily/today", response_model=schemas.DailyNoteResponse)
async def get_or_create_today_note(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get or create today's daily note.

    If a daily note for today already exists, returns it.
    Otherwise, creates a new daily note with a template.

    **Rate limit:** 30 requests/minute

    **Example:**
    ```
    POST /buckets/daily/today
    ```

    Returns today's daily note (creates it if it doesn't exist).
    """
    logger.info(f"Get/create today's note: user={current_user.id}")

    try:
        result = DailyNoteService.get_or_create_daily_note(
            db=db,
            owner_id=current_user.id,
            target_date=None  # Today
        )

        note = result["note"]
        return schemas.DailyNoteResponse(
            id=note.id,
            title=note.title,
            content=note.content,
            date=result["date"],
            created_at=note.created_at.isoformat() if note.created_at else "",
            updated_at=note.updated_at.isoformat() if note.updated_at else None,
            is_new=result["is_new"]
        )

    except Exception as e:
        logger.error(f"Get/create today's note failed: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to get/create daily note: {str(e)}")


@router.get("/daily/{date_str}", response_model=schemas.DailyNoteResponse)
async def get_or_create_daily_note(
    date_str: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get or create a daily note for a specific date.

    **Rate limit:** 30 requests/minute

    **Example:**
    ```
    GET /buckets/daily/2025-11-27
    ```

    Returns the daily note for the specified date (creates it if it doesn't exist).
    """
    logger.info(f"Get/create daily note: user={current_user.id}, date={date_str}")

    try:
        # Parse and validate date
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD (e.g., 2025-11-27)"
            )

        result = DailyNoteService.get_or_create_daily_note(
            db=db,
            owner_id=current_user.id,
            target_date=target_date
        )

        note = result["note"]
        return schemas.DailyNoteResponse(
            id=note.id,
            title=note.title,
            content=note.content,
            date=result["date"],
            created_at=note.created_at.isoformat() if note.created_at else "",
            updated_at=note.updated_at.isoformat() if note.updated_at else None,
            is_new=result["is_new"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get/create daily note failed: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to get/create daily note: {str(e)}")
