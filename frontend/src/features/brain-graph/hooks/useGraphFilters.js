/**
 * useGraphFilters - Layer and filter state management
 *
 * Controls which node types, edge types, and weight thresholds
 * are visible in the graph visualization.
 */

import { useState, useCallback, useMemo } from 'react';
import { usePersistedState } from '../../../hooks/usePersistedState';

// Available layer types
export const NODE_LAYERS = {
  notes: { label: 'Notes', color: 'var(--ng-accent-note)', icon: 'FileText' },
  tags: { label: 'Tags', color: 'var(--ng-accent-link)', icon: 'Tag' },
  images: { label: 'Images', color: 'var(--ng-accent-image)', icon: 'Image' },
  documents: { label: 'Documents', color: '#fb7185', icon: 'FileScan' },
  entities: { label: 'Entities', color: 'var(--ng-accent-ai)', icon: 'Sparkles' },
};

export const EDGE_LAYERS = {
  wikilink: { label: 'Wikilinks', color: 'rgba(255,255,255,0.6)', weight: 1.0 },
  tag: { label: 'Tags', color: 'var(--ng-accent-link)', weight: 0.7 },
  image: { label: 'Images', color: 'var(--ng-accent-image)', weight: 0.8 },
  source: { label: 'Sources', color: '#fb7185', weight: 0.9 },
  semantic: { label: 'Semantic', color: 'var(--ng-accent-ai)', weight: 0.5 },
  mentions: { label: 'Mentions', color: 'var(--ng-accent-ai)', weight: 0.6 },
};

// Default filter state
const DEFAULT_FILTERS = {
  nodeLayers: ['notes', 'tags', 'images', 'documents'],
  edgeLayers: ['wikilink', 'tag', 'image', 'source', 'semantic'],
  minWeight: 0.0,
  dateRange: null, // { start: Date, end: Date }
  searchQuery: '',
  communityId: null,
  depth: 2,
};

/**
 * Graph filter state hook
 */
export function useGraphFilters(initialFilters = {}) {
  const [persistedDepth, setPersistedDepth] = usePersistedState('brain:depth', DEFAULT_FILTERS.depth);
  const [filters, setFilters] = useState({
    ...DEFAULT_FILTERS,
    depth: persistedDepth,
    ...initialFilters,
  });

  // Toggle a node layer on/off
  const toggleNodeLayer = useCallback((layer) => {
    setFilters((prev) => {
      const layers = prev.nodeLayers.includes(layer)
        ? prev.nodeLayers.filter((l) => l !== layer)
        : [...prev.nodeLayers, layer];
      return { ...prev, nodeLayers: layers };
    });
  }, []);

  // Toggle an edge layer on/off
  const toggleEdgeLayer = useCallback((layer) => {
    setFilters((prev) => {
      const layers = prev.edgeLayers.includes(layer)
        ? prev.edgeLayers.filter((l) => l !== layer)
        : [...prev.edgeLayers, layer];
      return { ...prev, edgeLayers: layers };
    });
  }, []);

  // Set minimum edge weight threshold
  const setMinWeight = useCallback((weight) => {
    setFilters((prev) => ({ ...prev, minWeight: weight }));
  }, []);

  // Set date range filter
  const setDateRange = useCallback((range) => {
    setFilters((prev) => ({ ...prev, dateRange: range }));
  }, []);

  // Set search query
  const setSearchQuery = useCallback((query) => {
    setFilters((prev) => ({ ...prev, searchQuery: query }));
  }, []);

  // Set community filter
  const setCommunityId = useCallback((id) => {
    setFilters((prev) => ({ ...prev, communityId: id }));
  }, []);

  // Set depth for local graph (persisted)
  const setDepth = useCallback((depth) => {
    const clamped = Math.max(1, Math.min(5, depth));
    setFilters((prev) => ({ ...prev, depth: clamped }));
    setPersistedDepth(clamped);
  }, [setPersistedDepth]);

  // Reset to defaults
  const resetFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
  }, []);

  // Check if a node should be visible
  const isNodeVisible = useCallback((node) => {
    // Guard against nodes without id
    if (!node || !node.id) {
      return false;
    }

    // Check layer - node IDs use hyphen format (note-123, tag-456)
    const [type] = node.id.split('-');
    if (!type) {
      return true; // Allow nodes without proper type format
    }

    // Layer names are plural (notes, tags, images, entities)
    // Node ID types are singular (note, tag, image, entity)
    const plural = type + 's';
    if (!filters.nodeLayers.includes(plural) && !filters.nodeLayers.includes(type)) {
      return false;
    }

    // Check search query
    if (filters.searchQuery) {
      const query = filters.searchQuery.toLowerCase();
      const title = (node.title || '').toLowerCase();
      if (!title.includes(query)) {
        return false;
      }
    }

    // Check community
    if (filters.communityId !== null && node.metadata?.communityId !== filters.communityId) {
      return false;
    }

    return true;
  }, [filters]);

  // Check if an edge should be visible
  const isEdgeVisible = useCallback((edge) => {
    // Check layer
    if (!filters.edgeLayers.includes(edge.type)) {
      return false;
    }

    // Check weight threshold
    if (edge.weight < filters.minWeight) {
      return false;
    }

    return true;
  }, [filters]);

  // Get active layer info
  const activeNodeLayers = useMemo(() => {
    return filters.nodeLayers.map((layer) => ({
      id: layer,
      ...NODE_LAYERS[layer],
    }));
  }, [filters.nodeLayers]);

  const activeEdgeLayers = useMemo(() => {
    return filters.edgeLayers.map((layer) => ({
      id: layer,
      ...EDGE_LAYERS[layer],
    }));
  }, [filters.edgeLayers]);

  return {
    filters,
    toggleNodeLayer,
    toggleEdgeLayer,
    setMinWeight,
    setDateRange,
    setSearchQuery,
    setCommunityId,
    setDepth,
    resetFilters,
    isNodeVisible,
    isEdgeVisible,
    activeNodeLayers,
    activeEdgeLayers,
    NODE_LAYERS,
    EDGE_LAYERS,
  };
}

export default useGraphFilters;
