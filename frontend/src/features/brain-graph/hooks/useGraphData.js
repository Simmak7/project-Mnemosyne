/**
 * useGraphData - Data fetching hooks for Brain Graph
 *
 * Uses React Query for caching and deduplication.
 * Supports local neighborhood, map, path, search, and stats queries.
 */

import { useState, useEffect, useRef, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/** Shared fetch helper with auth */
async function graphFetch(path, signal) {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
    signal,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/**
 * Fetch local neighborhood graph for a node.
 * Layers/minWeight serialized to string keys to prevent refetch loops.
 */
export function useLocalGraph(nodeId, depth = 2, layers = ['notes', 'tags'], minWeight = 0.0) {
  // Serialize array to stable string for cache key + dependency
  const layersKey = useMemo(() => [...layers].sort().join(','), [layers]);

  const query = useQuery({
    queryKey: ['graph', 'local', nodeId, depth, layersKey, minWeight],
    queryFn: async ({ signal }) => {
      const params = new URLSearchParams({
        nodeId, depth: String(depth), layers: layersKey, minWeight: String(minWeight),
      });
      return graphFetch(`/graph/local?${params}`, signal);
    },
    enabled: !!nodeId,
    staleTime: 60_000,
    gcTime: 5 * 60_000,
  });

  return {
    data: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error?.message ?? null,
    refetch: query.refetch,
  };
}

/**
 * Fetch clustered map graph data
 */
export function useMapGraph(scope = 'all') {
  const query = useQuery({
    queryKey: ['graph', 'map', scope],
    queryFn: async ({ signal }) => {
      const params = new URLSearchParams({ scope });
      return graphFetch(`/graph/map?${params}`, signal);
    },
    enabled: !!scope,
    staleTime: 60_000,
    gcTime: 5 * 60_000,
  });

  return {
    data: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error?.message ?? null,
    refetch: query.refetch,
  };
}

/**
 * Find path between two nodes
 */
export function usePath(fromId, toId) {
  const query = useQuery({
    queryKey: ['graph', 'path', fromId, toId],
    queryFn: async ({ signal }) => {
      const params = new URLSearchParams({ from: fromId, to: toId, limit: '10' });
      return graphFetch(`/graph/path?${params}`, signal);
    },
    enabled: !!fromId && !!toId,
    staleTime: 30_000,
    gcTime: 5 * 60_000,
  });

  return {
    data: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error?.message ?? null,
    refetch: query.refetch,
  };
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

    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      setIsLoading(true);
      try {
        const params = new URLSearchParams({ q: query, limit: String(limit) });
        const data = await graphFetch(`/graph/search?${params}`);
        setResults(data.nodes || []);
      } catch {
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query, limit]);

  return { results, isLoading };
}

/**
 * Fetch graph statistics
 */
export function useGraphStats() {
  const query = useQuery({
    queryKey: ['graph', 'stats'],
    queryFn: ({ signal }) => graphFetch('/graph/stats', signal),
    staleTime: 120_000,
    gcTime: 10 * 60_000,
  });

  return {
    data: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error?.message ?? null,
  };
}

export default useLocalGraph;
