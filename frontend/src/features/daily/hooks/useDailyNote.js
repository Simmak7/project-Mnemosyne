import { useState, useEffect, useCallback } from 'react';
import { format } from 'date-fns';

/**
 * useDailyNote - Fetches or creates the daily note for a given date
 *
 * @param {Date} date - Date to fetch note for (defaults to today)
 * @returns {Object} { dailyNote, isLoading, error, refetch, appendContent, updateContent }
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

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      let response;

      if (isToday) {
        // For today, use POST to create if not exists
        response = await fetch('http://localhost:8000/buckets/daily/today', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      } else {
        // For other dates, use GET
        response = await fetch(`http://localhost:8000/buckets/daily/${dateStr}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      }

      if (!response.ok) {
        if (response.status === 404) {
          // No note for this date
          setDailyNote(null);
          return;
        }
        throw new Error('Failed to fetch daily note');
      }

      const data = await response.json();
      setDailyNote(data);
    } catch (err) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Error fetching daily note:', err);
      }
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [dateStr, isToday]);

  // Append content to the daily note (adds timestamped entry)
  // @param {string} type - Content type: 'text', 'todo', 'link'
  // @param {string} content - The content to append
  const appendContent = useCallback(async (type, content) => {
    if (!dailyNote?.id) {
      throw new Error('No daily note to append to');
    }

    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    // Create timestamped entry based on type
    const timestamp = format(new Date(), 'HH:mm');
    let entry;

    if (type === 'todo') {
      // Task list item - markdown format with checkbox
      entry = `- [ ] [${timestamp}] ${content}`;
    } else {
      // Regular text entry
      entry = `- [${timestamp}] ${content}`;
    }

    // Append to existing content
    const currentContent = dailyNote.content || '';
    const updatedContent = currentContent
      ? `${currentContent}\n${entry}`
      : `## Captures\n\n${entry}`;

    // Build request body - always use markdown, clear html_content
    const requestBody = {
      title: dailyNote.title,
      content: updatedContent,
      html_content: null, // Clear HTML to force markdown rendering
    };

    const response = await fetch(`http://localhost:8000/notes/${dailyNote.id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error('Failed to append to daily note');
    }

    const updatedNote = await response.json();
    setDailyNote(updatedNote);
    return updatedNote;
  }, [dailyNote]);

  // Update the entire content (for editor saves)
  const updateContent = useCallback(async (newContent) => {
    if (!dailyNote?.id) {
      throw new Error('No daily note to update');
    }

    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`http://localhost:8000/notes/${dailyNote.id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: dailyNote.title,
        content: newContent,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to update daily note');
    }

    const updatedNote = await response.json();
    setDailyNote(updatedNote);
    return updatedNote;
  }, [dailyNote]);

  // Toggle a checkbox in the content by matching the line content
  // lineIdentifier: the text content of the list item (e.g., "[09:52] wash dishes")
  const toggleCheckbox = useCallback(async (lineIdentifier, checked) => {
    if (!dailyNote?.id || !dailyNote?.content) {
      return;
    }

    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const lines = dailyNote.content.split('\n');
    let foundMatch = false;

    const updatedLines = lines.map((line) => {
      // Match checkbox patterns: - [ ] or - [x]
      const checkboxMatch = line.match(/^(\s*-\s*)\[([ xX])\](.*)$/);
      if (checkboxMatch && !foundMatch) {
        // If lineIdentifier is a string, match by content
        if (typeof lineIdentifier === 'string') {
          // Match if the line contains the identifier (timestamp + text)
          if (line.includes(lineIdentifier)) {
            const [, prefix, , rest] = checkboxMatch;
            foundMatch = true;
            return `${prefix}[${checked ? 'x' : ' '}]${rest}`;
          }
        }
      }
      return line;
    });

    if (!foundMatch) {
      return;
    }

    const updatedContent = updatedLines.join('\n');

    const response = await fetch(`http://localhost:8000/notes/${dailyNote.id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: dailyNote.title,
        content: updatedContent,
        html_content: null,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to toggle checkbox');
    }

    const updatedNote = await response.json();
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
