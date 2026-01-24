import React from 'react';
import { FiSearch, FiRefreshCw, FiFilter } from 'react-icons/fi';
import './GraphControls.css';

/**
 * Control panel for knowledge graph
 *
 * Features:
 * - Search bar with real-time filtering
 * - Toggle filters (notes, tags, images, link types)
 * - Refresh button
 * - Node/link count display
 */
function GraphControls({
  searchTerm,
  onSearch,
  filters,
  onFilterChange,
  onRefresh,
  nodeCount,
  linkCount,
}) {
  const [showFilters, setShowFilters] = React.useState(false);

  const handleFilterToggle = (filterKey) => {
    onFilterChange({
      ...filters,
      [filterKey]: !filters[filterKey],
    });
  };

  return (
    <div className="graph-controls">
      <div className="graph-controls-left">
        {/* Search bar */}
        <div className="graph-search">
          <FiSearch className="search-icon" aria-hidden="true" />
          <input
            type="text"
            placeholder="Search nodes..."
            value={searchTerm}
            onChange={(e) => onSearch(e.target.value)}
            className="search-input"
            aria-label="Search graph nodes"
          />
          {searchTerm && (
            <button
              className="clear-search"
              onClick={() => onSearch('')}
              aria-label="Clear search"
            >
              ×
            </button>
          )}
        </div>

        {/* Filter toggle */}
        <button
          className={`filter-toggle ${showFilters ? 'active' : ''}`}
          onClick={() => setShowFilters(!showFilters)}
          aria-label="Toggle filters"
        >
          <FiFilter />
          Filters
        </button>

        {/* Refresh button */}
        <button
          className="refresh-button"
          onClick={onRefresh}
          aria-label="Refresh graph"
        >
          <FiRefreshCw />
        </button>
      </div>

      <div className="graph-controls-right">
        {/* Stats */}
        <div className="graph-stats">
          <span className="stat">
            <strong>{nodeCount}</strong> nodes
          </span>
          <span className="stat-divider">•</span>
          <span className="stat">
            <strong>{linkCount}</strong> links
          </span>
        </div>
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="filter-panel">
          <div className="filter-section">
            <h4>Node Types</h4>
            <label className="filter-checkbox">
              <input
                type="checkbox"
                checked={filters.showNotes}
                onChange={() => handleFilterToggle('showNotes')}
              />
              <span className="filter-label">
                <span className="node-indicator note"></span>
                Notes
              </span>
            </label>
            <label className="filter-checkbox">
              <input
                type="checkbox"
                checked={filters.showTags}
                onChange={() => handleFilterToggle('showTags')}
              />
              <span className="filter-label">
                <span className="node-indicator tag"></span>
                Tags
              </span>
            </label>
            <label className="filter-checkbox">
              <input
                type="checkbox"
                checked={filters.showImages}
                onChange={() => handleFilterToggle('showImages')}
              />
              <span className="filter-label">
                <span className="node-indicator image"></span>
                Images
              </span>
            </label>
          </div>

          <div className="filter-section">
            <h4>Link Types</h4>
            <label className="filter-checkbox">
              <input
                type="checkbox"
                checked={filters.showWikilinks}
                onChange={() => handleFilterToggle('showWikilinks')}
              />
              <span className="filter-label">
                <span className="link-indicator wikilink"></span>
                Wikilinks
              </span>
            </label>
            <label className="filter-checkbox">
              <input
                type="checkbox"
                checked={filters.showTagLinks}
                onChange={() => handleFilterToggle('showTagLinks')}
              />
              <span className="filter-label">
                <span className="link-indicator tag-link"></span>
                Tag Links
              </span>
            </label>
            <label className="filter-checkbox">
              <input
                type="checkbox"
                checked={filters.showImageLinks}
                onChange={() => handleFilterToggle('showImageLinks')}
              />
              <span className="filter-label">
                <span className="link-indicator image-link"></span>
                Image Links
              </span>
            </label>
          </div>
        </div>
      )}
    </div>
  );
}

export default GraphControls;
