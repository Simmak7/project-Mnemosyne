"""
Wikilink parser for Obsidian-style [[wikilinks]] in markdown content.

Provides utilities for:
- Extracting wikilinks from content
- Parsing wikilink syntax (with aliases)
- Creating URL-friendly slugs from titles
- Hashtag extraction for tags
"""

import re
import unicodedata
from typing import List, Tuple, Set


def extract_wikilinks(content: str) -> List[str]:
    """
    Extract [[wikilink]] references from markdown content.

    Supports formats:
    - [[note-title]]
    - [[note-title|display alias]]

    Args:
        content: Markdown content to parse

    Returns:
        List of wikilink targets (without aliases)
    """
    # Pattern: [[target]] or [[target|alias]]
    pattern = r'\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]'
    matches = re.findall(pattern, content)
    return [match.strip() for match in matches]


def parse_wikilink(wikilink: str) -> Tuple[str, str | None]:
    """
    Parse [[title]] or [[title|alias]] format.

    Args:
        wikilink: Raw wikilink text (without [[ ]])

    Returns:
        Tuple of (target, alias) where alias is None if not provided
    """
    if '|' in wikilink:
        target, alias = wikilink.split('|', 1)
        return target.strip(), alias.strip()
    return wikilink.strip(), None


def extract_hashtags(content: str) -> Set[str]:
    """
    Extract #hashtags from content.

    Supports:
    - #tag
    - #multi-word-tag
    - #camelCaseTag

    Args:
        content: Content to parse

    Returns:
        Set of hashtags (lowercase, without # prefix)
    """
    # Pattern: # followed by alphanumeric, hyphens, underscores
    # Must be preceded by whitespace or start of string
    # Must not be followed by another #
    pattern = r'(?:^|\s)#([\w-]+)'
    matches = re.findall(pattern, content)
    return {match.lower() for match in matches}


def create_slug(title: str) -> str:
    """
    Create URL-friendly slug from title.

    Transformations:
    - Remove accents/diacritics
    - Convert to lowercase
    - Replace spaces and special chars with hyphens
    - Remove duplicate hyphens
    - Trim leading/trailing hyphens

    Args:
        title: Note title

    Returns:
        URL-friendly slug

    Examples:
        "My Note Title" -> "my-note-title"
        "Cafe Notes!" -> "cafe-notes"
        "  Spaced   Out  " -> "spaced-out"
    """
    # Normalize unicode (remove accents)
    title = unicodedata.normalize('NFKD', title)
    title = title.encode('ascii', 'ignore').decode('ascii')

    # Lowercase
    title = title.lower()

    # Replace non-word characters (except hyphens) with hyphens
    title = re.sub(r'[^\w\s-]', '', title)

    # Replace whitespace and multiple hyphens with single hyphen
    title = re.sub(r'[-\s]+', '-', title)

    # Trim hyphens from ends
    title = title.strip('-')

    return title


def find_wikilink_positions(content: str) -> List[Tuple[int, int, str]]:
    """
    Find positions of all wikilinks in content.

    Useful for syntax highlighting or link replacement.

    Args:
        content: Content to search

    Returns:
        List of (start_pos, end_pos, target) tuples
    """
    pattern = r'\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]'
    positions = []

    for match in re.finditer(pattern, content):
        start = match.start()
        end = match.end()
        target = match.group(1).strip()
        positions.append((start, end, target))

    return positions


def replace_wikilinks_with_markdown(content: str, link_resolver) -> str:
    """
    Replace [[wikilinks]] with standard markdown [links](url).

    Args:
        content: Content with wikilinks
        link_resolver: Function that takes (target, alias) and returns URL or None

    Returns:
        Content with markdown links

    Example:
        link_resolver = lambda target, alias: f"/notes/{target.lower()}"
        replace_wikilinks_with_markdown("See [[My Note]]", link_resolver)
        # Returns: "See [My Note](/notes/my-note)"
    """
    def replacer(match):
        full_match = match.group(0)
        target_with_alias = match.group(1)

        target, alias = parse_wikilink(target_with_alias)
        display_text = alias if alias else target

        url = link_resolver(target, alias)
        if url:
            return f"[{display_text}]({url})"
        else:
            # Keep original if link can't be resolved
            return full_match

    pattern = r'\[\[([^\]]+)\]\]'
    return re.sub(pattern, replacer, content)


def validate_wikilink_syntax(content: str) -> List[Tuple[int, str]]:
    """
    Validate wikilink syntax and return errors.

    Checks for:
    - Empty wikilinks: [[]]
    - Unclosed wikilinks: [[note
    - Multiple pipes: [[note|alias|extra]]

    Args:
        content: Content to validate

    Returns:
        List of (line_number, error_message) tuples
    """
    errors = []
    lines = content.split('\n')

    for line_num, line in enumerate(lines, start=1):
        # Check for empty wikilinks
        if '[[]]' in line:
            errors.append((line_num, "Empty wikilink found: [[]]"))

        # Check for unclosed wikilinks
        open_count = line.count('[[')
        close_count = line.count(']]')
        if open_count != close_count:
            errors.append((line_num, f"Unclosed wikilink (found {open_count} '[[' but {close_count} ']]')"))

        # Check for multiple pipes in wikilinks
        for match in re.finditer(r'\[\[([^\]]+)\]\]', line):
            link_content = match.group(1)
            if link_content.count('|') > 1:
                errors.append((line_num, f"Multiple pipes in wikilink: [[{link_content}]]"))

    return errors
