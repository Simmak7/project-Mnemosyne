import React from 'react';
import { FiX } from 'react-icons/fi';
import './FilterChips.css';

/**
 * Active filter chips display
 *
 * Features:
 * - Shows active filters as removable chips
 * - Click to remove filter
 * - Clear all button
 * - Visual indicator of applied filters
 */
function FilterChips({ searchMode, filters, sortBy, onRemove }) {
  const activeFilters = [];

  // Add search mode chip (if not default)
  if (searchMode !== 'combined') {
    activeFilters.push({
      id: 'searchMode',
      label: `Mode: ${searchMode}`,
      value: searchMode,
    });
  }

  // Add type filter chip (if not default)
  if (filters.type !== 'all') {
    activeFilters.push({
      id: 'type',
      label: `Type: ${filters.type}`,
      value: filters.type,
    });
  }

  // Add date range chip (if not default)
  if (filters.dateRange !== 'all') {
    const dateLabels = {
      today: 'Today',
      week: 'This Week',
      month: 'This Month',
      year: 'This Year',
    };
    activeFilters.push({
      id: 'dateRange',
      label: `Date: ${dateLabels[filters.dateRange] || filters.dateRange}`,
      value: filters.dateRange,
    });
  }

  // Add sort by chip (if not default)
  if (sortBy !== 'relevance') {
    activeFilters.push({
      id: 'sortBy',
      label: `Sort: ${sortBy}`,
      value: sortBy,
    });
  }

  // Don't render if no active filters
  if (activeFilters.length === 0) {
    return null;
  }

  const handleClearAll = () => {
    activeFilters.forEach((filter) => {
      onRemove(filter.id);
    });
  };

  return (
    <div className="filter-chips-container">
      <div className="filter-chips-label">Active Filters:</div>

      <div className="filter-chips-list">
        {activeFilters.map((filter) => (
          <button
            key={filter.id}
            className="filter-chip"
            onClick={() => onRemove(filter.id)}
            aria-label={`Remove ${filter.label} filter`}
          >
            <span className="filter-chip-label">{filter.label}</span>
            <FiX className="filter-chip-remove" />
          </button>
        ))}

        {activeFilters.length > 1 && (
          <button
            className="filter-chip clear-all"
            onClick={handleClearAll}
            aria-label="Clear all filters"
          >
            <span className="filter-chip-label">Clear All</span>
            <FiX className="filter-chip-remove" />
          </button>
        )}
      </div>
    </div>
  );
}

export default FilterChips;
