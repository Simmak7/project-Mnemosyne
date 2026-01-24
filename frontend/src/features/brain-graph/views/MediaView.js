/**
 * MediaView - Visual content filter view
 *
 * Shows only images, notes, and tags for fast visual retrieval.
 * Filters out entities and other non-visual node types.
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { RefreshCw, Image, FileText, Tag } from 'lucide-react';

import { GraphCanvas } from '../components/GraphCanvas';
import { useMapGraph } from '../hooks/useGraphData';

import './MediaView.css';

// Media-focused layers
const MEDIA_LAYERS = ['notes', 'images', 'tags'];

export function MediaView({ graphState, filters, layout }) {
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [activeFilters, setActiveFilters] = useState({
    notes: true,
    images: true,
    tags: false,
  });

  // Fetch map data
  const { data, isLoading, error, refetch } = useMapGraph('all');

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

  // Toggle filter
  const toggleFilter = (type) => {
    setActiveFilters((prev) => ({
      ...prev,
      [type]: !prev[type],
    }));
  };

  // Filter data to media types only
  const graphData = useMemo(() => {
    if (!data) return null;

    const activeLayers = Object.entries(activeFilters)
      .filter(([_, active]) => active)
      .map(([type]) => type);

    // Node IDs use hyphen format (note-123, image-456, tag-789)
    const visibleNodes = data.nodes.filter((node) => {
      const [type] = node.id.split('-');
      const layerType = type === 'image' ? 'images' : type + 's';
      return activeLayers.includes(layerType);
    });

    const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));

    const visibleEdges = data.edges.filter((edge) => {
      return visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target);
    });

    return {
      nodes: visibleNodes.map((node) => ({
        ...node,
        val: node.connections || 1,
      })),
      links: visibleEdges.map((edge) => ({
        source: edge.source,
        target: edge.target,
        type: edge.type,
        weight: edge.weight,
      })),
    };
  }, [data, activeFilters]);

  // Counts - node IDs use hyphen format (note-123, image-456, tag-789)
  const counts = useMemo(() => {
    if (!data?.nodes) return { notes: 0, images: 0, tags: 0 };

    const result = { notes: 0, images: 0, tags: 0 };
    data.nodes.forEach((node) => {
      const [type] = node.id.split('-');
      if (type === 'note') result.notes++;
      else if (type === 'image') result.images++;
      else if (type === 'tag') result.tags++;
    });
    return result;
  }, [data]);

  return (
    <div className="media-view" ref={containerRef}>
      {/* Filter Controls */}
      <div className="media-view__filters">
        <button
          className={`media-view__filter ${activeFilters.notes ? 'is-active' : ''}`}
          onClick={() => toggleFilter('notes')}
          style={{ '--filter-color': 'var(--ng-accent-note)' }}
        >
          <FileText size={14} />
          <span>Notes</span>
          <span className="media-view__filter-count">{counts.notes}</span>
        </button>

        <button
          className={`media-view__filter ${activeFilters.images ? 'is-active' : ''}`}
          onClick={() => toggleFilter('images')}
          style={{ '--filter-color': 'var(--ng-accent-image)' }}
        >
          <Image size={14} />
          <span>Images</span>
          <span className="media-view__filter-count">{counts.images}</span>
        </button>

        <button
          className={`media-view__filter ${activeFilters.tags ? 'is-active' : ''}`}
          onClick={() => toggleFilter('tags')}
          style={{ '--filter-color': 'var(--ng-accent-link)' }}
        >
          <Tag size={14} />
          <span>Tags</span>
          <span className="media-view__filter-count">{counts.tags}</span>
        </button>

        <button
          onClick={refetch}
          className="media-view__refresh"
          title="Refresh"
          disabled={isLoading}
        >
          <RefreshCw size={14} className={isLoading ? 'is-spinning' : ''} />
        </button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="media-view__loading">
          <div className="media-view__spinner" />
          <span>Loading media...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="media-view__error">
          <span>Error: {error}</span>
          <button onClick={refetch}>Retry</button>
        </div>
      )}

      {/* Graph Canvas */}
      {graphData && !isLoading && graphData.nodes.length > 0 && (
        <GraphCanvas
          graphData={graphData}
          graphState={graphState}
          layout={layout}
          filters={filters}
          width={dimensions.width}
          height={dimensions.height}
        />
      )}

      {/* Empty State */}
      {!isLoading && !error && (!graphData || graphData.nodes.length === 0) && (
        <div className="media-view__empty">
          <Image size={48} className="media-view__empty-icon" />
          <p>No media content</p>
          <p className="media-view__empty-hint">
            Enable filters above or upload images to see them here
          </p>
        </div>
      )}
    </div>
  );
}

export default MediaView;
