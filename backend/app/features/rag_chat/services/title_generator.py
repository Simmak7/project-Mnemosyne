"""
Conversation title generation utilities.

Provides smart title generation from user queries.
"""


def generate_conversation_title(query: str, max_length: int = 50) -> str:
    """
    Generate a conversation title from the query.

    Uses smart truncation:
    - If query is short enough, use as-is
    - Otherwise, truncate at word boundary and add "..."
    - Remove common question starters for cleaner titles

    Args:
        query: The user's query text
        max_length: Maximum title length

    Returns:
        Generated title string
    """
    # Clean up the query
    title = query.strip()

    # Remove common prefixes for cleaner titles
    prefixes_to_remove = [
        "what do i know about ",
        "what do you know about ",
        "tell me about ",
        "can you tell me about ",
        "explain ",
        "summarize ",
        "find ",
        "search for ",
        "what is ",
        "what are ",
        "how do i ",
        "how can i ",
        "who is ",
        "where is ",
        "when did ",
        "why did ",
    ]

    lower_title = title.lower()
    for prefix in prefixes_to_remove:
        if lower_title.startswith(prefix):
            title = title[len(prefix):]
            # Capitalize first letter after removing prefix
            if title:
                title = title[0].upper() + title[1:]
            break

    # Remove trailing punctuation
    title = title.rstrip("?!.")

    # Truncate if too long
    if len(title) > max_length:
        # Find last space before max_length
        truncate_at = title.rfind(' ', 0, max_length - 3)
        if truncate_at > max_length // 2:
            title = title[:truncate_at] + "..."
        else:
            title = title[:max_length - 3] + "..."

    return title or "New Conversation"
