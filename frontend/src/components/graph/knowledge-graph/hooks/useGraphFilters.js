import { useState, useMemo } from 'react';

/**
 * Hook for graph filtering logic
 */
export function useGraphFilters(graphData) {
  const [filters, setFilters] = useState({
    showNotes: true,
    showTags: true,
    showImages: true,
    showWikilinks: true,
    showTagLinks: true,
    showImageLinks: true,
  });

  // Filter graph data based on active filters
  const filteredGraphData = useMemo(() => {
    if (!graphData.nodes.length) return graphData;

    const filteredNodes = graphData.nodes.filter((node) => {
      if (node.type === 'note' && !filters.showNotes) return false;
      if (node.type === 'tag' && !filters.showTags) return false;
      if (node.type === 'image' && !filters.showImages) return false;
      return true;
    });

    const nodeIds = new Set(filteredNodes.map((n) => n.id));

    // Helper to get node ID from link source/target
    const getLinkNodeId = (linkNode) => {
      if (typeof linkNode === 'string') return linkNode;
      if (linkNode && typeof linkNode === 'object') return linkNode.id;
      return null;
    };

    const filteredLinks = graphData.links.filter((link) => {
      const sourceId = getLinkNodeId(link.source);
      const targetId = getLinkNodeId(link.target);
      if (!sourceId || !targetId) return false;
      if (!nodeIds.has(sourceId) || !nodeIds.has(targetId)) return false;
      if (link.type === 'wikilink' && !filters.showWikilinks) return false;
      if (link.type === 'tag' && !filters.showTagLinks) return false;
      if (link.type === 'image' && !filters.showImageLinks) return false;
      return true;
    });

    return { nodes: filteredNodes, links: filteredLinks };
  }, [graphData, filters]);

  return {
    filters,
    setFilters,
    filteredGraphData,
  };
}
