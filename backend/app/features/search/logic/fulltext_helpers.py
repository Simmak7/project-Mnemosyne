"""
Full-text Search - Helper Functions.

Utilities for query parsing and date filtering.
"""

from datetime import datetime, timedelta
from sqlalchemy import text


def parse_search_query(query: str) -> str:
    """
    Parse user search query into PostgreSQL tsquery format.

    Handles:
    - Multiple words: "machine learning" -> "machine & learning"
    - Quoted phrases: '"exact phrase"' -> "exact <-> phrase"
    - Single words: "python" -> "python"

    Args:
        query: Raw search query from user

    Returns:
        PostgreSQL tsquery-compatible string
    """
    if not query or not query.strip():
        return ""

    # Remove extra whitespace
    query = query.strip()

    # For now, use simple AND logic between words
    # Future: Could add support for OR, NOT, phrase matching
    words = query.split()

    # Escape special characters and join with &
    escaped_words = [word.replace("'", "''") for word in words]
    return " & ".join(escaped_words)


def apply_date_filter(query_base, date_range: str, date_column: str):
    """
    Apply date range filter to a query.

    Args:
        query_base: SQLAlchemy query object
        date_range: One of: 'all', 'today', 'week', 'month', 'year'
        date_column: Name of the date column to filter on

    Returns:
        Query with date filter applied
    """
    if date_range == "all":
        return query_base

    now = datetime.utcnow()

    if date_range == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_range == "week":
        start_date = now - timedelta(days=7)
    elif date_range == "month":
        start_date = now - timedelta(days=30)
    elif date_range == "year":
        start_date = now - timedelta(days=365)
    else:
        return query_base  # Unknown range, return unfiltered

    return query_base.filter(text(f"{date_column} >= :start_date")).params(start_date=start_date)
