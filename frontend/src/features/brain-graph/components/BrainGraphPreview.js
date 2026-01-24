/**
 * BrainGraphPreview - Mini Neural Glass graph for workspace context rail
 *
 * Shows local neighborhood of the current note with Neural Glass styling.
 * Optimized for small panel size with click-to-navigate functionality.
 */

import React, { useMemo, useRef, useEffect, useCallback, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import ForceGraph2D from 'react-force-graph-2d';
import { Network } from 'lucide-react';
import { NODE_COLORS, getNodeSize } from '../utils/nodeRendering';
import { EDGE_COLORS } from '../utils/edgeRendering';
import './BrainGraphPreview.css';

export function BrainGraphPreview({
  selectedNoteId,
  onSelectNote,
  editorWikilinks = [],
  isEditMode = false,
}) {
  const graphRef = useRef();
  const [hoveredNode, setHoveredNode] = useState(null);

  // Fetch graph data
  const { data: graphData, isLoading, error } = useQuery({
    queryKey: ['graphData', selectedNoteId],
    queryFn: async () => {
      if (!selectedNoteId) return null;

      const token = localStorage.getItem('token');
      if (!token) throw new Error('No authentication token');

      const response = await fetch('http://localhost:8000/graph/data', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Failed to fetch graph data');
      return response.json();
    },
    enabled: !!selectedNoteId,
    staleTime: 30000,
    refetchOnWindowFocus: false,
  });

  // Filter to local neighborhood (1-hop from current note)
  const localGraphData = useMemo(() => {
    if (!graphData || !selectedNoteId) {
      return { nodes: [], links: [] };
    }

    const currentNodeId = `note-${selectedNoteId}`;
    const currentNode = graphData.nodes.find(n => n.id === currentNodeId);
    if (!currentNode) return { nodes: [], links: [] };

    // Find connected links
    const connectedLinks = graphData.links.filter(link => {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;
      return sourceId === currentNodeId || targetId === currentNodeId;
    });

    // Find connected node IDs
    const connectedNodeIds = new Set([currentNodeId]);
    connectedLinks.forEach(link => {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;
      connectedNodeIds.add(sourceId);
      connectedNodeIds.add(targetId);
    });

    // Filter nodes
    const localNodes = graphData.nodes.filter(n => connectedNodeIds.has(n.id));

    return { nodes: localNodes, links: connectedLinks };
  }, [graphData, selectedNoteId]);

  // Highlighted nodes (current + wikilinks in editor)
  const highlightedNodeIds = useMemo(() => {
    const highlighted = new Set([`note-${selectedNoteId}`]);

    if (isEditMode && editorWikilinks.length > 0) {
      editorWikilinks.forEach(wikilink => {
        const node = localGraphData.nodes.find(
          n => n.type === 'note' && n.title === wikilink
        );
        if (node) highlighted.add(node.id);
      });
    }

    return highlighted;
  }, [selectedNoteId, isEditMode, editorWikilinks, localGraphData.nodes]);

  // Zoom to fit on data change
  useEffect(() => {
    if (graphRef.current && localGraphData.nodes.length > 0) {
      const timer1 = setTimeout(() => graphRef.current?.centerAt(0, 0, 0), 50);
      const timer2 = setTimeout(() => graphRef.current?.zoomToFit(600, 60), 400);
      const timer3 = setTimeout(() => graphRef.current?.zoomToFit(400, 60), 1200);
      return () => { clearTimeout(timer1); clearTimeout(timer2); clearTimeout(timer3); };
    }
  }, [localGraphData]);

  // Get node color
  const getNodeColor = useCallback((node) => {
    const isCurrent = node.id === `note-${selectedNoteId}`;
    const isHighlighted = highlightedNodeIds.has(node.id);
    const isHovered = hoveredNode === node.id;
    const [type] = node.id.split('-');

    if (isCurrent) return NODE_COLORS.entity.base; // Violet for current
    if (isHovered) {
      const colors = NODE_COLORS[type] || NODE_COLORS.default;
      return colors.base;
    }
    const colors = NODE_COLORS[type] || NODE_COLORS.default;
    return isHighlighted ? colors.base : colors.border;
  }, [selectedNoteId, highlightedNodeIds, hoveredNode]);

  // Handle node click
  const handleNodeClick = useCallback((node) => {
    if (node.id.startsWith('note-')) {
      const noteId = parseInt(node.id.replace('note-', ''));
      onSelectNote?.(noteId);
    }
  }, [onSelectNote]);

  // Handle hover
  const handleNodeHover = useCallback((node) => {
    setHoveredNode(node?.id || null);
  }, []);

  // Custom node rendering
  const paintNode = useCallback((node, ctx, globalScale) => {
    // Guard: Skip if coordinates are not yet initialized by force simulation
    if (!Number.isFinite(node.x) || !Number.isFinite(node.y)) {
      return;
    }

    const isCurrent = node.id === `note-${selectedNoteId}`;
    const isHighlighted = highlightedNodeIds.has(node.id);
    const isHovered = hoveredNode === node.id;
    const [type] = node.id.split('-');

    const colors = isCurrent ? NODE_COLORS.entity : (NODE_COLORS[type] || NODE_COLORS.default);
    const size = isCurrent ? 6 : getNodeSize(node, { minSize: 3, maxSize: 5, baseSize: 3 });

    // Draw glow for current node
    if (isCurrent) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, size + 6, 0, 2 * Math.PI);
      const gradient = ctx.createRadialGradient(node.x, node.y, size, node.x, node.y, size + 10);
      gradient.addColorStop(0, 'rgba(129, 140, 248, 0.5)');
      gradient.addColorStop(1, 'rgba(129, 140, 248, 0)');
      ctx.fillStyle = gradient;
      ctx.fill();
    }

    // Draw hover glow
    if (isHovered && !isCurrent) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, size + 5, 0, 2 * Math.PI);
      ctx.fillStyle = colors.glow;
      ctx.fill();
    }

    // Draw node
    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
    ctx.fillStyle = isCurrent || isHighlighted || isHovered ? colors.base : colors.border;
    ctx.fill();

    // Draw border
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.lineWidth = 0.5;
    ctx.stroke();

    // Draw label for current, hovered, or highlighted
    if ((isCurrent || isHovered || (isHighlighted && globalScale > 0.8)) && node.title) {
      const fontSize = Math.max(9, 11 / globalScale);
      const label = node.title.length > 16 ? node.title.slice(0, 15) + '…' : node.title;

      ctx.font = `500 ${fontSize}px Inter, system-ui, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';

      const textWidth = ctx.measureText(label).width;
      const padding = 3;
      const yOffset = size + 4;

      // Background pill
      ctx.fillStyle = 'rgba(5, 5, 5, 0.9)';
      ctx.beginPath();
      ctx.roundRect(
        node.x - textWidth / 2 - padding,
        node.y + yOffset,
        textWidth + padding * 2,
        fontSize + 3,
        2
      );
      ctx.fill();

      // Text
      ctx.fillStyle = '#f9fafb';
      ctx.fillText(label, node.x, node.y + yOffset + 1);
    }
  }, [selectedNoteId, highlightedNodeIds, hoveredNode]);

  // Custom link rendering
  const paintLink = useCallback((link, ctx) => {
    const start = link.source;
    const end = link.target;

    // Guard: Skip if coordinates are not yet initialized
    if (!Number.isFinite(start?.x) || !Number.isFinite(start?.y) ||
        !Number.isFinite(end?.x) || !Number.isFinite(end?.y)) {
      return;
    }

    const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
    const targetId = typeof link.target === 'object' ? link.target.id : link.target;
    const isConnectedToHovered = hoveredNode === sourceId || hoveredNode === targetId;

    const edgeColors = EDGE_COLORS[link.type] || EDGE_COLORS.default;

    // Glow for hovered connections
    if (isConnectedToHovered) {
      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      ctx.lineTo(end.x, end.y);
      ctx.strokeStyle = edgeColors.glow;
      ctx.lineWidth = 4;
      ctx.stroke();
    }

    // Main line
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
    ctx.strokeStyle = isConnectedToHovered ? edgeColors.highlight : edgeColors.base;
    ctx.lineWidth = isConnectedToHovered ? 1.5 : 1;
    ctx.stroke();
  }, [hoveredNode]);

  // Empty state
  if (!selectedNoteId) {
    return (
      <div className="brain-graph-preview brain-graph-preview--empty">
        <Network size={36} strokeWidth={1.5} />
        <p>Select a note to see connections</p>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="brain-graph-preview brain-graph-preview--loading">
        <div className="brain-graph-preview__spinner" />
        <p>Loading graph...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="brain-graph-preview brain-graph-preview--empty">
        <Network size={36} strokeWidth={1.5} />
        <p>Error loading graph</p>
        <span className="brain-graph-preview__error">{error.message}</span>
      </div>
    );
  }

  // No connections state
  if (!localGraphData.nodes.length) {
    return (
      <div className="brain-graph-preview brain-graph-preview--empty">
        <Network size={36} strokeWidth={1.5} />
        <p>No connections yet</p>
        <span className="brain-graph-preview__hint">Link notes with [[wikilinks]]</span>
      </div>
    );
  }

  return (
    <div className="brain-graph-preview">
      {/* Live indicator */}
      {isEditMode && editorWikilinks.length > 0 && (
        <div className="brain-graph-preview__live">
          <span className="brain-graph-preview__live-badge">Live</span>
          <span>Highlighting {highlightedNodeIds.size - 1} links</span>
        </div>
      )}

      {/* Graph canvas */}
      <div className="brain-graph-preview__canvas">
        <ForceGraph2D
          ref={graphRef}
          graphData={localGraphData}
          nodeId="id"
          nodeCanvasObject={paintNode}
          linkCanvasObject={paintLink}
          onNodeClick={handleNodeClick}
          onNodeHover={handleNodeHover}
          enableNodeDrag={true}
          enableZoomInteraction={true}
          enablePanInteraction={true}
          backgroundColor="transparent"
          warmupTicks={60}
          cooldownTicks={100}
          d3AlphaDecay={0.04}
          d3VelocityDecay={0.4}
        />
      </div>

      {/* Legend */}
      <div className="brain-graph-preview__legend">
        <div className="brain-graph-preview__legend-item">
          <span className="brain-graph-preview__dot brain-graph-preview__dot--current" />
          <span>Current</span>
        </div>
        <div className="brain-graph-preview__legend-item">
          <span className="brain-graph-preview__dot brain-graph-preview__dot--note" />
          <span>Notes</span>
        </div>
        <div className="brain-graph-preview__legend-item">
          <span className="brain-graph-preview__dot brain-graph-preview__dot--tag" />
          <span>Tags</span>
        </div>
        <div className="brain-graph-preview__legend-item">
          <span className="brain-graph-preview__dot brain-graph-preview__dot--image" />
          <span>Images</span>
        </div>
      </div>

      {/* Hint */}
      <div className="brain-graph-preview__footer">
        Click nodes to navigate
      </div>
    </div>
  );
}

export default BrainGraphPreview;
