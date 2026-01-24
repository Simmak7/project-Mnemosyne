/**
 * ExploreView - Local neighborhood navigation view
 *
 * Default view showing focused node at center with neighbors up to depth.
 * Optimized for fast navigation: click sets focus, double-click opens.
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Search, RefreshCw, Target } from 'lucide-react';

import { GraphCanvas } from '../components/GraphCanvas';
import { useLocalGraph } from '../hooks/useGraphData';

import './ExploreView.css';

// Number of top hubs to show labels for
const TOP_HUBS_COUNT = 5;

export function ExploreView({ graphState, filters, layout }) {
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [searchQuery, setSearchQuery] = useState('');

  // Get focused node ID - no hardcoded default, user must select a starting point
  // Backend expects hyphen format: note-1, tag-123
  const focusNodeId = graphState.focusNodeId;

  // Calculate effective depth (base + expanded)
  const effectiveDepth = Math.min(
    (filters.filters.depth || 2) + (graphState.expandedDepth || 0),
    3 // Max depth capped at 3
  );

  // Fetch local neighborhood data only if we have a focus node
  const { data, isLoading, error, refetch } = useLocalGraph(
    focusNodeId,
    effectiveDepth,
    filters.filters.nodeLayers,
    filters.filters.minWeight
  );

  // Show prompt if no focus node is set
  const showWelcome = !focusNodeId;

  // Resize handling
  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setDimensions({ width, height });
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Calculate hub nodes (most connected) for label display
  const hubNodeIds = useMemo(() => {
    if (!data?.nodes) return new Set();

    const sorted = [...data.nodes]
      .sort((a, b) => (b.connections || 0) - (a.connections || 0))
      .slice(0, TOP_HUBS_COUNT);

    return new Set(sorted.map((n) => n.id));
  }, [data]);

  // Transform API data to graph format with hub marking
  const graphData = useMemo(() => {
    if (!data) return null;

    // Compute connection counts from edges
    const connectionCounts = {};
    data.edges.forEach((edge) => {
      connectionCounts[edge.source] = (connectionCounts[edge.source] || 0) + 1;
      connectionCounts[edge.target] = (connectionCounts[edge.target] || 0) + 1;
    });

    return {
      nodes: data.nodes.map((node) => {
        const connections = connectionCounts[node.id] || 0;
        return {
          ...node,
          id: node.id,
          title: node.title,
          metadata: node.metadata,
          connections, // Computed from edges
          val: connections || 1, // Size based on connections
          isHub: hubNodeIds.has(node.id),
          isFocus: node.id === focusNodeId,
        };
      }),
      links: data.edges.map((edge) => ({
        source: edge.source,
        target: edge.target,
        type: edge.type,
        weight: edge.weight,
        evidence: edge.evidence,
      })),
    };
  }, [data, hubNodeIds, focusNodeId]);

  // Center on focus node when data loads
  useEffect(() => {
    if (graphData && focusNodeId && layout.graphRef?.current) {
      // Small delay to let graph settle
      const timer = setTimeout(() => {
        layout.centerOnNode(focusNodeId);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [focusNodeId, graphData, layout]);

  // Handle search
  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      filters.setSearchQuery(searchQuery);
    }
  };

  // Clear search
  const clearSearch = () => {
    setSearchQuery('');
    filters.setSearchQuery('');
  };

  return (
    <div className="explore-view" ref={containerRef}>
      {/* Search Bar */}
      <div className="explore-view__search">
        <form onSubmit={handleSearch} className="explore-view__search-form">
          <Search size={16} className="explore-view__search-icon" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search nodes..."
            className="explore-view__search-input"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={clearSearch}
              className="explore-view__search-clear"
            >
              Clear
            </button>
          )}
        </form>

        <button
          onClick={refetch}
          className="explore-view__refresh"
          title="Refresh graph"
          disabled={isLoading}
        >
          <RefreshCw size={16} className={isLoading ? 'is-spinning' : ''} />
        </button>
      </div>

      {/* Focus Info */}
      {graphState.focusNodeId && (
        <div className="explore-view__focus-info">
          <Target size={14} className="explore-view__focus-icon" />
          <span className="explore-view__focus-label">Focus:</span>
          <span className="explore-view__focus-id">
            {graphData?.nodes.find((n) => n.id === graphState.focusNodeId)?.title || graphState.focusNodeId}
          </span>
          <button
            className="explore-view__center-btn"
            onClick={() => layout.centerOnNode(graphState.focusNodeId)}
            title="Center on focus node"
          >
            Center
          </button>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="explore-view__loading">
          <div className="explore-view__spinner" />
          <span>Loading neighborhood...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="explore-view__error">
          <span>Error: {error}</span>
          <button onClick={refetch}>Retry</button>
        </div>
      )}

      {/* Graph Canvas */}
      {graphData && !isLoading && (
        <GraphCanvas
          graphData={graphData}
          graphState={graphState}
          layout={layout}
          filters={filters}
          width={dimensions.width}
          height={dimensions.height}
        />
      )}

      {/* Welcome State - No focus node selected */}
      {showWelcome && !isLoading && (
        <div className="explore-view__welcome">
          <Target size={32} className="explore-view__welcome-icon" />
          <h3>Select a Starting Point</h3>
          <p>Use the <strong>Map</strong> view to browse your knowledge graph and click a node to explore its neighborhood.</p>
          <p className="explore-view__welcome-hint">
            Or search for a specific note above
          </p>
        </div>
      )}

      {/* Empty State - Focus node selected but no data */}
      {!showWelcome && !isLoading && !error && (!graphData || graphData.nodes.length === 0) && (
        <div className="explore-view__empty">
          <p>No connections found</p>
          <p className="explore-view__empty-hint">
            Try creating notes with [[wikilinks]] to build your knowledge graph
          </p>
        </div>
      )}
    </div>
  );
}

export default ExploreView;
