"""
Notes AI Enhancement Service

AI-powered: Improve Title, Summarize, Suggest Wikilinks, Regenerate.
"""

import logging
import requests
from typing import List, Dict
from sqlalchemy.orm import Session

from core import config

logger = logging.getLogger(__name__)

OLLAMA_HOST = config.OLLAMA_HOST
RAG_MODEL = config.RAG_MODEL
RAG_TIMEOUT = 60


def call_ollama(prompt: str, system_prompt: str, max_tokens: int = 256) -> str:
    """Call Ollama API for text generation."""
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": RAG_MODEL,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "think": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": max_tokens,
                }
            },
            timeout=RAG_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except requests.exceptions.Timeout:
        logger.error(f"Ollama timeout after {RAG_TIMEOUT}s")
        raise Exception("AI service timeout")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama request failed: {e}")
        raise Exception("AI service unavailable")


IMPROVE_TITLE_SYSTEM = """You are a note title generator. Given note content, generate a clear, concise, descriptive title that is DIFFERENT from the current one.

Rules:
- Title MUST be different from the current title
- Title should be 3-8 words
- Capture the main topic or theme
- Use title case
- No quotes, punctuation at end, or special characters
- Be specific, not generic
- Do NOT repeat or rephrase the current title

Respond with ONLY the new title, nothing else."""

def improve_title(content: str, current_title: str) -> str:
    """Generate an improved title for a note."""
    content_preview = content[:2000] if len(content) > 2000 else content

    prompt = f"""The current title is "{current_title}" but I need a DIFFERENT, better title.

Note content:
{content_preview}

Generate a completely new, more descriptive title (must be different from "{current_title}"):"""

    result = call_ollama(prompt, IMPROVE_TITLE_SYSTEM, max_tokens=50)

    # Clean up the result
    result = result.strip('"\'').strip()
    if result.endswith('.'):
        result = result[:-1]
    # Remove any leading "Title:" or similar prefixes
    for prefix in ['Title:', 'New Title:', 'Suggested Title:', 'Improved Title:']:
        if result.lower().startswith(prefix.lower()):
            result = result[len(prefix):].strip()

    # If AI returned the same title or empty, try harder
    if not result or result.lower().strip() == current_title.lower().strip():
        retry_prompt = f"""Read this note and create a SHORT title (3-6 words) that summarizes the key topic. Do NOT use the title "{current_title}".

{content_preview[:1000]}

New title:"""
        result = call_ollama(retry_prompt, IMPROVE_TITLE_SYSTEM, max_tokens=50)
        result = result.strip('"\'').strip()
        if result.endswith('.'):
            result = result[:-1]

    return result or current_title


SUMMARIZE_SYSTEM = """You are a note summarizer. Create a concise summary of the note content.

Rules:
- Summary should be 2-4 sentences
- Capture key points and main ideas
- Use clear, simple language
- Be informative but brief

Respond with ONLY the summary, nothing else."""

def summarize_note(content: str, title: str) -> str:
    """Generate a summary of a note."""
    content_preview = content[:3000] if len(content) > 3000 else content

    prompt = f"""Title: {title}

Content:
{content_preview}

Provide a concise summary:"""

    return call_ollama(prompt, SUMMARIZE_SYSTEM, max_tokens=200)


SUGGEST_WIKILINKS_SYSTEM = """You are a knowledge connection assistant. Given a note and a numbered list of other note titles, suggest which existing notes should be linked.

Rules:
- ONLY suggest notes from the numbered list below
- Use the EXACT title as shown in the list (copy it exactly)
- Explain briefly why each connection makes sense
- Maximum 5 suggestions
- Focus on meaningful semantic connections, not vague ones

Respond in this EXACT format (use the number and exact title from the list):
1. [[Exact Note Title From List]] - reason for connection
2. [[Another Exact Title From List]] - reason for connection

If no meaningful connections exist, respond with: NO_CONNECTIONS"""

def suggest_wikilinks(
    db: Session,
    note_id: int,
    content: str,
    title: str,
    owner_id: int
) -> List[Dict]:
    """Suggest potential wikilink connections for a note."""
    from features.notes.models import Note
    from difflib import get_close_matches

    other_notes = db.query(Note).filter(
        Note.owner_id == owner_id,
        Note.id != note_id,
        Note.is_trashed == False
    ).limit(100).all()

    if not other_notes:
        return []

    available_titles = [n.title for n in other_notes if n.title]
    titles_list = "\n".join(f"{i+1}. {t}" for i, t in enumerate(available_titles[:50]))

    content_preview = content[:2000] if len(content) > 2000 else content

    prompt = f"""Current note: "{title}"

Content:
{content_preview}

Available notes (use EXACT titles from this list):
{titles_list}

Which of these notes are related? Suggest connections using [[exact title]]:"""

    result = call_ollama(prompt, SUGGEST_WIKILINKS_SYSTEM, max_tokens=500)

    if 'NO_CONNECTIONS' in result:
        return []

    title_to_note = {n.title.lower(): n for n in other_notes if n.title}
    all_titles_lower = list(title_to_note.keys())

    suggestions = []
    for line in result.split('\n'):
        line = line.strip()
        if '[[' in line and ']]' in line:
            # Extract title from [[Title]]
            start = line.find('[[') + 2
            end = line.find(']]')
            if start > 1 and end > start:
                suggested_title = line[start:end].strip()

                # Try exact match first (case-insensitive)
                matched_note = title_to_note.get(suggested_title.lower())

                # Try fuzzy match if exact match fails
                if not matched_note and all_titles_lower:
                    close = get_close_matches(
                        suggested_title.lower(),
                        all_titles_lower,
                        n=1,
                        cutoff=0.6
                    )
                    if close:
                        matched_note = title_to_note.get(close[0])

                if matched_note:
                    # Avoid duplicates
                    if any(s['note_id'] == matched_note.id for s in suggestions):
                        continue
                    reason = ""
                    if ' - ' in line:
                        reason = line.split(' - ', 1)[1].strip()
                    suggestions.append({
                        "note_id": matched_note.id,
                        "title": matched_note.title,
                        "reason": reason
                    })

    return suggestions[:5]


# Re-export from split module
from features.notes.ai_regenerate import regenerate_from_source  # noqa: F401

def enhance_note(
    db: Session,
    note_id: int,
    content: str,
    title: str,
    owner_id: int
) -> Dict:
    """Run all AI enhancements and return results."""
    results = {
        "improved_title": None,
        "summary": None,
        "suggested_wikilinks": []
    }

    try:
        results["improved_title"] = improve_title(content, title)
    except Exception as e:
        logger.error(f"Error improving title: {e}")

    try:
        results["summary"] = summarize_note(content, title)
    except Exception as e:
        logger.error(f"Error summarizing: {e}")

    try:
        results["suggested_wikilinks"] = suggest_wikilinks(
            db, note_id, content, title, owner_id
        )
    except Exception as e:
        logger.error(f"Error suggesting wikilinks: {e}")

    return results
