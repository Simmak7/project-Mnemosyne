import { useState, useMemo, useCallback } from 'react';
import useDebounce from '../../../../hooks/useDebounce';

/**
 * Hook for graph search and highlighting
 */
export function useGraphSearch(filteredGraphData, graphRef) {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useDebounce(searchTerm, 300);

  // Highlight nodes matching search term
  const highlightedNodes = useMemo(() => {
    if (!debouncedSearchTerm) return new Set();

    const term = debouncedSearchTerm.toLowerCase();
    return new Set(
      filteredGraphData.nodes
        .filter((node) => node.name.toLowerCase().includes(term))
        .map((node) => node.id)
    );
  }, [debouncedSearchTerm, filteredGraphData]);

  // Handle search and focus
  const handleSearch = useCallback((term) => {
    setSearchTerm(term);

    if (term && graphRef.current) {
      const match = filteredGraphData.nodes.find((node) =>
        node.name.toLowerCase().includes(term.toLowerCase())
      );

      if (match) {
        graphRef.current.centerAt(match.x, match.y, 1000);
        graphRef.current.zoom(3, 1000);
      }
    }
  }, [filteredGraphData, graphRef]);

  return {
    searchTerm,
    highlightedNodes,
    handleSearch,
  };
}
