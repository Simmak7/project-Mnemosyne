/**
 * Content parsers for journal day view.
 * Extract tasks, wikilinks, captures from daily note content.
 */

const TASK_RE = /^[\s]*-\s*\[([ xX])\]\s*(.*)$/gm;
const CAPTURE_RE = /^[\s]*-\s*\[(\d{2}:\d{2})\]\s*(.*)$/gm;
const WIKILINK_RE = /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g;

/**
 * Parse tasks from content.
 * @returns {{ text: string, checked: boolean, lineText: string }[]}
 */
export function parseTasks(content) {
  if (!content) return [];
  const tasks = [];
  let match;
  const re = new RegExp(TASK_RE.source, 'gm');
  while ((match = re.exec(content)) !== null) {
    const checked = match[1].toLowerCase() === 'x';
    const text = match[2].trim();
    // lineText is what we use to identify the line for toggle
    tasks.push({ text, checked, lineText: text });
  }
  return tasks;
}

/**
 * Parse captures (timestamped entries) from content.
 * @returns {{ time: string, text: string }[]}
 */
export function parseCaptures(content) {
  if (!content) return [];
  const captures = [];
  let match;
  const re = new RegExp(CAPTURE_RE.source, 'gm');
  while ((match = re.exec(content)) !== null) {
    captures.push({ time: match[1], text: match[2].trim() });
  }
  return captures;
}

/**
 * Parse wikilinks from content.
 * @returns {{ title: string, alias: string|null }[]}
 */
export function parseWikilinks(content) {
  if (!content) return [];
  const links = [];
  const seen = new Set();
  let match;
  const re = new RegExp(WIKILINK_RE.source, 'g');
  while ((match = re.exec(content)) !== null) {
    const title = match[1].trim();
    if (!seen.has(title)) {
      seen.add(title);
      links.push({ title, alias: match[2]?.trim() || null });
    }
  }
  return links;
}
