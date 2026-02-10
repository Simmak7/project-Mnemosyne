import React from 'react';

/**
 * Search filters panel
 */
function SearchFilters({
  searchMode,
  setSearchMode,
  filters,
  setFilters,
  sortBy,
  setSortBy,
}) {
  return (
    <div className="search-filters">
      <div className="filter-group">
        <label className="filter-label">Search Mode:</label>
        <div className="filter-options">
          <button
            className={`filter-option ${searchMode === 'combined' ? 'active' : ''}`}
            onClick={() => setSearchMode('combined')}
          >
            Combined
          </button>
          <button
            className={`filter-option ${searchMode === 'fulltext' ? 'active' : ''}`}
            onClick={() => setSearchMode('fulltext')}
          >
            Full-Text
          </button>
          <button
            className={`filter-option ${searchMode === 'semantic' ? 'active' : ''}`}
            onClick={() => setSearchMode('semantic')}
          >
            Semantic
          </button>
        </div>
      </div>

      <div className="filter-group">
        <label className="filter-label">Type:</label>
        <div className="filter-options">
          {['all', 'notes', 'tags', 'images'].map(type => (
            <button
              key={type}
              className={`filter-option ${filters.type === type ? 'active' : ''}`}
              onClick={() => setFilters({ ...filters, type })}
            >
              {type === 'all' ? 'All' : type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="filter-group">
        <label className="filter-label">Date Range:</label>
        <div className="filter-options">
          {[
            { value: 'all', label: 'All Time' },
            { value: 'today', label: 'Today' },
            { value: 'week', label: 'This Week' },
            { value: 'month', label: 'This Month' },
          ].map(({ value, label }) => (
            <button
              key={value}
              className={`filter-option ${filters.dateRange === value ? 'active' : ''}`}
              onClick={() => setFilters({ ...filters, dateRange: value })}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="filter-group">
        <label className="filter-label">Sort By:</label>
        <div className="filter-options">
          {['relevance', 'date', 'title'].map(sort => (
            <button
              key={sort}
              className={`filter-option ${sortBy === sort ? 'active' : ''}`}
              onClick={() => setSortBy(sort)}
            >
              {sort.charAt(0).toUpperCase() + sort.slice(1)}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default SearchFilters;
