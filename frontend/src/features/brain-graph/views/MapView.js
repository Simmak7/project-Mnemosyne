/**
 * MapView - Clustered overview for insight mode
 *
 * Shows all notes with community clusters visualized.
 * Uses precomputed stable positions for consistent layout.
 */

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { RefreshCw, Layers, Info } from 'lucide-react';

import { GraphCanvas } from '../components/GraphCanvas';
import { useMapGraph, useGraphStats } from '../hooks/useGraphData';

import './MapView.css';

// Community colors for visual clustering
const COMMUNITY_COLORS = [
  '#818cf8', // Violet
  '#34d399', // Emerald
  '#fbbf24', // Amber
  '#22d3ee', // Cyan
  '#f472b6', // Pink
  '#fb923c', // Orange
  '#a78bfa', // Purple
  '#4ade80', // Green
];

export function MapView({ graphState, filters, layout, onExploreNode }) {
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [showStats, setShowStats] = useState(false);

  // Fetch map data
  const { data, isLoading, error, refetch } = useMapGraph('all');
  const { data: stats } = useGraphStats();

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

  // Transform API data with community colors and positions
  const graphData = useMemo(() => {
    if (!data) return null;

    // Positions are in data.positions dict keyed by node ID
    const positions = data.positions || {};

    // Compute connection counts from edges
    const connectionCounts = {};
    data.edges.forEach((edge) => {
      connectionCounts[edge.source] = (connectionCounts[edge.source] || 0) + 1;
      connectionCounts[edge.target] = (connectionCounts[edge.target] || 0) + 1;
    });

    return {
      nodes: data.nodes.map((node) => {
        const communityId = node.metadata?.communityId ?? node.metadata?.community_id ?? 0;
        const communityColor = COMMUNITY_COLORS[communityId % COMMUNITY_COLORS.length];
        const pos = positions[node.id];
        const connections = connectionCounts[node.id] || 0;

        return {
          ...node,
          id: node.id,
          title: node.title,
          metadata: {
            ...node.metadata,
            communityId,
            communityColor,
          },
          // Use precomputed position from positions dict if available
          fx: pos?.x ?? undefined,
          fy: pos?.y ?? undefined,
          connections, // Computed from edges
          val: connections || 1,
        };
      }),
      links: data.edges.map((edge) => ({
        source: edge.source,
        target: edge.target,
        type: edge.type,
        weight: edge.weight,
      })),
    };
  }, [data]);

  // Community summary
  const communitySummary = useMemo(() => {
    if (!data?.nodes) return [];

    const counts = {};
    data.nodes.forEach((node) => {
      const cid = node.metadata?.communityId ?? node.metadata?.community_id ?? 0;
      counts[cid] = (counts[cid] || 0) + 1;
    });

    return Object.entries(counts)
      .map(([id, count]) => ({
        id: parseInt(id, 10),
        count,
        color: COMMUNITY_COLORS[parseInt(id, 10) % COMMUNITY_COLORS.length],
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8);
  }, [data]);

  // Override double-click to explore node in Explore view
  const handleNodeDoubleClick = useCallback((node) => {
    if (onExploreNode && node) {
      onExploreNode(node.id);
    }
  }, [onExploreNode]);

  // Create wrapped graphState with explore behavior for double-click
  const mapGraphState = useMemo(() => ({
    ...graphState,
    handleNodeDoubleClick,
  }), [graphState, handleNodeDoubleClick]);

  return (
    <div className="map-view" ref={containerRef}>
      {/* Controls */}
      <div className="map-view__controls">
        <button
          onClick={refetch}
          className="map-view__control"
          title="Refresh map"
          disabled={isLoading}
        >
          <RefreshCw size={16} className={isLoading ? 'is-spinning' : ''} />
        </button>

        <button
          onClick={() => setShowStats(!showStats)}
          className={`map-view__control ${showStats ? 'is-active' : ''}`}
          title="Toggle stats"
        >
          <Info size={16} />
        </button>
      </div>

      {/* Community Legend */}
      <div className="map-view__legend">
        <div className="map-view__legend-header">
          <Layers size={14} />
          <span>Communities</span>
        </div>
        <div className="map-view__legend-items">
          {communitySummary.map((community) => (
            <button
              key={community.id}
              className="map-view__legend-item"
              onClick={() => filters.setCommunityId(
                filters.filters.communityId === community.id ? null : community.id
              )}
              style={{
                '--community-color': community.color,
                opacity: filters.filters.communityId === null ||
                         filters.filters.communityId === community.id ? 1 : 0.4,
              }}
            >
              <span
                className="map-view__legend-dot"
                style={{ backgroundColor: community.color }}
              />
              <span className="map-view__legend-count">{community.count}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Stats Panel */}
      {showStats && stats && (
        <div className="map-view__stats">
          <div className="map-view__stat">
            <span className="map-view__stat-value">{stats.total_nodes}</span>
            <span className="map-view__stat-label">Nodes</span>
          </div>
          <div className="map-view__stat">
            <span className="map-view__stat-value">{stats.total_edges}</span>
            <span className="map-view__stat-label">Edges</span>
          </div>
          <div className="map-view__stat">
            <span className="map-view__stat-value">{stats.communities || 0}</span>
            <span className="map-view__stat-label">Communities</span>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="map-view__loading">
          <div className="map-view__spinner" />
          <span>Loading map...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="map-view__error">
          <span>Error: {error}</span>
          <button onClick={refetch}>Retry</button>
        </div>
      )}

      {/* Graph Canvas - uses mapGraphState to override double-click for exploration */}
      {graphData && !isLoading && (
        <GraphCanvas
          graphData={graphData}
          graphState={mapGraphState}
          layout={layout}
          filters={filters}
          width={dimensions.width}
          height={dimensions.height}
        />
      )}
    </div>
  );
}

export default MapView;
