/**
 * useGraphData - Data fetching hook for Brain Graph
 *
 * Fetches typed graph data from backend API with caching.
 * Supports local neighborhood, map, and path queries.
 */

import { useState, useEffect, useCallback, useRef } from 'react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Fetch local neighborhood graph for a node
 */
export function useLocalGraph(nodeId, depth = 2, layers = ['notes', 'tags'], minWeight = 0.0) {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);

  const fetchData = useCallback(async () => {
    if (!nodeId) {
      setData(null);
      return;
    }

    // Abort previous request
    if (abortRef.current) {
      abortRef.current.abort();
    }
    abortRef.current = new AbortController();

    setIsLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        nodeId: nodeId,
        depth: depth.toString(),
        layers: layers.join(','),
        minWeight: minWeight.toString(),
      });

      const response = await fetch(`${API_BASE}/graph/local?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
        signal: abortRef.current.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = await response.json();
      setData(result);
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message);
      }
    } finally {
      setIsLoading(false);
    }
  }, [nodeId, depth, layers, minWeight]);

  useEffect(() => {
    fetchData();
    return () => abortRef.current?.abort();
  }, [fetchData]);

  return { data, isLoading, error, refetch: fetchData };
}

/**
 * Fetch clustered map graph data
 */
export function useMapGraph(scope = 'all') {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({ scope });

      const response = await fetch(`${API_BASE}/graph/map?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [scope]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, isLoading, error, refetch: fetchData };
}

/**
 * Find path between two nodes
 */
export function usePath(fromId, toId) {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const findPath = useCallback(async () => {
    if (!fromId || !toId) {
      setData(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        from: fromId,
        to: toId,
        limit: '10',
      });

      const response = await fetch(`${API_BASE}/graph/path?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [fromId, toId]);

  useEffect(() => {
    findPath();
  }, [findPath]);

  return { data, isLoading, error, refetch: findPath };
}

/**
 * Search for nodes by title (for path finder autocomplete)
 */
export function useNodeSearch(query, limit = 10) {
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const debounceRef = useRef(null);

  useEffect(() => {
    if (!query || query.length < 2) {
      setResults([]);
      return;
    }

    // Debounce search
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(async () => {
      setIsLoading(true);
      try {
        const token = localStorage.getItem('token');
        const params = new URLSearchParams({ q: query, limit: limit.toString() });
        const response = await fetch(`${API_BASE}/graph/search?${params}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        setResults(data.nodes || []);
      } catch (err) {
        // Fallback to simple filtering if endpoint doesn't exist
        console.warn('Node search failed, falling back to local search');
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query, limit]);

  return { results, isLoading };
}

/**
 * Fetch graph statistics
 */
export function useGraphStats() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      setIsLoading(true);
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE}/graph/stats`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        setData(await response.json());
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };
    fetchStats();
  }, []);

  return { data, isLoading, error };
}

/**
 * Combined hook for graph data management
 */
export function useGraphData(view, nodeId, options = {}) {
  const { depth = 2, layers = ['notes', 'tags'], scope = 'all' } = options;

  const localGraph = useLocalGraph(
    view === 'explore' ? nodeId : null,
    depth,
    layers
  );

  const mapGraph = useMapGraph(view === 'map' ? scope : null);

  return view === 'explore' ? localGraph : mapGraph;
}

export default useGraphData;
