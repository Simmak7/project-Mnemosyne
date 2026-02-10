import { useMemo } from 'react';
import { parseTasks, parseCaptures, parseWikilinks } from '../utils/contentParsers';

/**
 * useDayStats - Parse content to extract stats for the insights panel.
 *
 * @param {string|null} content - Daily note content
 * @returns {{ tasks, captures, wikilinks, mood }}
 */
export function useDayStats(content) {
  return useMemo(() => {
    if (!content) {
      return {
        tasks: [],
        captures: [],
        wikilinks: [],
        mood: null,
        wordCount: 0,
      };
    }

    const tasks = parseTasks(content);
    const captures = parseCaptures(content);
    const wikilinks = parseWikilinks(content);

    // Extract mood from "Mood: emoji" line
    const moodMatch = content.match(/^Mood:\s*(.+)$/m);
    const mood = moodMatch ? moodMatch[1].trim() : null;

    // Word count (exclude markdown syntax)
    const plainText = content
      .replace(/^#+\s/gm, '')
      .replace(/[-*]\s*\[[ xX]\]/g, '')
      .replace(/\[\[([^\]]+)\]\]/g, '$1')
      .replace(/#[a-zA-Z][a-zA-Z0-9_-]*/g, '');
    const wordCount = plainText.split(/\s+/).filter(w => w.length > 0).length;

    return { tasks, captures, wikilinks, mood, wordCount };
  }, [content]);
}

export default useDayStats;
