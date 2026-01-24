"""
Smart Buckets API endpoints.

Provides AI-powered note organization using clustering and semantic analysis.
Includes endpoints for AI Clusters, Orphans, Inbox, etc.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
import logging
import json
import os

from core.database import get_db
from models import User, Note, Tag
from core.auth import get_current_user
from clustering import cluster_notes_by_embeddings, get_cluster_statistics
import redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/buckets", tags=["smart-buckets"])

# Redis for caching cluster results
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CACHE_EXPIRY = 3600  # 1 hour

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None


# Response schemas
class ClusterInfo(BaseModel):
    """Information about a cluster."""
    cluster_id: int
    label: str
    keywords: List[str]
    size: int
    emoji: str
    note_ids: List[int]

    class Config:
        from_attributes = True


class ClusterListResponse(BaseModel):
    """Response for cluster list."""
    clusters: List[ClusterInfo]
    total_clusters: int
    total_notes: int
    average_cluster_size: float
    cached: bool = Field(default=False, description="Whether result came from cache")


class NoteBasicInfo(BaseModel):
    """Basic note information."""
    id: int
    title: str
    content: str
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class ClusterNotesResponse(BaseModel):
    """Response for notes in a cluster."""
    cluster_id: int
    label: str
    keywords: List[str]
    notes: List[NoteBasicInfo]
    total: int


class OrphansResponse(BaseModel):
    """Response for orphan notes."""
    notes: List[NoteBasicInfo]
    total: int
    description: str = "Notes with no wikilinks (incoming or outgoing)"


class InboxResponse(BaseModel):
    """Response for inbox notes."""
    notes: List[NoteBasicInfo]
    total: int
    description: str = "Recently created notes (last 7 days)"


class DailyNoteResponse(BaseModel):
    """Response for a daily note."""
    id: int
    title: str
    content: str
    date: str
    created_at: str
    updated_at: Optional[str]
    is_new: bool = Field(default=False, description="Whether this note was just created")

    class Config:
        from_attributes = True


class DailyNotesListResponse(BaseModel):
    """Response for daily notes list."""
    notes: List[DailyNoteResponse]
    total: int
    description: str = "Daily notes organized by date"


@router.get("/clusters", response_model=ClusterListResponse)
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

    cache_key = f"clusters:{current_user.id}:k{k}"

    # Try to get from cache (unless force refresh)
    if redis_client and not force_refresh:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                logger.info(f"Returning cached clusters for user {current_user.id}")
                data = json.loads(cached)
                data['cached'] = True
                return ClusterListResponse(**data)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")

    # Generate clusters
    try:
        cluster_results = cluster_notes_by_embeddings(db, current_user.id, k=k)

        # Convert to response format
        clusters = [
            ClusterInfo(
                cluster_id=c.cluster_id,
                label=c.label,
                keywords=c.keywords,
                size=c.size,
                emoji=c.emoji,
                note_ids=c.note_ids
            )
            for c in cluster_results
        ]

        stats = get_cluster_statistics(cluster_results)

        response_data = {
            "clusters": [c.dict() for c in clusters],
            "total_clusters": stats['total_clusters'],
            "total_notes": stats['total_notes'],
            "average_cluster_size": stats['average_cluster_size'],
            "cached": False
        }

        # Cache the result
        if redis_client:
            try:
                redis_client.setex(
                    cache_key,
                    CACHE_EXPIRY,
                    json.dumps(response_data)
                )
                logger.info(f"Cached clusters for user {current_user.id}")
            except Exception as e:
                logger.warning(f"Cache storage failed: {e}")

        return ClusterListResponse(**response_data)

    except ValueError as e:
        # Not enough notes for clustering
        logger.warning(f"Clustering failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Clustering failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate clusters: {str(e)}"
        )


@router.get("/clusters/{cluster_id}/notes", response_model=ClusterNotesResponse)
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

    # Regenerate clusters to get the specific cluster
    # (We could cache this, but clusters are already cached in /clusters endpoint)
    try:
        cluster_results = cluster_notes_by_embeddings(db, current_user.id, k=k)

        # Find the requested cluster
        target_cluster = None
        for cluster in cluster_results:
            if cluster.cluster_id == cluster_id:
                target_cluster = cluster
                break

        if not target_cluster:
            raise HTTPException(
                status_code=404,
                detail=f"Cluster {cluster_id} not found (valid range: 0-{len(cluster_results)-1})"
            )

        # Fetch the actual notes
        stmt = select(Note).where(
            Note.id.in_(target_cluster.note_ids),
            Note.owner_id == current_user.id
        )
        result = db.execute(stmt)
        notes = result.scalars().all()

        # Convert to response format
        note_infos = [
            NoteBasicInfo(
                id=note.id,
                title=note.title,
                content=note.content,
                created_at=note.created_at.isoformat() if note.created_at else "",
                updated_at=note.updated_at.isoformat() if note.updated_at else None
            )
            for note in notes
        ]

        return ClusterNotesResponse(
            cluster_id=cluster_id,
            label=target_cluster.label,
            keywords=target_cluster.keywords,
            notes=note_infos,
            total=len(note_infos)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get cluster notes failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cluster notes: {str(e)}"
        )


@router.get("/orphans", response_model=OrphansResponse)
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
        # Find notes with no wikilinks
        # A note is an orphan if:
        # 1. Its content contains no [[wikilinks]]
        # 2. No other notes link to it

        # Note: Simplified version for performance. For complete orphan detection
        # with backlink checking, see crud_wikilinks.find_orphaned_notes().
        # This quick check uses SQL pattern matching for speed.

        stmt = select(Note).where(
            Note.owner_id == current_user.id,
            ~Note.content.contains('[[')  # No wikilinks in content
        ).order_by(Note.created_at.desc()).limit(limit)

        result = db.execute(stmt)
        notes = result.scalars().all()

        note_infos = [
            NoteBasicInfo(
                id=note.id,
                title=note.title,
                content=note.content,
                created_at=note.created_at.isoformat() if note.created_at else "",
                updated_at=note.updated_at.isoformat() if note.updated_at else None
            )
            for note in notes
        ]

        return OrphansResponse(
            notes=note_infos,
            total=len(note_infos)
        )

    except Exception as e:
        logger.error(f"Get orphan notes failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get orphan notes: {str(e)}"
        )


@router.get("/inbox", response_model=InboxResponse)
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
        # Get notes created in the last N days
        query_text = text("""
            SELECT id, title, content, created_at, updated_at
            FROM notes
            WHERE
                owner_id = :owner_id
                AND created_at >= NOW() - INTERVAL ':days days'
            ORDER BY created_at DESC
            LIMIT :limit
        """)

        result = db.execute(
            query_text,
            {
                "owner_id": current_user.id,
                "days": days,
                "limit": limit
            }
        )

        rows = result.fetchall()

        note_infos = [
            NoteBasicInfo(
                id=row[0],
                title=row[1],
                content=row[2],
                created_at=row[3].isoformat() if row[3] else "",
                updated_at=row[4].isoformat() if row[4] else None
            )
            for row in rows
        ]

        return InboxResponse(
            notes=note_infos,
            total=len(note_infos)
        )

    except Exception as e:
        logger.error(f"Get inbox notes failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get inbox notes: {str(e)}"
        )


@router.get("/daily", response_model=DailyNotesListResponse)
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
        # Find notes with #daily-note tag or title starting with "Daily Note -"
        # Use join to find notes with the "daily-note" tag
        stmt = select(Note).outerjoin(Note.tags).where(
            Note.owner_id == current_user.id
        ).where(
            (Tag.name == "daily-note") |
            (Note.title.like("Daily Note -%"))
        ).order_by(Note.created_at.desc()).limit(days).distinct()

        result = db.execute(stmt)
        notes = result.scalars().all()

        daily_notes = []
        for note in notes:
            # Extract date from title (format: "Daily Note - YYYY-MM-DD")
            note_date = ""
            if note.title and note.title.startswith("Daily Note -"):
                try:
                    date_str = note.title.replace("Daily Note - ", "").strip()
                    note_date = date_str
                except:
                    note_date = note.created_at.date().isoformat() if note.created_at else ""
            else:
                note_date = note.created_at.date().isoformat() if note.created_at else ""

            daily_notes.append(DailyNoteResponse(
                id=note.id,
                title=note.title,
                content=note.content,
                date=note_date,
                created_at=note.created_at.isoformat() if note.created_at else "",
                updated_at=note.updated_at.isoformat() if note.updated_at else None,
                is_new=False
            ))

        return DailyNotesListResponse(
            notes=daily_notes,
            total=len(daily_notes)
        )

    except Exception as e:
        logger.error(f"Get daily notes failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get daily notes: {str(e)}"
        )


@router.post("/daily/today", response_model=DailyNoteResponse)
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
        today = date.today()
        today_str = today.isoformat()
        title = f"Daily Note - {today_str}"

        # Check if note already exists
        stmt = select(Note).where(
            Note.owner_id == current_user.id,
            Note.title == title
        )
        result = db.execute(stmt)
        existing_note = result.scalar_one_or_none()

        if existing_note:
            logger.info(f"Found existing daily note for {today_str}")
            return DailyNoteResponse(
                id=existing_note.id,
                title=existing_note.title,
                content=existing_note.content,
                date=today_str,
                created_at=existing_note.created_at.isoformat() if existing_note.created_at else "",
                updated_at=existing_note.updated_at.isoformat() if existing_note.updated_at else None,
                is_new=False
            )

        # Create new daily note with template
        template_content = f"""# {today.strftime('%A, %B %d, %Y')}

