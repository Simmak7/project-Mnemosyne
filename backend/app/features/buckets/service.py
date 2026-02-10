"""
Business logic for the Buckets feature.

Provides:
- AI Clustering operations
- Orphan note detection
- Inbox (recent notes)
- Daily notes management
- Redis caching for clusters
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import logging
import json
import os
import redis

from models import Note, Tag
from features.images.logic.clustering import cluster_notes_by_embeddings, get_cluster_statistics

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CACHE_EXPIRY = 3600  # 1 hour

# Initialize Redis client
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None


class ClusterService:
    """Service for AI clustering operations."""

    @staticmethod
    def get_clusters(
        db: Session,
        owner_id: int,
        k: int = 5,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get AI-powered note clusters.

        Args:
            db: Database session
            owner_id: User ID
            k: Number of clusters
            force_refresh: Skip cache if True

        Returns:
            Dictionary with clusters and statistics
        """
        cache_key = f"clusters:{owner_id}:k{k}"

        # Try cache first
        if redis_client and not force_refresh:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.info(f"Returning cached clusters for user {owner_id}")
                    data = json.loads(cached)
                    data['cached'] = True
                    return data
            except Exception as e:
                logger.warning(f"Cache retrieval failed: {e}")

        # Generate clusters
        cluster_results = cluster_notes_by_embeddings(db, owner_id, k=k)

        # Convert to dict format
        clusters = [
            {
                "cluster_id": c.cluster_id,
                "label": c.label,
                "keywords": c.keywords,
                "size": c.size,
                "emoji": c.emoji,
                "note_ids": c.note_ids
            }
            for c in cluster_results
        ]

        stats = get_cluster_statistics(cluster_results)

        response_data = {
            "clusters": clusters,
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
                logger.info(f"Cached clusters for user {owner_id}")
            except Exception as e:
                logger.warning(f"Cache storage failed: {e}")

        return response_data

    @staticmethod
    def get_cluster_notes(
        db: Session,
        owner_id: int,
        cluster_id: int,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Get notes in a specific cluster.

        Args:
            db: Database session
            owner_id: User ID
            cluster_id: Cluster ID
            k: Number of clusters (must match generation)

        Returns:
            Dictionary with cluster info and notes

        Raises:
            ValueError: If cluster not found
        """
        cluster_results = cluster_notes_by_embeddings(db, owner_id, k=k)

        # Find the requested cluster
        target_cluster = None
        for cluster in cluster_results:
            if cluster.cluster_id == cluster_id:
                target_cluster = cluster
                break

        if not target_cluster:
            raise ValueError(f"Cluster {cluster_id} not found (valid range: 0-{len(cluster_results)-1})")

        # Fetch the actual notes
        stmt = select(Note).where(
            Note.id.in_(target_cluster.note_ids),
            Note.owner_id == owner_id
        )
        result = db.execute(stmt)
        notes = result.scalars().all()

        return {
            "cluster_id": cluster_id,
            "label": target_cluster.label,
            "keywords": target_cluster.keywords,
            "notes": notes,
            "total": len(notes)
        }

    @staticmethod
    def invalidate_cache(owner_id: int) -> Dict[str, Any]:
        """
        Invalidate cached cluster results for a user.

        Args:
            owner_id: User ID

        Returns:
            Dictionary with invalidation result

        Raises:
            ValueError: If cache service unavailable
        """
        if not redis_client:
            raise ValueError("Cache service unavailable")

        pattern = f"clusters:{owner_id}:*"
        keys = redis_client.keys(pattern)

        if keys:
            deleted = redis_client.delete(*keys)
            logger.info(f"Invalidated {deleted} cluster cache entries for user {owner_id}")
            return {
                "status": "success",
                "invalidated_keys": deleted,
                "message": f"Invalidated {deleted} cluster cache entries"
            }

        return {
            "status": "success",
            "invalidated_keys": 0,
            "message": "No cache entries found"
        }


class OrphanService:
    """Service for orphan note operations."""

    @staticmethod
    def get_orphan_notes(
        db: Session,
        owner_id: int,
        limit: int = 50
    ) -> List[Note]:
        """
        Get orphan notes - notes with no wikilinks.

        Args:
            db: Database session
            owner_id: User ID
            limit: Maximum results

        Returns:
            List of orphan notes
        """
        stmt = select(Note).where(
            Note.owner_id == owner_id,
            ~Note.content.contains('[[')  # No wikilinks in content
        ).order_by(Note.created_at.desc()).limit(limit)

        result = db.execute(stmt)
        return result.scalars().all()


class InboxService:
    """Service for inbox (recent notes) operations."""

    @staticmethod
    def get_inbox_notes(
        db: Session,
        owner_id: int,
        days: int = 7,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get inbox notes - recently created notes.

        Args:
            db: Database session
            owner_id: User ID
            days: Number of days to look back
            limit: Maximum results

        Returns:
            List of note dictionaries
        """
        # Using raw SQL for date interval
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        stmt = select(Note).where(
            Note.owner_id == owner_id,
            Note.created_at >= cutoff_date
        ).order_by(Note.created_at.desc()).limit(limit)

        result = db.execute(stmt)
        notes = result.scalars().all()

        return [
            {
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "created_at": note.created_at.isoformat() if note.created_at else "",
                "updated_at": note.updated_at.isoformat() if note.updated_at else None
            }
            for note in notes
        ]


def generate_daily_note_template(target_date: date) -> tuple:
    """
    Generate daily note content and HTML template.

    Args:
        target_date: The date for the daily note

    Returns:
        Tuple of (plain_text_content, html_content)
    """
    formatted_date = target_date.strftime('%A, %B %d, %Y')

    # Plain text content for search indexing
    plain_content = f"""{formatted_date}

Morning Notes

Tasks
[ ] Add your tasks here...

Evening Reflection

#daily-note"""

    # HTML content for TipTap editor rendering
    html_content = f"""<h1>{formatted_date}</h1>
<h2>Morning Notes</h2>
<p></p>
<h2>Tasks</h2>
<ul data-type="taskList">
<li data-type="taskItem" data-checked="false"><p>Add your tasks here...</p></li>
</ul>
<h2>Evening Reflection</h2>
<p></p>
<hr>
<p><span data-hashtag="daily-note" class="hashtag">#daily-note</span></p>"""

    return plain_content, html_content


class DailyNoteService:
    """Service for daily note operations."""

    @staticmethod
    def get_daily_notes(
        db: Session,
        owner_id: int,
        days: int = 30
    ) -> List[Note]:
        """
        Get all daily notes.

        Args:
            db: Database session
            owner_id: User ID
            days: Maximum days to look back

        Returns:
            List of daily notes
        """
        stmt = select(Note).outerjoin(Note.tags).where(
            Note.owner_id == owner_id
        ).where(
            (Tag.name == "daily-note") |
            (Note.title.like("Daily Note -%"))
        ).order_by(Note.created_at.desc()).limit(days).distinct()

        result = db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    def get_or_create_daily_note(
        db: Session,
        owner_id: int,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get or create a daily note for a specific date.

        Args:
            db: Database session
            owner_id: User ID
            target_date: Date for the note (defaults to today)

        Returns:
            Dictionary with note data and is_new flag
        """
        if target_date is None:
            target_date = date.today()

        date_str = target_date.isoformat()
        title = f"Daily Note - {date_str}"

        # Check if note already exists
        stmt = select(Note).where(
            Note.owner_id == owner_id,
            Note.title == title
        )
        result = db.execute(stmt)
        existing_note = result.scalar_one_or_none()

        if existing_note:
            logger.info(f"Found existing daily note for {date_str}")
            return {
                "note": existing_note,
                "date": date_str,
                "is_new": False
            }

        # Create new daily note with template (both plain text and HTML)
        plain_content, html_content = generate_daily_note_template(target_date)

        # Get or create the "daily-note" tag
        tag = DailyNoteService._get_or_create_daily_tag(db, owner_id)

        new_note = Note(
            title=title,
            content=plain_content,
            html_content=html_content,
            owner_id=owner_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        new_note.tags = [tag]

        db.add(new_note)
        db.commit()
        db.refresh(new_note)

        logger.info(f"Created new daily note for {date_str}: note_id={new_note.id}")

        return {
            "note": new_note,
            "date": date_str,
            "is_new": True
        }

    @staticmethod
    def get_calendar_summary(
        db: Session,
        owner_id: int,
        year: int,
        month: int
    ) -> List[Dict[str, Any]]:
        """
        Get lightweight calendar summary for a month.
        Returns list of day summaries without loading full content.
        """
        import re
        prefix = f"Daily Note - {year}-{month:02d}"

        stmt = select(Note).where(
            Note.owner_id == owner_id,
            Note.title.like(f"{prefix}%")
        )
        result = db.execute(stmt)
        notes = result.scalars().all()

        task_re = re.compile(r'^[\s]*-\s*\[([ xX])\]', re.MULTILINE)
        capture_re = re.compile(r'^[\s]*-\s*\[\d{2}:\d{2}\]', re.MULTILINE)
        wikilink_re = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
        mood_re = re.compile(r'^Mood:\s*(.+)$', re.MULTILINE)

        summaries = []
        for note in notes:
            date_str = note.title.replace("Daily Note - ", "").strip()
            content = note.content or ""
            tasks = task_re.findall(content)
            task_count = len(tasks)
            completed = sum(1 for t in tasks if t.lower() == 'x')
            captures = len(capture_re.findall(content))
            wikilink_count = len(wikilink_re.findall(content))
            mood_match = mood_re.search(content)
            mood = mood_match.group(1).strip() if mood_match else None
            template_lines = {"Morning Notes", "Tasks", "Evening Reflection",
                              "Add your tasks here..."}
            has_content = any(
                line.strip() and line.strip().lstrip('#').strip() not in template_lines
                and not line.strip().startswith('#daily-note')
                for line in content.split('\n')
                if line.strip()
            )

            summaries.append({
                "date": date_str,
                "has_entry": True,
                "has_content": has_content,
                "task_count": task_count,
                "completed_tasks": completed,
                "capture_count": captures,
                "wikilink_count": wikilink_count,
                "mood": mood,
            })

        return summaries

    @staticmethod
    def _get_or_create_daily_tag(db: Session, owner_id: int) -> Tag:
        """Get or create the daily-note tag."""
        tag_name = "daily-note"
        tag = db.query(Tag).filter(Tag.name == tag_name).first()

        if not tag:
            try:
                tag = Tag(name=tag_name, owner_id=owner_id)
                db.add(tag)
                db.flush()
            except IntegrityError:
                db.rollback()
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    raise ValueError("Failed to create or retrieve daily-note tag")

        return tag
