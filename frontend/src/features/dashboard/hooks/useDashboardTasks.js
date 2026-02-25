/**
 * useDashboardTasks - Fetches open tasks from recent daily notes
 *
 * Reuses parseTasks() from journal utils for markdown checkbox parsing.
 * API: GET /buckets/daily?days=30 for daily note entries, PUT /notes/{id} for toggling.
 */
import { useState, useEffect, useCallback } from 'react';
import { api } from '../../../utils/api';
import { parseTasks } from '../../journal/utils/contentParsers';

export function useDashboardTasks() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchTasks = useCallback(async () => {
    try {
      const res = await api.get('/buckets/daily?days=30');
      const notes = Array.isArray(res) ? res : res?.notes;
      if (!Array.isArray(notes)) return;

      const allTasks = [];
      for (const note of notes) {
        if (!note.content) continue;
        const parsed = parseTasks(note.content);
        parsed.forEach(task => {
          allTasks.push({
            ...task,
            noteId: note.id,
            noteTitle: note.title,
            noteContent: note.content,
          });
        });
      }
      setTasks(allTasks);
    } catch {
      // silently fail - widget shows empty
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchTasks(); }, [fetchTasks]);

  const toggleTask = useCallback(async (task) => {
    const { noteId, noteContent, text, checked } = task;
    // Replace the checkbox line in content
    const oldMark = checked ? '[x]' : '[ ]';
    const newMark = checked ? '[ ]' : '[x]';
    const pattern = new RegExp(
      `(- ${oldMark.replace('[', '\\[').replace(']', '\\]')}\\s*)${text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`
    );
    const updatedContent = noteContent.replace(pattern, `- ${newMark} ${text}`);

    if (updatedContent === noteContent) return;

    try {
      await api.put(`/notes/${noteId}`, { content: updatedContent });
      // Optimistically update local state
      setTasks(prev => prev.map(t =>
        t.noteId === noteId && t.text === text
          ? { ...t, checked: !checked, noteContent: updatedContent }
          : t
      ));
    } catch {
      // revert on failure
    }
  }, []);

  const openTasks = tasks.filter(t => !t.checked);
  return { tasks: openTasks, allTasks: tasks, loading, toggleTask, refetch: fetchTasks };
}

export default useDashboardTasks;
