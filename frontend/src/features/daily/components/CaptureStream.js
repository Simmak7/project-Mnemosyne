import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Sparkles, Send, Loader2, FileText } from 'lucide-react';
import './CaptureStream.css';

/**
 * CaptureStream - Quick capture input for appending thoughts to daily note
 *
 * Features:
 * - Enter to capture
 * - Shift+Enter for multiline
 * - Auto-expands textarea
 * - Shows command hints
 * - Autocomplete for /link command
 */
function CaptureStream({ onCapture, disabled = false, placeholder }) {
  const [value, setValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [notes, setNotes] = useState([]);
  const [showLinkSuggestions, setShowLinkSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(0);
  const [linkSearchQuery, setLinkSearchQuery] = useState('');
  const textareaRef = useRef(null);
  const suggestionsRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [value]);

  // Fetch notes for autocomplete when typing /link
  useEffect(() => {
    const fetchNotes = async () => {
      const token = localStorage.getItem('token');
      if (!token) return;

      try {
        const response = await fetch('http://localhost:8000/notes/', {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (response.ok) {
          const data = await response.json();
          setNotes(data);
        }
      } catch (err) {
        // Silently fail - autocomplete is optional
      }
    };

    fetchNotes();
  }, []);

  // Filter notes based on search query
  const filteredNotes = useCallback(() => {
    if (!linkSearchQuery) return notes.slice(0, 8);
    const query = linkSearchQuery.toLowerCase();
    return notes
      .filter((note) => note.title.toLowerCase().includes(query))
      .slice(0, 8);
  }, [notes, linkSearchQuery]);

  // Check if typing /link command and extract search query
  useEffect(() => {
    const trimmed = value.trim().toLowerCase();
    if (trimmed.startsWith('/link')) {
      setShowLinkSuggestions(true);
      const searchPart = value.trim().slice(5).trim();
      setLinkSearchQuery(searchPart);
      setSelectedSuggestionIndex(0);
    } else {
      setShowLinkSuggestions(false);
      setLinkSearchQuery('');
    }
  }, [value]);

  // Select a note from suggestions
  const selectNote = (noteTitle) => {
    setValue(`/link ${noteTitle}`);
    setShowLinkSuggestions(false);
    textareaRef.current?.focus();
  };

  const handleSubmit = async () => {
    if (!value.trim() || disabled || isSubmitting) return;

    setIsSubmitting(true);
    try {
      await onCapture(value.trim());
      setValue('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    } catch (err) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Capture failed:', err);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e) => {
    const suggestions = filteredNotes();

    // Handle suggestions navigation
    if (showLinkSuggestions && suggestions.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedSuggestionIndex((prev) =>
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedSuggestionIndex((prev) =>
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
        return;
      }
      if (e.key === 'Tab' || (e.key === 'Enter' && !e.shiftKey)) {
        e.preventDefault();
        selectNote(suggestions[selectedSuggestionIndex].title);
        return;
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        setShowLinkSuggestions(false);
        return;
      }
    }

    // Enter without Shift submits
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleChange = (e) => {
    setValue(e.target.value);
  };

  // Detect if user is typing a command
  const isCommand = value.startsWith('/');
  const commandHint = getCommandHint(value);

  return (
    <div className={`capture-stream ng-glass ${disabled ? 'disabled' : ''}`}>
      <div className="capture-icon">
        <Sparkles size={20} />
      </div>

      <div className="capture-input-wrapper">
        <textarea
          ref={textareaRef}
          className="capture-input"
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder || "What's on your mind? Press Enter to capture..."}
          disabled={disabled || isSubmitting}
          rows={1}
          aria-label="Quick capture input"
        />

        {commandHint && (
          <div className="capture-hint">{commandHint}</div>
        )}

        {/* Link suggestions dropdown */}
        {showLinkSuggestions && filteredNotes().length > 0 && (
          <div className="capture-suggestions" ref={suggestionsRef}>
            <div className="suggestions-header">Select a note to link</div>
            {filteredNotes().map((note, index) => (
              <div
                key={note.id}
                className={`suggestion-item ${index === selectedSuggestionIndex ? 'selected' : ''}`}
                onClick={() => selectNote(note.title)}
                onMouseEnter={() => setSelectedSuggestionIndex(index)}
              >
                <FileText size={14} className="suggestion-icon" />
                <span className="suggestion-title">{note.title}</span>
              </div>
            ))}
            <div className="suggestions-hint">
              <kbd>↑↓</kbd> navigate <kbd>Tab</kbd> or <kbd>Enter</kbd> select <kbd>Esc</kbd> close
            </div>
          </div>
        )}
      </div>

      <button
        className={`capture-submit ${value.trim() ? 'active' : ''}`}
        onClick={handleSubmit}
        disabled={!value.trim() || disabled || isSubmitting}
        aria-label="Capture thought"
      >
        {isSubmitting ? (
          <Loader2 size={18} className="ng-animate-spin" />
        ) : (
          <Send size={18} />
        )}
      </button>

      {/* Keyboard hint */}
      <div className="capture-keyboard-hint">
        <kbd>Enter</kbd> to capture
        <span className="separator">|</span>
        <kbd>Shift+Enter</kbd> new line
      </div>
    </div>
  );
}

/**
 * Get hint text for commands
 */
function getCommandHint(text) {
  const trimmed = text.trim().toLowerCase();

  if (trimmed === '/') {
    return 'Commands: /todo, /link, /img';
  }

  if (trimmed.startsWith('/todo')) {
    return '/todo [task] - Create a checkbox item';
  }

  if (trimmed.startsWith('/link')) {
    return '/link [note title] - Create a wikilink';
  }

  if (trimmed.startsWith('/img')) {
    return '/img - Insert an image (coming soon)';
  }

  return null;
}

export default CaptureStream;
