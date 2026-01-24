import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FiSearch, FiX, FiFilter } from 'react-icons/fi';
import useDebounce from '../../hooks/useDebounce';
import SearchResults from './SearchResults';
import FilterChips from './FilterChips';
import './UnifiedSearch.css';

/**
 * Unified search interface with keyboard shortcuts
 *
 * Features:
 * - Global keyboard shortcut (Cmd/Ctrl+K)
 * - Multi-modal search (full-text, semantic, combined)
 * - Filter by type (notes, tags, images)
 * - Date range filtering
 * - Sort options (relevance, date, title)
 * - Search history
 */
function UnifiedSearch({ isOpen, onClose, onResultClick }) {
  const [query, setQuery] = useState('');
  const [searchMode, setSearchMode] = useState('combined'); // fulltext, semantic, combined
  const [filters, setFilters] = useState({
    type: 'all', // all, notes, tags, images
    dateRange: 'all', // all, today, week, month, year
  });
  const [sortBy, setSortBy] = useState('relevance'); // relevance, date, title
  const [showFilters, setShowFilters] = useState(false);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchHistory, setSearchHistory] = useState([]);

  const searchInputRef = useRef(null);
  const debouncedQuery = useDebounce(query, 300);

  // Load search history from localStorage
  useEffect(() => {
    const history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
    setSearchHistory(history);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  // Global keyboard shortcut (Cmd/Ctrl+K)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) {
          onClose();
        } else {
          // This would be triggered from parent component
        }
      }

      // Escape to close
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Perform search
  useEffect(() => {
    if (!debouncedQuery) {
      setResults([]);
      return;
    }

    const performSearch = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('token');

        // Build search URL with filters
        // Note: The backend /search/fulltext endpoint handles combined search
        const params = new URLSearchParams({
          q: debouncedQuery,
          type: filters.type,
          date_range: filters.dateRange,
          sort_by: sortBy,
          limit: '50'
        });

        const url = `http://localhost:8000/search/fulltext?${params.toString()}`;

        const response = await fetch(url, {
          headers: { 'Authorization': `Bearer ${token}` },
        });

        console.log('Search request URL:', url);
        console.log('Token present:', !!token);

        if (response.ok) {
          const data = await response.json();
          console.log('Search response:', data);
          let searchResults = data.results || [];

          // Results are already filtered and sorted by backend
          setResults(searchResults);
        } else {
          const errorText = await response.text();
          console.error('Search failed!');
          console.error('Status:', response.status);
          console.error('Status Text:', response.statusText);
          console.error('Response:', errorText);
          console.error('URL was:', url);
        }
      } catch (error) {
        console.error('Error performing search:', error);
        console.error('Error details:', error.message, error.stack);
      } finally {
        setLoading(false);
      }
    };

    performSearch();
  }, [debouncedQuery, searchMode, filters, sortBy]);

  // Apply filters to results
  const applyFilters = useCallback((results) => {
    let filtered = [...results];

    // Filter by type
    if (filters.type !== 'all') {
      filtered = filtered.filter(item => {
        if (filters.type === 'notes') return item.title !== undefined;
        if (filters.type === 'tags') return item.name !== undefined && !item.filename;
        if (filters.type === 'images') return item.filename !== undefined;
        return true;
      });
    }

    // Filter by date range
    if (filters.dateRange !== 'all') {
      const now = new Date();
      const cutoffDate = new Date();

      switch (filters.dateRange) {
        case 'today':
          cutoffDate.setHours(0, 0, 0, 0);
          break;
        case 'week':
          cutoffDate.setDate(now.getDate() - 7);
          break;
        case 'month':
          cutoffDate.setMonth(now.getMonth() - 1);
          break;
        case 'year':
          cutoffDate.setFullYear(now.getFullYear() - 1);
          break;
        default:
          break;
      }

      filtered = filtered.filter(item => {
        const itemDate = new Date(item.created_at || item.uploaded_at);
        return itemDate >= cutoffDate;
      });
    }

    return filtered;
  }, [filters]);

  // Apply sorting to results
  const applySorting = useCallback((results) => {
    const sorted = [...results];

    switch (sortBy) {
      case 'date':
        sorted.sort((a, b) => {
          const dateA = new Date(a.created_at || a.uploaded_at || 0);
          const dateB = new Date(b.created_at || b.uploaded_at || 0);
          return dateB - dateA; // Newest first
        });
        break;
      case 'title':
        sorted.sort((a, b) => {
          const titleA = (a.title || a.name || a.filename || '').toLowerCase();
          const titleB = (b.title || b.name || b.filename || '').toLowerCase();
          return titleA.localeCompare(titleB);
        });
        break;
      case 'relevance':
      default:
        // Keep original order (sorted by relevance from API)
        break;
    }

    return sorted;
  }, [sortBy]);

  // Save to search history
  const saveToHistory = useCallback((searchQuery) => {
    if (!searchQuery.trim()) return;

    const history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
    const newHistory = [searchQuery, ...history.filter(q => q !== searchQuery)].slice(0, 10);
    localStorage.setItem('searchHistory', JSON.stringify(newHistory));
    setSearchHistory(newHistory);
  }, []);

  // Handle search submission
  const handleSearch = useCallback((e) => {
    e.preventDefault();
    if (query.trim()) {
      saveToHistory(query);
    }
  }, [query, saveToHistory]);

  // Clear search
  const handleClear = () => {
    setQuery('');
    setResults([]);
    searchInputRef.current?.focus();
  };

  // Remove filter
  const handleRemoveFilter = (filterType) => {
    if (filterType === 'type') {
      setFilters({ ...filters, type: 'all' });
    } else if (filterType === 'dateRange') {
      setFilters({ ...filters, dateRange: 'all' });
    } else if (filterType === 'searchMode') {
      setSearchMode('combined');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="unified-search-overlay" onClick={onClose}>
      <div className="unified-search-container" onClick={(e) => e.stopPropagation()}>
        {/* Search Header */}
        <div className="search-header">
          <form onSubmit={handleSearch} className="search-form">
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
                onClick={handleClear}
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

        {/* Search Filters */}
        {showFilters && (
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
                <button
                  className={`filter-option ${filters.type === 'all' ? 'active' : ''}`}
                  onClick={() => setFilters({ ...filters, type: 'all' })}
                >
                  All
                </button>
                <button
                  className={`filter-option ${filters.type === 'notes' ? 'active' : ''}`}
                  onClick={() => setFilters({ ...filters, type: 'notes' })}
                >
                  Notes
                </button>
                <button
                  className={`filter-option ${filters.type === 'tags' ? 'active' : ''}`}
                  onClick={() => setFilters({ ...filters, type: 'tags' })}
                >
                  Tags
                </button>
                <button
                  className={`filter-option ${filters.type === 'images' ? 'active' : ''}`}
                  onClick={() => setFilters({ ...filters, type: 'images' })}
                >
                  Images
                </button>
              </div>
            </div>

            <div className="filter-group">
              <label className="filter-label">Date Range:</label>
              <div className="filter-options">
                <button
                  className={`filter-option ${filters.dateRange === 'all' ? 'active' : ''}`}
                  onClick={() => setFilters({ ...filters, dateRange: 'all' })}
                >
                  All Time
                </button>
                <button
                  className={`filter-option ${filters.dateRange === 'today' ? 'active' : ''}`}
                  onClick={() => setFilters({ ...filters, dateRange: 'today' })}
                >
                  Today
                </button>
                <button
                  className={`filter-option ${filters.dateRange === 'week' ? 'active' : ''}`}
                  onClick={() => setFilters({ ...filters, dateRange: 'week' })}
                >
                  This Week
                </button>
                <button
                  className={`filter-option ${filters.dateRange === 'month' ? 'active' : ''}`}
                  onClick={() => setFilters({ ...filters, dateRange: 'month' })}
                >
                  This Month
                </button>
              </div>
            </div>

            <div className="filter-group">
              <label className="filter-label">Sort By:</label>
              <div className="filter-options">
                <button
                  className={`filter-option ${sortBy === 'relevance' ? 'active' : ''}`}
                  onClick={() => setSortBy('relevance')}
                >
                  Relevance
                </button>
                <button
                  className={`filter-option ${sortBy === 'date' ? 'active' : ''}`}
                  onClick={() => setSortBy('date')}
                >
                  Date
                </button>
                <button
                  className={`filter-option ${sortBy === 'title' ? 'active' : ''}`}
                  onClick={() => setSortBy('title')}
                >
                  Title
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Active Filters */}
        <FilterChips
          searchMode={searchMode}
          filters={filters}
          sortBy={sortBy}
          onRemove={handleRemoveFilter}
        />

        {/* Search Results or History */}
        {query ? (
          <SearchResults
            results={results}
            loading={loading}
            query={query}
            onClose={onClose}
            onResultClick={onResultClick}
          />
        ) : (
          <div className="search-history">
            <h3 className="search-history-title">Recent Searches</h3>
            {searchHistory.length > 0 ? (
              <div className="search-history-list">
                {searchHistory.map((historyQuery, index) => (
                  <button
                    key={index}
                    className="search-history-item"
                    onClick={() => setQuery(historyQuery)}
                  >
                    <FiSearch className="history-icon" />
                    <span>{historyQuery}</span>
                  </button>
                ))}
              </div>
            ) : (
              <p className="search-history-empty">No recent searches</p>
            )}
            <div className="search-hint">
              <span>💡 Press Cmd/Ctrl+K to open search anywhere</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default UnifiedSearch;
