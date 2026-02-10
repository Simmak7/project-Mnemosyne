import { useState, useEffect, useCallback, useRef } from 'react';
import useDebounce from '../../../../hooks/useDebounce';

/**
 * Hook for managing unified search state
 */
export function useSearchState(isOpen, onClose) {
  const [query, setQuery] = useState('');
  const [searchMode, setSearchMode] = useState('combined');
  const [filters, setFilters] = useState({
    type: 'all',
    dateRange: 'all',
  });
  const [sortBy, setSortBy] = useState('relevance');
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
        }
      }

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

        if (response.ok) {
          const data = await response.json();
          setResults(data.results || []);
        } else {
          console.error('Search failed:', response.status);
        }
      } catch (error) {
        console.error('Error performing search:', error);
      } finally {
        setLoading(false);
      }
    };

    performSearch();
  }, [debouncedQuery, searchMode, filters, sortBy]);

  // Save to search history
  const saveToHistory = useCallback((searchQuery) => {
    if (!searchQuery.trim()) return;

    const history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
    const newHistory = [searchQuery, ...history.filter(q => q !== searchQuery)].slice(0, 10);
    localStorage.setItem('searchHistory', JSON.stringify(newHistory));
    setSearchHistory(newHistory);
  }, []);

  // Clear search
  const handleClear = useCallback(() => {
    setQuery('');
    setResults([]);
    searchInputRef.current?.focus();
  }, []);

  // Remove filter
  const handleRemoveFilter = useCallback((filterType) => {
    if (filterType === 'type') {
      setFilters(f => ({ ...f, type: 'all' }));
    } else if (filterType === 'dateRange') {
      setFilters(f => ({ ...f, dateRange: 'all' }));
    } else if (filterType === 'searchMode') {
      setSearchMode('combined');
    }
  }, []);

  return {
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
  };
}
