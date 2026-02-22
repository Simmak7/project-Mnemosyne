/** ExploreView - Local neighborhood navigation view */

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Target, RefreshCw } from 'lucide-react';

import { GraphCanvas } from '../components/GraphCanvas';
import { ExploreSearchBar } from '../components/ExploreSearchBar';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { DiscoveryPanel } from '../components/DiscoveryPanel';
import { useLocalGraph } from '../hooks/useGraphData';

import '../components/Breadcrumbs.css';
import '../components/DiscoveryPanel.css';
import './ExploreView.css';

// Number of top hubs to show labels for
const TOP_HUBS_COUNT = 5;

export function ExploreView({ graphState, filters, layout, onViewChange }) {
  const containerRef = useRef(null);
  const prevFocusRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  const focusNodeId = graphState.focusNodeId;
  const effectiveDepth = Math.min((filters.filters.depth || 2) + (graphState.expandedDepth || 0), 3);

  const { data, isLoading, error, refetch } = useLocalGraph(
    focusNodeId,
    effectiveDepth,
    filters.filters.nodeLayers,
    filters.filters.minWeight
  );

  const showWelcome = !focusNodeId;

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setDimensions({ width, height });
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  const hubNodeIds = useMemo(() => {
    if (!data?.nodes) return new Set();
    const sorted = [...data.nodes]
      .sort((a, b) => (b.connections || 0) - (a.connections || 0))
      .slice(0, TOP_HUBS_COUNT);

    return new Set(sorted.map((n) => n.id));
  }, [data]);

  const graphData = useMemo(() => {
    if (!data) return null;
    const connectionCounts = {};
    data.edges.forEach((edge) => {
      connectionCounts[edge.source] = (connectionCounts[edge.source] || 0) + 1;
      connectionCounts[edge.target] = (connectionCounts[edge.target] || 0) + 1;
    });

    const depths = {};
    if (focusNodeId) {
      const adj = {};
      data.edges.forEach((e) => {
        (adj[e.source] ??= []).push(e.target);
        (adj[e.target] ??= []).push(e.source);
      });
      let queue = [focusNodeId];
      depths[focusNodeId] = 0;
      while (queue.length) {
        const next = [];
        for (const id of queue) {
          for (const neighbor of adj[id] || []) {
            if (depths[neighbor] === undefined) {
              depths[neighbor] = depths[id] + 1;
              next.push(neighbor);
            }
          }
        }
        queue = next;
      }
    }

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
          depth: depths[node.id] ?? 99,
          // Pin focus node at center to anchor the simulation (prevents spinning)
          ...(node.id === focusNodeId ? { fx: 0, fy: 0, x: 0, y: 0 } : {}),
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

  // Compute edge breakdown by type for selected node
  const selectedNodeId = graphState.selectedNode?.id;
  useEffect(() => {
    if (!selectedNodeId || !graphData?.links) {
      graphState.setEdgeBreakdown(null);
      return;
    }
    const counts = {};
    graphData.links.forEach((link) => {
      const src = typeof link.source === 'object' ? link.source.id : link.source;
      const tgt = typeof link.target === 'object' ? link.target.id : link.target;
      if (src === selectedNodeId || tgt === selectedNodeId) {
        counts[link.type] = (counts[link.type] || 0) + 1;
      }
    });
    graphState.setEdgeBreakdown(Object.keys(counts).length > 0 ? counts : null);
  }, [selectedNodeId, graphData]); // eslint-disable-line react-hooks/exhaustive-deps

  // Center on focus node when data loads + unpin previous focus
  useEffect(() => {
    if (graphData && focusNodeId && layout.graphRef?.current) {
      const fg = layout.graphRef.current;

      // Unpin previous auto-pinned focus node (pinned at 0,0 by us)
      if (prevFocusRef.current && prevFocusRef.current !== focusNodeId) {
        const nodes = fg.graphData?.()?.nodes || [];
        const oldFocus = nodes.find((n) => n.id === prevFocusRef.current);
        if (oldFocus && oldFocus.fx === 0 && oldFocus.fy === 0) {
          oldFocus.fx = undefined;
          oldFocus.fy = undefined;
        }
      }
      prevFocusRef.current = focusNodeId;

      // Small delay to let graph settle, then center
      const timer = setTimeout(() => {
        layout.centerOnNode(focusNodeId);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [focusNodeId, graphData, layout]);

  // Proper refresh: refetch + reheat simulation + fit to view
  const handleRefresh = useCallback(() => {
    refetch().then(() => {
      if (layout.graphRef?.current) {
        const nodes = layout.graphRef.current.graphData?.()?.nodes || [];
        nodes.forEach((n) => { n.fx = undefined; n.fy = undefined; });
        // Re-pin focus node at center to keep simulation anchored
        if (focusNodeId) {
          const fn = nodes.find((n) => n.id === focusNodeId);
          if (fn) { fn.fx = 0; fn.fy = 0; }
        }
        layout.graphRef.current.d3ReheatSimulation?.();
        setTimeout(() => layout.fitToView(40), 600);
      }
    });
  }, [refetch, layout, focusNodeId]);

  // Wire search results to canvas highlight
  const handleSearchResults = useCallback((results) => {
    graphState.setHighlightedNodes(results.map((r) => r.id));
  }, [graphState]);

  return (
    <div className="explore-view" ref={containerRef}>
      {/* Search Bar with autocomplete */}
      <ExploreSearchBar
        onFocusNode={(nodeId) => graphState.setFocus(nodeId)}
        onRefresh={handleRefresh}
        isRefreshing={isLoading}
        onSearchResults={handleSearchResults}
      />

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

      {/* Breadcrumbs - navigation history trail */}
      <Breadcrumbs graphState={graphState} graphData={graphData} />

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
          onViewChange={onViewChange}
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
          <DiscoveryPanel onFocusNode={(id) => graphState.setFocusNodeId(id)} />
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
