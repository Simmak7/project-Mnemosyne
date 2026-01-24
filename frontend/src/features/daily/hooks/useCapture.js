import { useState, useCallback } from 'react';

/**
 * useCapture - Handles quick capture logic including command parsing
 *
 * Commands:
 * - /todo → Creates checkbox item (task list)
 * - /img → Opens image picker (placeholder)
 * - /link → Opens note picker (wikilink)
 *
 * @param {Function} onCapture - Callback to handle captured content: (type, content) => void
 * @returns {Object} { capture, isCapturing, parseCommand }
 */
export function useCapture(onCapture) {
  const [isCapturing, setIsCapturing] = useState(false);

  /**
   * Parse text for quick commands
   * @param {string} text - Raw input text
   * @returns {Object} { type: 'text' | 'todo' | 'img' | 'link', content: string }
   */
  const parseCommand = useCallback((text) => {
    const trimmed = text.trim();

    // Check for /todo command - return raw task text, formatting done in appendContent
    if (trimmed.startsWith('/todo ')) {
      return {
        type: 'todo',
        content: trimmed.slice(6).trim(),
      };
    }

    // Check for /img command (placeholder for future)
    if (trimmed === '/img' || trimmed.startsWith('/img ')) {
      return {
        type: 'img',
        content: trimmed.slice(4).trim() || '',
      };
    }

    // Check for /link command (placeholder for future)
    if (trimmed === '/link' || trimmed.startsWith('/link ')) {
      const noteTitle = trimmed.slice(5).trim();
      if (noteTitle) {
        return {
          type: 'link',
          content: `[[${noteTitle}]]`,
        };
      }
      return {
        type: 'link',
        content: '',
      };
    }

    // Default: plain text
    return {
      type: 'text',
      content: trimmed,
    };
  }, []);

  /**
   * Capture text and call the onCapture callback
   * @param {string} text - Text to capture
   */
  const capture = useCallback(async (text) => {
    if (!text.trim() || !onCapture) return;

    setIsCapturing(true);

    try {
      const parsed = parseCommand(text);

      // Handle special command types
      if (parsed.type === 'img') {
        // TODO: Open image picker dialog
        if (process.env.NODE_ENV === 'development') {
          console.log('Image picker not yet implemented');
        }
        return;
      }

      if (parsed.type === 'link' && !parsed.content) {
        // TODO: Open note picker dialog
        if (process.env.NODE_ENV === 'development') {
          console.log('Note picker not yet implemented');
        }
        return;
      }

      // Capture the content with type information
      await onCapture(parsed.type, parsed.content);
    } catch (err) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Capture error:', err);
      }
      throw err;
    } finally {
      setIsCapturing(false);
    }
  }, [onCapture, parseCommand]);

  return {
    capture,
    isCapturing,
    parseCommand,
  };
}

export default useCapture;