## Morning Notes


## Tasks
- [ ]


## Evening Reflection


---
#daily-note
"""

        # Get or create the "daily-note" tag (tags are globally unique)
        tag_name = "daily-note"
        tag = db.query(Tag).filter(Tag.name == tag_name).first()

        if not tag:
            try:
                tag = Tag(name=tag_name, owner_id=current_user.id)
                db.add(tag)
                db.flush()  # Get the tag ID without committing
            except IntegrityError:
                # Tag was created by another request, fetch it again
                db.rollback()
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    # This should never happen, but handle gracefully
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to create or retrieve daily-note tag"
                    )

        new_note = Note(
            title=title,
            content=template_content,
            owner_id=current_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        new_note.tags = [tag]  # Associate the tag object

        db.add(new_note)
        db.commit()
        db.refresh(new_note)

        logger.info(f"Created new daily note for {today_str}: note_id={new_note.id}")

        return DailyNoteResponse(
            id=new_note.id,
            title=new_note.title,
            content=new_note.content,
            date=today_str,
            created_at=new_note.created_at.isoformat() if new_note.created_at else "",
            updated_at=new_note.updated_at.isoformat() if new_note.updated_at else None,
            is_new=True
        )

    except Exception as e:
        logger.error(f"Get/create today's note failed: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get/create daily note: {str(e)}"
        )


@router.get("/daily/{date_str}", response_model=DailyNoteResponse)
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
                detail=f"Invalid date format. Use YYYY-MM-DD (e.g., 2025-11-27)"
            )

        title = f"Daily Note - {date_str}"

        # Check if note already exists
        stmt = select(Note).where(
            Note.owner_id == current_user.id,
            Note.title == title
        )
        result = db.execute(stmt)
        existing_note = result.scalar_one_or_none()

        if existing_note:
            logger.info(f"Found existing daily note for {date_str}")
            return DailyNoteResponse(
                id=existing_note.id,
                title=existing_note.title,
                content=existing_note.content,
                date=date_str,
                created_at=existing_note.created_at.isoformat() if existing_note.created_at else "",
                updated_at=existing_note.updated_at.isoformat() if existing_note.updated_at else None,
                is_new=False
            )

        # Create new daily note with template
        template_content = f"""# {target_date.strftime('%A, %B %d, %Y')}

