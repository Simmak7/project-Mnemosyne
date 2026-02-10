import React from 'react';
import { FiSearch, FiX, FiFilter } from 'react-icons/fi';

/**
 * Search header with input and controls
 */
function SearchHeader({
  searchInputRef,
  query,
  setQuery,
  showFilters,
  setShowFilters,
  onClear,
  onClose,
  onSubmit,
}) {
  return (
    <div className="search-header">
      <form onSubmit={onSubmit} className="search-form">
        <FiSearch className="search-icon" />
        <input
          ref={searchInputRef}
          type="text"
          className="search-input"
          placeholder="Search notes, tags, and images..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoComplete="off"
        />
        {query && (
          <button
            type="button"
            className="search-clear"
            onClick={onClear}
            aria-label="Clear search"
          >
            <FiX />
          </button>
        )}
      </form>

      <button
        className={`filter-toggle-btn ${showFilters ? 'active' : ''}`}
        onClick={() => setShowFilters(!showFilters)}
        aria-label="Toggle filters"
      >
        <FiFilter />
      </button>

      <button
        className="search-close"
        onClick={onClose}
        aria-label="Close search"
      >
        <FiX />
      </button>
    </div>
  );
}

export default SearchHeader;
