import React, { useCallback } from 'react';
import SearchResults from '../SearchResults';
import FilterChips from '../FilterChips';
import { useSearchState } from './hooks';
import { SearchHeader, SearchFilters, SearchHistory } from './components';
import '../UnifiedSearch.css';

/**
 * Unified search interface with keyboard shortcuts
 */
function UnifiedSearch({ isOpen, onClose, onResultClick }) {
  const {
    query,
    setQuery,
    searchMode,
    setSearchMode,
    filters,
    setFilters,
    sortBy,
    setSortBy,
    showFilters,
    setShowFilters,
    results,
    loading,
    searchHistory,
    searchInputRef,
    saveToHistory,
    handleClear,
    handleRemoveFilter,
  } = useSearchState(isOpen, onClose);

  // Handle search submission
  const handleSearch = useCallback((e) => {
    e.preventDefault();
    if (query.trim()) {
      saveToHistory(query);
    }
  }, [query, saveToHistory]);

  if (!isOpen) return null;

  return (
    <div className="unified-search-overlay" onClick={onClose}>
      <div className="unified-search-container" onClick={(e) => e.stopPropagation()}>
        <SearchHeader
          searchInputRef={searchInputRef}
          query={query}
          setQuery={setQuery}
          showFilters={showFilters}
          setShowFilters={setShowFilters}
          onClear={handleClear}
          onClose={onClose}
          onSubmit={handleSearch}
        />

        {showFilters && (
          <SearchFilters
            searchMode={searchMode}
            setSearchMode={setSearchMode}
            filters={filters}
            setFilters={setFilters}
            sortBy={sortBy}
            setSortBy={setSortBy}
          />
        )}

        <FilterChips
          searchMode={searchMode}
          filters={filters}
          sortBy={sortBy}
          onRemove={handleRemoveFilter}
        />

        {query ? (
          <SearchResults
            results={results}
            loading={loading}
            query={query}
            onClose={onClose}
            onResultClick={onResultClick}
          />
        ) : (
          <SearchHistory
            searchHistory={searchHistory}
            onSelect={setQuery}
          />
        )}
      </div>
    </div>
  );
}

export default UnifiedSearch;
