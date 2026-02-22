import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FiFileText, FiPlus } from 'react-icons/fi';
import useDebounce from '../../hooks/useDebounce';
import { API_URL } from '../../utils/api';
import './WikilinkAutocomplete.css';

/**
 * Wikilink autocomplete dropdown
 *
 * Features:
 * - Triggered by [[ in markdown editor
 * - Fuzzy search through existing notes
 * - Create new note if not found
 * - Keyboard navigation (arrow keys, Enter, Esc)
 * - Shows recent notes if query is empty
 */
function WikilinkAutocomplete({ query, onSelect, onClose, position }) {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [showCreateOption, setShowCreateOption] = useState(false);

  const listRef = useRef(null);
  const debouncedQuery = useDebounce(query, 300);

  // Fetch matching notes
  useEffect(() => {
    const fetchNotes = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('token');
        const url = debouncedQuery
          ? `${API_URL}/search/fulltext?q=${encodeURIComponent(debouncedQuery)}&limit=10`
          : `${API_URL}/notes/?limit=10`; // Recent notes

        const response = await fetch(url, {
          headers: { 'Authorization': `Bearer ${token}` },
        });

        if (response.ok) {
          const data = await response.json();
          // Handle both search results and regular notes list
          const notesList = Array.isArray(data) ? data : data.results || [];
          setNotes(notesList);

          // Show "Create new" option if query doesn't match any titles exactly
          const exactMatch = notesList.some(
            note => note.title.toLowerCase() === debouncedQuery.toLowerCase()
          );
          setShowCreateOption(debouncedQuery.length > 0 && !exactMatch);
        }
      } catch (error) {
        console.error('Error fetching notes:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchNotes();
  }, [debouncedQuery]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      const totalItems = notes.length + (showCreateOption ? 1 : 0);

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % totalItems);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + totalItems) % totalItems);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        handleSelect();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [notes, selectedIndex, showCreateOption]);

  // Scroll selected item into view
  useEffect(() => {
    if (listRef.current) {
      const selectedElement = listRef.current.children[selectedIndex];
      if (selectedElement) {
        selectedElement.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [selectedIndex]);

  // Handle selection
  const handleSelect = useCallback(() => {
    if (selectedIndex < notes.length) {
      // Select existing note
      onSelect(notes[selectedIndex]);
    } else if (showCreateOption) {
      // Create new note
      onSelect({
        title: query,
        content: '',
        isNew: true,
      });
    }
  }, [notes, selectedIndex, showCreateOption, query, onSelect]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (listRef.current && !listRef.current.contains(e.target)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  if (notes.length === 0 && !loading && !showCreateOption) {
    return null;
  }

  return (
    <div
      className="wikilink-autocomplete"
      style={{
        position: 'fixed',
        top: position.top,
        left: position.left,
      }}
    >
      {loading && (
        <div className="autocomplete-loading">
          <div className="loading-spinner-small"></div>
          <span>Searching...</span>
        </div>
      )}

      {!loading && (
        <>
          <div className="autocomplete-header">
            <span className="autocomplete-title">
              {query ? `Search: "${query}"` : 'Recent Notes'}
            </span>
            <span className="autocomplete-hint">↑↓ to navigate, Enter to select, Esc to close</span>
          </div>

          <div className="autocomplete-list" ref={listRef}>
            {notes.map((note, index) => (
              <div
                key={note.id}
                className={`autocomplete-item ${selectedIndex === index ? 'selected' : ''}`}
                onClick={() => {
                  setSelectedIndex(index);
                  handleSelect();
                }}
              >
                <FiFileText className="item-icon" />
                <div className="item-content">
                  <div className="item-title">{note.title}</div>
                  {note.content && (
                    <div className="item-snippet">
                      {note.content.substring(0, 80)}...
                    </div>
                  )}
                </div>
                {note.tags && note.tags.length > 0 && (
                  <div className="item-tags">
                    {note.tags.slice(0, 2).map((tag, idx) => (
                      <span key={idx} className="tag-badge">
                        {typeof tag === 'string' ? tag : tag.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {showCreateOption && (
              <div
                className={`autocomplete-item create-new ${
                  selectedIndex === notes.length ? 'selected' : ''
                }`}
                onClick={() => {
                  setSelectedIndex(notes.length);
                  handleSelect();
                }}
              >
                <FiPlus className="item-icon create-icon" />
                <div className="item-content">
                  <div className="item-title">
                    Create new note: <strong>"{query}"</strong>
                  </div>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default WikilinkAutocomplete;
