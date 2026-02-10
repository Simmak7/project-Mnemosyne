/**
 * hashtagExtractor - Extract #hashtags from text for auto-tagging.
 *
 * Finds all #word patterns in text, excluding template tags like #daily-note.
 * Returns lowercase, deduplicated tag names.
 */

const HASHTAG_RE = /#([a-zA-Z][a-zA-Z0-9_-]*)/g;
const EXCLUDED_TAGS = new Set(['daily-note']);

/**
 * Extract hashtag names from text.
 * @param {string} text - Input text to scan
 * @returns {string[]} Array of unique, lowercase tag names
 */
export function extractHashtags(text) {
  if (!text) return [];

  const tags = new Set();
  let match;
  const re = new RegExp(HASHTAG_RE.source, 'g');

  while ((match = re.exec(text)) !== null) {
    const tag = match[1].toLowerCase();
    if (!EXCLUDED_TAGS.has(tag)) {
      tags.add(tag);
    }
  }

  return Array.from(tags);
}

export default extractHashtags;