## Morning Notes


## Tasks
- [ ]


## Evening Reflection


---
#daily-note
"""

        # Get or create the "daily-note" tag (tags are globally unique)
        tag_name = "daily-note"
        tag = db.query(Tag).filter(Tag.name == tag_name).first()

        if not tag:
            try:
                tag = Tag(name=tag_name, owner_id=current_user.id)
                db.add(tag)
                db.flush()  # Get the tag ID without committing
            except IntegrityError:
                # Tag was created by another request, fetch it again
                db.rollback()
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    # This should never happen, but handle gracefully
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to create or retrieve daily-note tag"
                    )

        new_note = Note(
            title=title,
            content=template_content,
            owner_id=current_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        new_note.tags = [tag]  # Associate the tag object

        db.add(new_note)
        db.commit()
        db.refresh(new_note)

        logger.info(f"Created new daily note for {date_str}: note_id={new_note.id}")

        return DailyNoteResponse(
            id=new_note.id,
            title=new_note.title,
            content=new_note.content,
            date=date_str,
            created_at=new_note.created_at.isoformat() if new_note.created_at else "",
            updated_at=new_note.updated_at.isoformat() if new_note.updated_at else None,
            is_new=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get/create daily note failed: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get/create daily note: {str(e)}"
        )


@router.post("/clusters/invalidate-cache")
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
    if not redis_client:
        raise HTTPException(
            status_code=503,
            detail="Cache service unavailable"
        )

    try:
        # Delete all cluster cache keys for this user
        pattern = f"clusters:{current_user.id}:*"
        keys = redis_client.keys(pattern)

        if keys:
            deleted = redis_client.delete(*keys)
            logger.info(f"Invalidated {deleted} cluster cache entries for user {current_user.id}")

            return {
                "status": "success",
                "invalidated_keys": deleted,
                "message": f"Invalidated {deleted} cluster cache entries"
            }
        else:
            return {
                "status": "success",
                "invalidated_keys": 0,
                "message": "No cache entries found"
            }

    except Exception as e:
        logger.error(f"Cache invalidation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invalidate cache: {str(e)}"
        )
