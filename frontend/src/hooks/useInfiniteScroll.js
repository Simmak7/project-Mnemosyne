import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Custom hook for infinite scrolling with pagination
 * @param {Function} fetchFunction - Function to fetch data (receives page number)
 * @param {number} initialPage - Starting page number
 * @returns {Object} - { items, loading, hasMore, loadMore, reset }
 */
function useInfiniteScroll(fetchFunction, initialPage = 1) {
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(initialPage);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState(null);
  const isFetching = useRef(false);

  const loadMore = useCallback(async () => {
    if (loading || !hasMore || isFetching.current) return;

    isFetching.current = true;
    setLoading(true);
    setError(null);

    try {
      const newItems = await fetchFunction(page);

      if (newItems.length === 0) {
        setHasMore(false);
      } else {
        setItems(prev => [...prev, ...newItems]);
        setPage(prev => prev + 1);
      }
    } catch (err) {
      if (process.env.NODE_ENV === 'development') console.error('Error loading more items:', err);
      setError(err);
      setHasMore(false);
    } finally {
      setLoading(false);
      isFetching.current = false;
    }
  }, [fetchFunction, page, loading, hasMore]);

  const reset = useCallback(() => {
    setItems([]);
    setPage(initialPage);
    setHasMore(true);
    setError(null);
    setLoading(false);
    isFetching.current = false;
  }, [initialPage]);

  // Load first page on mount
  useEffect(() => {
    if (items.length === 0 && !loading && hasMore) {
      loadMore();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    items,
    loading,
    hasMore,
    error,
    loadMore,
    reset,
    setItems, // Exposed for manual updates
  };
}

export default useInfiniteScroll;
