import { useState, useEffect, useCallback } from 'react';
import { format } from 'date-fns';
import { api } from '../../../utils/api';

/**
 * useDailyNote - Fetches or creates the daily note for a given date.
 * Uses the api utility for proper CSRF + cookie-based auth.
 *
 * @param {Date} date - Date to fetch note for (defaults to today)
 * @returns {Object} { dailyNote, isLoading, error, refetch, appendContent, updateContent, toggleCheckbox, isToday }
 */
export function useDailyNote(date = new Date()) {
  const [dailyNote, setDailyNote] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const dateStr = format(date, 'yyyy-MM-dd');
  const isToday = format(new Date(), 'yyyy-MM-dd') === dateStr;

  // Fetch or create the daily note
  const fetchDailyNote = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      let data;

      if (isToday) {
        // For today, use POST to create if not exists
        data = await api.post('/buckets/daily/today');
      } else {
        // For other dates, use GET (handle 404 gracefully)
        const response = await api.fetch(`/buckets/daily/${dateStr}`, {
          method: 'GET',
        });

        if (!response.ok) {
          if (response.status === 404) {
            setDailyNote(null);
            return;
          }
          throw new Error('Failed to fetch daily note');
        }
        data = await response.json();
      }

      setDailyNote(data);
    } catch (err) {
      // 404 from api.post means no note (shouldn't happen for today, but handle it)
      if (err.status === 404) {
        setDailyNote(null);
        return;
      }
      if (process.env.NODE_ENV === 'development') {
        console.error('Error fetching daily note:', err);
      }
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [dateStr, isToday]);

  // Append content to the daily note (adds timestamped entry)
  const appendContent = useCallback(async (type, content) => {
    if (!dailyNote?.id) {
      throw new Error('No daily note to append to');
    }

    const timestamp = format(new Date(), 'HH:mm');
    let entry;

    if (type === 'todo') {
      entry = `- [ ] [${timestamp}] ${content}`;
    } else {
      entry = `- [${timestamp}] ${content}`;
    }

    const currentContent = dailyNote.content || '';
    const updatedContent = currentContent
      ? `${currentContent}\n${entry}`
      : `## Captures\n\n${entry}`;

    const updatedNote = await api.put(`/notes/${dailyNote.id}`, {
      title: dailyNote.title,
      content: updatedContent,
      html_content: null,
    });

    setDailyNote(updatedNote);
    return updatedNote;
  }, [dailyNote]);

  // Update the entire content (for editor saves, mood, etc.)
  const updateContent = useCallback(async (newContent) => {
    if (!dailyNote?.id) {
      throw new Error('No daily note to update');
    }

    const updatedNote = await api.put(`/notes/${dailyNote.id}`, {
      title: dailyNote.title,
      content: newContent,
    });

    setDailyNote(updatedNote);
    return updatedNote;
  }, [dailyNote]);

  // Toggle a checkbox in the content by matching the line content
  const toggleCheckbox = useCallback(async (lineIdentifier, checked) => {
    if (!dailyNote?.id || !dailyNote?.content) {
      return;
    }

    const lines = dailyNote.content.split('\n');
    let foundMatch = false;

    const updatedLines = lines.map((line) => {
      const checkboxMatch = line.match(/^(\s*-\s*)\[([ xX])\](.*)$/);
      if (checkboxMatch && !foundMatch) {
        if (typeof lineIdentifier === 'string' && line.includes(lineIdentifier)) {
          const [, prefix, , rest] = checkboxMatch;
          foundMatch = true;
          return `${prefix}[${checked ? 'x' : ' '}]${rest}`;
        }
      }
      return line;
    });

    if (!foundMatch) return;

    const updatedContent = updatedLines.join('\n');

    const updatedNote = await api.put(`/notes/${dailyNote.id}`, {
      title: dailyNote.title,
      content: updatedContent,
      html_content: null,
    });

    setDailyNote(updatedNote);
    return updatedNote;
  }, [dailyNote]);

  // Fetch on mount and when date changes
  useEffect(() => {
    fetchDailyNote();
  }, [fetchDailyNote]);

  return {
    dailyNote,
    isLoading,
    error,
    refetch: fetchDailyNote,
    appendContent,
    updateContent,
    toggleCheckbox,
    isToday,
  };
}

export default useDailyNote;
