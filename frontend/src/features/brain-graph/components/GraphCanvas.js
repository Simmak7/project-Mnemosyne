/**
 * GraphCanvas - Force-directed graph canvas wrapper
 *
 * Wraps react-force-graph-2d with custom node/edge rendering.
 * Handles interactions and forwards events to parent.
 */

import React, { useRef, useCallback, useEffect, useMemo, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { forceX, forceY } from 'd3-force';

import { getNodeColor, getNodeSize, renderNodeLabel } from '../utils/nodeRendering';
import { getEdgeColor, getEdgeWidth, getEdgeDash } from '../utils/edgeRendering';
import { buildForceConfig, getLODSettings } from '../utils/layoutPresets';

import './GraphCanvas.css';

// Animation timing constants
const PULSE_DURATION = 2000; // 2 second pulse cycle

export function GraphCanvas({
  graphData,
  graphState,
  layout,
  filters,
  width,
  height,
}) {
  const graphRef = useRef();
  const [tooltip, setTooltip] = useState(null);

  // Use ref for hover state to avoid re-renders that cause jumping
  const hoverRef = useRef({ nodeId: null });

  // Animation ref for pulse effect (updates without React re-renders)
  const animationRef = useRef({
    active: false,
    frameId: null,
    phase: 0,
    startTime: 0
  });

  // Animation loop for focused node pulse
  // Note: Pulse animation updates ref only, visible during natural canvas repaints
  useEffect(() => {
    const needsAnimation = !!graphState.focusNodeId;

    if (needsAnimation && !animationRef.current.active) {
      animationRef.current.active = true;
      animationRef.current.startTime = Date.now();

      const animate = () => {
        if (!animationRef.current.active) return;

        const elapsed = Date.now() - animationRef.current.startTime;
        animationRef.current.phase = (elapsed % PULSE_DURATION) / PULSE_DURATION;

        // Update ref only - don't force React re-render
        // Pulse will show during natural canvas repaints (drag, zoom, hover)
        animationRef.current.frameId = requestAnimationFrame(animate);
      };

      animationRef.current.frameId = requestAnimationFrame(animate);
    } else if (!needsAnimation && animationRef.current.active) {
      animationRef.current.active = false;
      if (animationRef.current.frameId) {
        cancelAnimationFrame(animationRef.current.frameId);
        animationRef.current.frameId = null;
      }
      animationRef.current.phase = 0;
    }

    return () => {
      animationRef.current.active = false;
      if (animationRef.current.frameId) {
        cancelAnimationFrame(animationRef.current.frameId);
      }
    };
  }, [graphState.focusNodeId]);

  // Connect layout ref
  useEffect(() => {
    if (graphRef.current) {
      layout.graphRef.current = graphRef.current;
    }
  }, [layout]);

  // Apply force configuration
  useEffect(() => {
    if (!graphRef.current) return;

    const config = buildForceConfig(layout.preset);
    const fg = graphRef.current;

    // Configure basic forces
    fg.d3Force('charge')?.strength(config.charge);
    fg.d3Force('link')
      ?.distance(config.link.distance)
      ?.strength(config.link.strength);

    // Add X and Y centering forces with adjustable strength
    // forceCenter() has no strength param, so we use forceX/forceY instead
    // This pulls ALL nodes toward center, preventing isolated nodes from flying away
    fg.d3Force('centerX', forceX(0).strength(0.15));
    fg.d3Force('centerY', forceY(0).strength(0.15));
  }, [layout.preset]);

  // Filter visible nodes/edges
  const filteredData = useMemo(() => {
    if (!graphData) return { nodes: [], links: [] };

    const visibleNodes = graphData.nodes.filter(filters.isNodeVisible);
    const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));

    const visibleLinks = graphData.links.filter((link) => {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;

      return (
        visibleNodeIds.has(sourceId) &&
        visibleNodeIds.has(targetId) &&
        filters.isEdgeVisible(link)
      );
    });

    return { nodes: visibleNodes, links: visibleLinks };
  }, [graphData, filters]);

  // Custom node rendering with LOD (Level of Detail)
  const paintNode = useCallback((node, ctx, globalScale) => {
    const isSelected = graphState.selectedNode?.id === node.id;
    // Use ref for hover to avoid re-renders
    const isHovered = hoverRef.current.nodeId === node.id;
    const isFocused = graphState.focusNodeId === node.id || node.isFocus;
    const isPinned = graphState.isPinned(node.id);
    const isHub = node.isHub;

    // Get LOD settings for current zoom level
    const lod = getLODSettings(globalScale);

    const colors = getNodeColor(node);
    const baseSize = getNodeSize(node);
    const size = Math.max(baseSize, lod.nodeMinSize);

    // Get animation phase from ref
    const pulseScale = Math.sin(animationRef.current.phase * Math.PI * 2) * 0.5 + 0.5;

    // Draw animated pulse ring for focused node
    if (isFocused) {
      const pulseRadius = size + 8 + pulseScale * 12;
      const pulseOpacity = 0.3 * (1 - pulseScale);
      ctx.beginPath();
      ctx.arc(node.x, node.y, pulseRadius, 0, 2 * Math.PI);
      ctx.strokeStyle = colors.base.replace(')', `, ${pulseOpacity})`).replace('rgb', 'rgba');
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(node.x, node.y, size + 5, 0, 2 * Math.PI);
      ctx.strokeStyle = colors.base;
      ctx.lineWidth = 2 + pulseScale;
      ctx.stroke();
    }

    // Draw glow for selected/hovered nodes
    if (isSelected || isHovered) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, size + 8, 0, 2 * Math.PI);
      ctx.fillStyle = colors.glow;
      ctx.fill();
    }

    // Draw node
    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
    ctx.fillStyle = isSelected || isFocused ? colors.base : colors.border;
    ctx.fill();
    ctx.strokeStyle = colors.base;
    ctx.lineWidth = isSelected ? 2 : 1;
    ctx.stroke();

    // Draw pin indicator
    if (isPinned && lod.showHubLabels) {
      ctx.beginPath();
      ctx.arc(node.x, node.y - size - 4, 3, 0, 2 * Math.PI);
      ctx.fillStyle = '#f9fafb';
      ctx.fill();
    }

    // Draw label
    const shouldShowLabel = isSelected || isHovered || isFocused ||
      (isHub && lod.showHubLabels) || (lod.showAllLabels && node.title);

    if (shouldShowLabel && node.title) {
      renderNodeLabel(ctx, node, globalScale, {
        isSelected,
        isHovered,
        isFocused,
        showAllLabels: lod.showAllLabels,
      });
    }
  }, [graphState.selectedNode, graphState.focusNodeId, graphState.isPinned]);

  // Custom link rendering
  const paintLink = useCallback((link, ctx, globalScale) => {
    const lod = getLODSettings(globalScale);

    const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
    const targetId = typeof link.target === 'object' ? link.target.id : link.target;

    // Use ref for hover
    const isHighlighted =
      hoverRef.current.nodeId === sourceId ||
      hoverRef.current.nodeId === targetId;
    const isSelected = graphState.selectedEdge === link;

    if (!lod.renderEdges && !isHighlighted && !isSelected) {
      return;
    }

    const colors = getEdgeColor(link);
    const baseWidth = getEdgeWidth(link);
    const edgeWidth = Math.max(baseWidth, lod.edgeMinWidth);
    const dash = getEdgeDash(link);

    const start = link.source;
    const end = link.target;

    const useCurved = layout.edgeBundling;
    const midX = (start.x + end.x) / 2;
    const midY = (start.y + end.y) / 2;
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const len = Math.sqrt(dx * dx + dy * dy) || 1;
    const curvature = useCurved ? Math.min(len * 0.15, 30) : 0;
    const ctrlX = midX - (dy / len) * curvature;
    const ctrlY = midY + (dx / len) * curvature;

    // Draw glow for highlighted edges
    if (isSelected || isHighlighted) {
      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      if (useCurved) {
        ctx.quadraticCurveTo(ctrlX, ctrlY, end.x, end.y);
      } else {
        ctx.lineTo(end.x, end.y);
      }
      ctx.strokeStyle = colors.glow;
      ctx.lineWidth = edgeWidth + 6;
      ctx.stroke();
    }

    // Draw edge
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    if (useCurved) {
      ctx.quadraticCurveTo(ctrlX, ctrlY, end.x, end.y);
    } else {
      ctx.lineTo(end.x, end.y);
    }
    ctx.strokeStyle = isSelected || isHighlighted ? colors.highlight : colors.base;
    ctx.lineWidth = isSelected ? edgeWidth + 1 : edgeWidth;
    ctx.setLineDash(dash);
    ctx.stroke();
    ctx.setLineDash([]);
  }, [graphState.selectedEdge, layout.edgeBundling]);

  // Define pointer area for nodes (important for hover detection)
  const nodePointerAreaPaint = useCallback((node, color, ctx) => {
    const size = getNodeSize(node);
    ctx.beginPath();
    ctx.arc(node.x, node.y, size + 4, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
  }, []);

  // Event handlers
  const handleNodeClick = useCallback((node, event) => {
    graphState.handleNodeClick(node, event);
  }, [graphState]);

  const handleNodeDoubleClick = useCallback((node) => {
    graphState.handleNodeDoubleClick(node);
  }, [graphState]);

  // Handle hover without triggering React re-renders
  // IMPORTANT: Don't call graphState.handleNodeHover - it causes re-renders that restart simulation
  const handleNodeHover = useCallback((node, prevNode) => {
    // Update ref only (no re-render, no state updates)
    hoverRef.current.nodeId = node?.id || null;

    // Update tooltip (local state only - doesn't affect ForceGraph2D)
    if (node && node.id) {
      const [type] = node.id.split('-');
      setTooltip({
        x: node.x,
        y: node.y,
        title: node.title || node.id,
        type: type || node.type || 'unknown',
        connections: node.val || node.connections || 0,
      });
    } else {
      setTooltip(null);
    }
  }, []);

  const handleLinkClick = useCallback((link) => {
    graphState.handleEdgeClick(link);
  }, [graphState]);

  const handleBackgroundClick = useCallback(() => {
    graphState.clearSelection();
    setTooltip(null);
  }, [graphState]);

  // Track drag start position to detect if node was actually moved
  const dragStartRef = useRef({ x: 0, y: 0 });

  // Handle node drag start - record initial position
  const handleNodeDrag = useCallback((node) => {
    if (node && dragStartRef.current.x === 0) {
      dragStartRef.current = { x: node.x, y: node.y };
    }
  }, []);

  // Handle node drag end - only pin if significantly moved
  const handleNodeDragEnd = useCallback((node) => {
    if (node) {
      const dx = node.x - dragStartRef.current.x;
      const dy = node.y - dragStartRef.current.y;
      const distance = Math.sqrt(dx * dx + dy * dy);

      // Only pin if dragged more than 10 pixels (intentional move)
      if (distance > 10) {
        node.fx = node.x;
        node.fy = node.y;
      }
      // Reset drag start
      dragStartRef.current = { x: 0, y: 0 };
    }
  }, []);

  // Engine stop handler - simulation naturally settles
  const handleEngineStop = useCallback(() => {
    // Let simulation settle naturally
  }, []);

  // Empty state
  if (!filteredData.nodes.length) {
    return (
      <div className="graph-canvas graph-canvas--empty">
        <p>No nodes to display</p>
      </div>
    );
  }

  return (
    <div className="graph-canvas">
      <ForceGraph2D
        ref={graphRef}
        graphData={filteredData}
        width={width}
        height={height}
        backgroundColor="transparent"
        nodeCanvasObject={paintNode}
        nodePointerAreaPaint={nodePointerAreaPaint}
        linkCanvasObject={paintLink}
        onNodeClick={handleNodeClick}
        onNodeRightClick={handleNodeDoubleClick}
        onNodeHover={handleNodeHover}
        onNodeDrag={handleNodeDrag}
        onNodeDragEnd={handleNodeDragEnd}
        onLinkClick={handleLinkClick}
        onBackgroundClick={handleBackgroundClick}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        minZoom={0.1}
        maxZoom={5}
        cooldownTicks={100}
        onEngineStop={handleEngineStop}
      />

      {/* Tooltip */}
      {tooltip && (
        <div
          className="graph-canvas__tooltip"
          style={{
            left: `calc(50% + ${tooltip.x}px)`,
            top: `calc(50% + ${tooltip.y - 40}px)`,
          }}
        >
          <div className="graph-canvas__tooltip-title">{tooltip.title}</div>
          <div className="graph-canvas__tooltip-meta">
            <span className="graph-canvas__tooltip-type">{tooltip.type}</span>
            {tooltip.connections > 0 && (
              <span className="graph-canvas__tooltip-connections">
                {tooltip.connections} connections
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default GraphCanvas;
