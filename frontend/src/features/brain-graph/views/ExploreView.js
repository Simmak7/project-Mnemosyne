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
  const filterDepth = filters.filters.depth || 2;

  // Reset expandedDepth when user changes depth slider so slider is always respected
  const prevFilterDepth = useRef(filterDepth);
  useEffect(() => {
    if (prevFilterDepth.current !== filterDepth) {
      prevFilterDepth.current = filterDepth;
      graphState.resetExpandedDepth();
    }
  }, [filterDepth]); // eslint-disable-line react-hooks/exhaustive-deps

  const effectiveDepth = Math.min(filterDepth + (graphState.expandedDepth || 0), 3);

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

    // BFS depth from focus node
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

    // Pre-compute evenly-spaced positions per depth ring so nodes start near
    // their equilibrium — eliminates orbital spinning during simulation warmup.
    const byDepth = {};
    data.nodes.forEach((node) => {
      if (node.id === focusNodeId) return;
      const d = depths[node.id] ?? 1;
      (byDepth[d] ??= []).push(node.id);
    });
    const initPos = {};
    Object.entries(byDepth).forEach(([d, ids]) => {
      const radius = parseInt(d, 10) * 140;
      ids.forEach((id, i) => {
        const angle = (i / ids.length) * 2 * Math.PI - Math.PI / 2;
        initPos[id] = { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius };
      });
    });

    return {
      nodes: data.nodes.map((node) => {
        const isFocus = node.id === focusNodeId;
        const connections = connectionCounts[node.id] || 0;
        const pos = initPos[node.id];
        return {
          ...node,
          id: node.id,
          title: node.title,
          metadata: node.metadata,
          connections,
          val: connections || 1,
          isHub: hubNodeIds.has(node.id),
          isFocus,
          depth: depths[node.id] ?? 99,
          // Focus node pinned at center; others start at ring positions
          ...(isFocus ? { fx: 0, fy: 0, x: 0, y: 0 } : pos ? { x: pos.x, y: pos.y } : {}),
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

  // Stable refs to layout callbacks so the effect doesn't re-fire on every render
  const layoutRef = useRef(layout);
  useEffect(() => { layoutRef.current = layout; });

  // Center on focus node when data loads + unpin previous focus
  useEffect(() => {
    if (graphData && focusNodeId && layoutRef.current.graphRef?.current) {
      const fg = layoutRef.current.graphRef.current;

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
        layoutRef.current.centerOnNode(focusNodeId);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [focusNodeId, graphData]); // layout intentionally excluded — use layoutRef instead

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

      {/* Graph Canvas — key forces fresh mount on focus change so D3 doesn't
          reuse stale node positions from cached data (staleTime: 60s). warmupTicks=0
          avoids spinning from default D3 forces before our custom forces are applied. */}
      {graphData && !isLoading && (
        <GraphCanvas
          key={`${focusNodeId || 'no-focus'}-d${effectiveDepth}`}
          warmupTicks={0}
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
