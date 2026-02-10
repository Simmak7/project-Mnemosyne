/**
 * ExploreSearchBar - Search bar with node autocomplete for ExploreView
 *
 * Uses useNodeSearch to search the graph API and show a dropdown
 * of matching nodes. Selecting a result focuses on that node.
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Search, RefreshCw, FileText, Tag, Image, Sparkles } from 'lucide-react';
import { useNodeSearch } from '../hooks/useGraphData';

const NODE_ICONS = { note: FileText, tag: Tag, image: Image, media: Image, entity: Sparkles };

export function ExploreSearchBar({ onFocusNode, onRefresh, isRefreshing, onSearchResults }) {
  const [query, setQuery] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const { results, isLoading } = useNodeSearch(query);
  const containerRef = useRef(null);

  // Broadcast search results for canvas highlighting
  useEffect(() => {
    if (onSearchResults) {
      onSearchResults(query.length >= 2 ? results : []);
    }
  }, [results, query, onSearchResults]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = useCallback((node) => {
    onFocusNode(node.id);
    setQuery('');
    setShowDropdown(false);
    if (onSearchResults) onSearchResults([]);
  }, [onFocusNode, onSearchResults]);

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setShowDropdown(false);
      e.target.blur();
    }
  };

  return (
    <div className="explore-view__search" ref={containerRef}>
      <div className="explore-view__search-form">
        <Search size={16} className="explore-view__search-icon" />
        <input
          type="text"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setShowDropdown(true); }}
          onFocus={() => query.length >= 2 && setShowDropdown(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search all nodes..."
          className="explore-view__search-input"
        />
        {query && (
          <button
            type="button"
            onClick={() => { setQuery(''); setShowDropdown(false); }}
            className="explore-view__search-clear"
          >
            Clear
          </button>
        )}
      </div>

      <button
        onClick={onRefresh}
        className="explore-view__refresh"
        title="Refresh graph"
        disabled={isRefreshing}
      >
        <RefreshCw size={16} className={isRefreshing ? 'is-spinning' : ''} />
      </button>

      {/* Search Results Dropdown */}
      {showDropdown && query.length >= 2 && (
        <div className="explore-search__dropdown">
          {isLoading && (
            <div className="explore-search__loading">Searching...</div>
          )}
          {!isLoading && results.length === 0 && (
            <div className="explore-search__empty">No nodes found</div>
          )}
          {!isLoading && results.map((node) => {
            const [type] = node.id.split('-');
            const Icon = NODE_ICONS[type] || FileText;
            return (
              <button
                key={node.id}
                className="explore-search__result"
                onClick={() => handleSelect(node)}
              >
                <Icon size={14} className={`explore-search__icon explore-search__icon--${type}`} />
                <span className="explore-search__title">{node.title || node.id}</span>
                <span className="explore-search__type">{type}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default ExploreSearchBar;
