import { useMemo } from 'react';
import { parseTasks } from '../utils/contentParsers';

// Template/placeholder task texts to exclude
const TEMPLATE_TASKS = new Set([
  'add your tasks here...',
  'add your tasks here',
]);

/**
 * useOpenTasks - Collects all uncompleted tasks across journal entries.
 * Filters out template/placeholder tasks from the daily note template.
 *
 * @param {Array} entries - Array of daily note entries from useJournalEntries
 * @returns {{ openTasks: Array, allTasks: Array }}
 */
export function useOpenTasks(entries) {
  return useMemo(() => {
    if (!entries || entries.length === 0) {
      return { openTasks: [], allTasks: [] };
    }

    const allTasks = [];

    for (const entry of entries) {
      if (!entry.content) continue;
      const tasks = parseTasks(entry.content);
      const dateStr = entry.date || entry.title?.replace('Daily Note - ', '');

      for (const task of tasks) {
        // Skip template/placeholder tasks
        if (TEMPLATE_TASKS.has(task.text.toLowerCase())) continue;
        // Skip empty tasks
        if (!task.text.trim()) continue;

        allTasks.push({
          text: task.text,
          checked: task.checked,
          date: dateStr,
          noteId: entry.id,
        });
      }
    }

    const openTasks = allTasks.filter(t => !t.checked);

    // Sort by date descending (most recent first)
    openTasks.sort((a, b) => (b.date || '').localeCompare(a.date || ''));

    return { openTasks, allTasks };
  }, [entries]);
}

export default useOpenTasks;
