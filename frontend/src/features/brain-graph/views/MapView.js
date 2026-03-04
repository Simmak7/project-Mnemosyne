/** MapView - Clustered overview for insight mode */

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { RefreshCw, Layers, Info, ChevronDown } from 'lucide-react';
import { GraphCanvas } from '../components/GraphCanvas';
import { StatsBreakdown } from '../components/StatsBreakdown';
import { useMapGraph, useGraphStats } from '../hooks/useGraphData';
import './MapView.css';

// Common words that don't describe a cluster meaningfully
const COMMUNITY_STOP_WORDS = new Set([
  'a', 'an', 'the', 'is', 'in', 'of', 'to', 'and', 'or', 'for',
  'with', 'that', 'this', 'my', 'i', 'it', 'its', 'note', 'notes',
  'daily', 'journal', 'entry', 'untitled', 'test', 'new', 'how',
  'why', 'what', 'when', 'where', 'who', 'was', 'are', 'be', 'at',
  'by', 'from', 'as', 'on', 'up', 'out', 'if', 'so', 'do', 'all',
  'can', 'had', 'but', 'not', 'one', 'have', 'more', 'about', 'get',
  'like', 'time', 'just', 'make', 'your', 'use', 'into', 'after',
  'work', 'some', 'want', 'also', 'than', 'only', 'other',
]);

function buildCommunityLabel(community) {
  if (!community.top_terms?.length) {
    return community.label && community.label !== 'Unclustered'
      ? community.label
      : `Cluster ${community.id + 1}`;
  }
  const unique = [...new Set(community.top_terms.map((t) => t.toLowerCase()))]
    .filter((t) => t.length > 2 && !COMMUNITY_STOP_WORDS.has(t));
  if (unique.length === 0) {
    return community.label && community.label !== 'Unclustered'
      ? community.label
      : `Cluster ${community.id + 1}`;
  }
  return unique
    .slice(0, 3)
    .map((t) => t.charAt(0).toUpperCase() + t.slice(1))
    .join(' · ');
}

const COMMUNITY_COLORS = [
  '#818cf8', '#34d399', '#fbbf24', '#22d3ee',
  '#f472b6', '#fb923c', '#a78bfa', '#4ade80',
];

export function MapView({ graphState, filters, layout, onExploreNode, onViewChange }) {
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [showStats, setShowStats] = useState(false);
  const [legendOpen, setLegendOpen] = useState(false);

  const { data, isLoading, error, refetch } = useMapGraph('all');
  const { data: stats } = useGraphStats();

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setDimensions({ width, height });
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  const graphData = useMemo(() => {
    if (!data) return null;
    const positions = data.positions || {};
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
          metadata: { ...node.metadata, communityId, communityColor },
          x: pos?.x ?? undefined,
          y: pos?.y ?? undefined,
          connections,
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

  const communitySummary = useMemo(() => {
    if (!data?.nodes) return [];
    if (data.communities?.length > 0) {
      return data.communities
        .filter((c) => c.label !== 'Unclustered')
        .map((c) => ({
          id: c.id,
          count: c.node_count,
          color: COMMUNITY_COLORS[c.id % COMMUNITY_COLORS.length],
          label: buildCommunityLabel(c),
        }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 8);
    }

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
        label: `Cluster ${parseInt(id, 10) + 1}`,
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8);
  }, [data]);

  const handleRefresh = useCallback(() => {
    refetch().then(() => {
      // After fresh data arrives, clear user-dragged positions and restart layout
      if (layout.graphRef?.current) {
        const nodes = layout.graphRef.current.graphData?.()?.nodes || [];
        nodes.forEach((n) => { n.fx = undefined; n.fy = undefined; });
        layout.graphRef.current.d3ReheatSimulation?.();
        setTimeout(() => layout.fitToView(40), 600);
      }
    });
  }, [refetch, layout]);

  // Auto-fit to view after initial data load (only when data changes, not on re-renders)
  useEffect(() => {
    if (graphData && layout.graphRef?.current) {
      const timer = setTimeout(() => layout.fitToView(40), 800);
      return () => clearTimeout(timer);
    }
  }, [graphData]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleNodeDoubleClick = useCallback((node) => {
    if (onExploreNode && node) onExploreNode(node.id);
  }, [onExploreNode]);

  const mapGraphState = useMemo(() => ({
    ...graphState, handleNodeDoubleClick,
  }), [graphState, handleNodeDoubleClick]);

  return (
    <div className="map-view" ref={containerRef}>
      <div className="map-view__controls">
        <button onClick={handleRefresh} className="map-view__control" title="Refresh map" disabled={isLoading}>
          <RefreshCw size={16} className={isLoading ? 'is-spinning' : ''} />
        </button>
        <button onClick={() => setShowStats(!showStats)} className={`map-view__control ${showStats ? 'is-active' : ''}`} title="Toggle stats">
          <Info size={16} />
        </button>
      </div>

      <div className={`map-view__legend ${legendOpen ? '' : 'is-collapsed'}`}>
        <button className="map-view__legend-header" onClick={() => setLegendOpen(!legendOpen)}>
          <Layers size={14} />
          <span>Communities</span>
          <ChevronDown size={14} className={`map-view__legend-chevron ${legendOpen ? '' : 'is-rotated'}`} />
        </button>
        {legendOpen && (
          <>
            <div className="map-view__legend-hint">
              Groups of related notes detected by AI clustering. Click to isolate.
            </div>
            <div className="map-view__legend-items">
              {communitySummary.map((community) => (
                <button
                  key={community.id}
                  className={`map-view__legend-item ${filters.filters.communityId === community.id ? 'is-active' : ''}`}
                  onClick={() => filters.setCommunityId(filters.filters.communityId === community.id ? null : community.id)}
                  style={{
                    '--community-color': community.color,
                    opacity: filters.filters.communityId === null || filters.filters.communityId === community.id ? 1 : 0.4,
                  }}
                >
                  <span className="map-view__legend-dot" style={{ backgroundColor: community.color }} />
                  <span className="map-view__legend-label">{community.label}</span>
                  <span className="map-view__legend-count">{community.count}</span>
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      {showStats && stats && <StatsBreakdown stats={stats} />}

      {isLoading && (
        <div className="map-view__loading">
          <div className="map-view__spinner" />
          <span>Loading map...</span>
        </div>
      )}

      {error && (
        <div className="map-view__error">
          <span>Error: {error}</span>
          <button onClick={refetch}>Retry</button>
        </div>
      )}

      {graphData && !isLoading && (
        <GraphCanvas
          graphData={graphData}
          graphState={mapGraphState}
          layout={layout}
          filters={filters}
          width={dimensions.width}
          height={dimensions.height}
          onViewChange={onViewChange}
        />
      )}
    </div>
  );
}

export default MapView;
