import { useState, useEffect, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { transformToGraphData, filterGraphData } from '../utils/graphDataTransform';

/**
 * Custom hook for managing knowledge graph data
 *
 * Provides:
 * - Fetching notes, tags, images from API
 * - Transforming data into graph format
 * - Filtering by node/link types
 * - Search and highlight functionality
 * - Refresh capability
 *
 * @returns {Object} Graph state and handlers
 */
export function useGraphData() {
  const queryClient = useQueryClient();

  const [filters, setFilters] = useState({
    showNotes: true,
    showTags: true,
    showImages: true,
    showWikilinks: true,
    showTagLinks: true,
    showImageLinks: true,
  });

  const [searchTerm, setSearchTerm] = useState('');

  // Fetch enhanced notes with relationships
  const {
    data: notesData,
    isLoading: notesLoading,
    error: notesError,
    refetch: refetchNotes
  } = useQuery({
    queryKey: ['notes-enhanced'],
    queryFn: async () => {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('No authentication token');

      const response = await fetch('http://localhost:8000/notes-enhanced/', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          localStorage.removeItem('token');
          localStorage.removeItem('username');
          window.location.reload();
          throw new Error('Authentication failed');
        }
        throw new Error('Failed to fetch notes');
      }

      return response.json();
    },
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
  });

  // Fetch tags
  const {
    data: tagsData,
    isLoading: tagsLoading,
    refetch: refetchTags
  } = useQuery({
    queryKey: ['tags'],
    queryFn: async () => {
      const token = localStorage.getItem('token');
      if (!token) return [];

      const response = await fetch('http://localhost:8000/tags/', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      return response.ok ? response.json() : [];
    },
    staleTime: 30000,
    refetchOnWindowFocus: false,
  });

  // Fetch images
  const {
    data: imagesData,
    isLoading: imagesLoading,
    refetch: refetchImages
  } = useQuery({
    queryKey: ['images'],
    queryFn: async () => {
      const token = localStorage.getItem('token');
      if (!token) return [];

      const response = await fetch('http://localhost:8000/images/', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      return response.ok ? response.json() : [];
    },
    staleTime: 30000,
    refetchOnWindowFocus: false,
  });

  // Transform raw data into graph format
  const rawGraphData = useCallback(() => {
    if (!notesData) return { nodes: [], links: [] };

    return transformToGraphData(
      notesData || [],
      tagsData || [],
      imagesData || []
    );
  }, [notesData, tagsData, imagesData]);

  // Apply filters to graph data
  const filteredGraphData = useCallback(() => {
    const raw = rawGraphData();
    return filterGraphData(raw, filters);
  }, [rawGraphData, filters]);

  // Get highlighted node IDs based on search term
  const highlightedNodes = useCallback(() => {
    if (!searchTerm) return new Set();

    const term = searchTerm.toLowerCase();
    const data = filteredGraphData();

    return new Set(
      data.nodes
        .filter((node) => node.name.toLowerCase().includes(term))
        .map((node) => node.id)
    );
  }, [searchTerm, filteredGraphData]);

  // Refresh all graph data
  const refresh = useCallback(async () => {
    await Promise.all([
      refetchNotes(),
      refetchTags(),
      refetchImages(),
    ]);
  }, [refetchNotes, refetchTags, refetchImages]);

  // Invalidate graph cache (for use after mutations)
  const invalidateGraph = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
    queryClient.invalidateQueries({ queryKey: ['tags'] });
    queryClient.invalidateQueries({ queryKey: ['images'] });
  }, [queryClient]);

  // Combined loading state
  const isLoading = notesLoading || tagsLoading || imagesLoading;

  return {
    // Data
    graphData: filteredGraphData(),
    rawGraphData: rawGraphData(),
    highlightedNodes: highlightedNodes(),

    // State
    filters,
    searchTerm,
    isLoading,
    error: notesError,

    // Stats
    stats: {
      totalNodes: rawGraphData().nodes.length,
      totalLinks: rawGraphData().links.length,
      filteredNodes: filteredGraphData().nodes.length,
      filteredLinks: filteredGraphData().links.length,
      noteCount: rawGraphData().nodes.filter(n => n.type === 'note').length,
      tagCount: rawGraphData().nodes.filter(n => n.type === 'tag').length,
      imageCount: rawGraphData().nodes.filter(n => n.type === 'image').length,
    },

    // Actions
    setFilters,
    setSearchTerm,
    refresh,
    invalidateGraph,
  };
}

export default useGraphData;
