import React, { useRef, useEffect, useCallback } from 'react';
import {
  X,
  ArrowUpDown,
  LayoutList,
  LayoutGrid,
  ChevronDown
} from 'lucide-react';
import { useNoteContext } from '../hooks/NoteContext';
import './NoteSearchBar.css';

/**
 * NoteSearchBar - Search and filter controls for note list
 * Features: Search input, sort options, view mode toggle
 */
function NoteSearchBar({ resultCount, isLoading }) {
  const {
    searchQuery,
    setSearchQuery,
    sortBy,
    setSortBy,
    sortOrder,
    setSortOrder,
    viewMode,
    setViewMode
  } = useNoteContext();

  const inputRef = useRef(null);
  const debounceRef = useRef(null);

  // Sort options
  const sortOptions = [
    { id: 'created', label: 'Date Created' },
    { id: 'updated', label: 'Last Modified' },
    { id: 'title', label: 'Title A-Z' },
    { id: 'custom', label: 'Custom Order' }
  ];

  // Debounced search input
  const handleInputChange = useCallback((e) => {
    const value = e.target.value;

    // Clear previous debounce
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    // Debounce search by 200ms
    debounceRef.current = setTimeout(() => {
      setSearchQuery(value);
    }, 200);
  }, [setSearchQuery]);

  // Clear search
  const handleClear = useCallback(() => {
    setSearchQuery('');
    if (inputRef.current) {
      inputRef.current.value = '';
      inputRef.current.focus();
    }
  }, [setSearchQuery]);

  // Handle sort change
  const handleSortChange = useCallback((e) => {
    const newSortBy = e.target.value;
    setSortBy(newSortBy);
    // Title defaults to ascending, dates to descending
    setSortOrder(newSortBy === 'title' ? 'asc' : 'desc');
  }, [setSortBy, setSortOrder]);

  // Toggle sort order
  const toggleSortOrder = useCallback(() => {
    setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
  }, [sortOrder, setSortOrder]);

  // Toggle view mode
  const toggleViewMode = useCallback(() => {
    setViewMode(viewMode === 'list' ? 'grid' : 'list');
  }, [viewMode, setViewMode]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      const activeElement = document.activeElement;
      const tagName = activeElement?.tagName?.toLowerCase();
      const isEditable = activeElement?.isContentEditable;
      const isFormElement = ['input', 'textarea', 'select'].includes(tagName);
      const isInEditor = activeElement?.closest?.('.ng-block-editor, .tiptap, .ProseMirror, [contenteditable="true"]');

      // Focus search on / key (when not typing in any editable area)
      if (e.key === '/' && !isFormElement && !isEditable && !isInEditor) {
        e.preventDefault();
        inputRef.current?.focus();
      }
      // Escape to clear and blur
      if (e.key === 'Escape' && activeElement === inputRef.current) {
        if (searchQuery) {
          handleClear();
        } else {
          inputRef.current?.blur();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [searchQuery, handleClear]);

  // Cleanup debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  return (
    <div className="note-search-bar">
      {/* Search Input */}
      <div className="search-input-wrapper">
        <input
          ref={inputRef}
          type="text"
          className="search-input"
          placeholder="Search notes... (press /)"
          defaultValue={searchQuery}
          onChange={handleInputChange}
        />
        {isLoading && <div className="search-spinner" />}
        {searchQuery && !isLoading && (
          <button className="search-clear" onClick={handleClear} title="Clear search">
            <X size={14} />
          </button>
        )}
      </div>

      {/* Controls Row */}
      <div className="search-controls">
        {/* Result count */}
        <span className="search-result-count">
          {resultCount} note{resultCount !== 1 ? 's' : ''}
        </span>

        <div className="search-controls-right">
          {/* Sort dropdown */}
          <div className="sort-control">
            <select
              value={sortBy}
              onChange={handleSortChange}
              className="sort-select"
            >
              {sortOptions.map(option => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>
            <ChevronDown size={14} className="sort-chevron" />
            <button
              className="sort-order-btn"
              onClick={toggleSortOrder}
              title={`Sort ${sortOrder === 'desc' ? 'descending' : 'ascending'}`}
            >
              <ArrowUpDown
                size={14}
                className={sortOrder === 'asc' ? 'flipped' : ''}
              />
            </button>
          </div>

          {/* View mode toggle */}
          <button
            className={`view-mode-btn ${viewMode}`}
            onClick={toggleViewMode}
            title={viewMode === 'list' ? 'Switch to grid view' : 'Switch to list view'}
          >
            {viewMode === 'list' ? (
              <LayoutGrid size={16} />
            ) : (
              <LayoutList size={16} />
            )}
          </button>
        </div>
      </div>

      {/* Custom order hint */}
      {sortBy === 'custom' && (
        <div className="custom-order-hint">
          Drag notes to reorder
        </div>
      )}
    </div>
  );
}

export default NoteSearchBar;
