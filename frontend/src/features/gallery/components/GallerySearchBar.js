import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  Search,
  X,
  Sparkles,
  FileText,
  SlidersHorizontal
} from 'lucide-react';
import './GallerySearchBar.css';

/**
 * GallerySearchBar - Immich-style search bar for gallery
 * Features: Text search, search type toggle, keyboard shortcuts
 */
function GallerySearchBar({
  onSearch,
  onClear,
  isSearching,
  searchType,
  onSearchTypeChange,
  resultCount
}) {
  const [query, setQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef(null);
  const debounceRef = useRef(null);

  // Search types
  const searchTypes = [
    { id: 'smart', label: 'Smart', icon: Sparkles, description: 'AI-powered semantic search' },
    { id: 'text', label: 'Text', icon: FileText, description: 'Search filename & description' }
  ];

  // Debounced search
  const handleInputChange = useCallback((e) => {
    const value = e.target.value;
    setQuery(value);

    // Clear previous debounce
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    // Debounce search by 300ms
    debounceRef.current = setTimeout(() => {
      if (value.trim()) {
        onSearch(value.trim());
      } else {
        onClear();
      }
    }, 300);
  }, [onSearch, onClear]);

  // Clear search
  const handleClear = useCallback(() => {
    setQuery('');
    onClear();
    inputRef.current?.focus();
  }, [onClear]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+K to focus search
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
      // Escape to clear and blur
      if (e.key === 'Escape' && document.activeElement === inputRef.current) {
        if (query) {
          handleClear();
        } else {
          inputRef.current?.blur();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [query, handleClear]);

  // Cleanup debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  return (
    <div className={`gallery-search-bar ${isFocused ? 'focused' : ''}`}>
      {/* Search Input */}
      <div className="search-input-container">
        <Search size={18} className="search-icon" />
        <input
          ref={inputRef}
          type="text"
          className="search-input"
          placeholder="Search photos... (Ctrl+K)"
          value={query}
          onChange={handleInputChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
        />
        {isSearching && (
          <div className="search-spinner" />
        )}
        {query && !isSearching && (
          <button className="search-clear-btn" onClick={handleClear}>
            <X size={16} />
          </button>
        )}
      </div>

      {/* Search Type Toggle */}
      <div className="search-type-toggle">
        {searchTypes.map((type) => {
          const Icon = type.icon;
          const isActive = searchType === type.id;

          return (
            <button
              key={type.id}
              className={`search-type-btn ${isActive ? 'active' : ''}`}
              onClick={() => onSearchTypeChange(type.id)}
              title={type.description}
            >
              <Icon size={14} />
              <span>{type.label}</span>
            </button>
          );
        })}
      </div>

      {/* Result Count (when searching) */}
      {query && resultCount !== undefined && (
        <div className="search-result-count">
          {resultCount} {resultCount === 1 ? 'result' : 'results'}
        </div>
      )}
    </div>
  );
}

export default GallerySearchBar;
