/**
 * GraphCanvas - Force-directed graph canvas wrapper
 *
 * Wraps react-force-graph-2d with custom node/edge rendering.
 * Handles interactions and forwards events to parent.
 * Rendering logic is in useCanvasRenderers hook.
 */

import React, { useRef, useCallback, useEffect, useMemo, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { forceX, forceY } from 'd3-force';

import { getNodeSize } from '../utils/nodeRendering';
import { buildForceConfig } from '../utils/layoutPresets';
import { useCanvasRenderers } from '../hooks/useCanvasRenderers';
import { GraphTooltip } from './GraphTooltip';
import { ContextMenu } from './ContextMenu';
import { Minimap } from './Minimap';

import './GraphCanvas.css';

export function GraphCanvas({
  graphData,
  graphState,
  layout,
  filters,
  width,
  height,
  onViewChange,
}) {
  const graphRef = useRef();
  const [tooltip, setTooltip] = useState(null);

  // Canvas rendering callbacks (paintNode, paintLink)
  const { paintNode, paintLink, hoverRef, stopAnimation } = useCanvasRenderers(graphState, layout);

  // Connect layout ref
  useEffect(() => {
    if (graphRef.current) {
      layout.graphRef.current = graphRef.current;
    }
  }, [layout]);

  // Build force config from current preset (used for both useEffect and props)
  const forceConfig = useMemo(() => buildForceConfig(layout.preset), [layout.preset]);

  // Apply all forces imperatively from preset config
  useEffect(() => {
    if (!graphRef.current) return;
    const fg = graphRef.current;
    fg.d3Force('charge')?.strength(forceConfig.charge);
    fg.d3Force('link')?.distance(forceConfig.link.distance)?.strength(forceConfig.link.strength);
    // Replace default d3.forceCenter with forceX/forceY springs
    fg.d3Force('center', null);
    const cs = forceConfig.center.strength;
    fg.d3Force('centerX', forceX(0).strength(cs));
    fg.d3Force('centerY', forceY(0).strength(cs));
    fg.d3ReheatSimulation?.();
  }, [forceConfig]);

  // Filter visible nodes/edges
  const filteredData = useMemo(() => {
    if (!graphData) return { nodes: [], links: [] };
    const visibleNodes = graphData.nodes.filter(filters.isNodeVisible);
    const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));
    const visibleLinks = graphData.links.filter((link) => {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;
      return visibleNodeIds.has(sourceId) && visibleNodeIds.has(targetId) && filters.isEdgeVisible(link);
    });
    return { nodes: visibleNodes, links: visibleLinks };
  }, [graphData, filters]);

  // Pointer area for nodes (hit detection)
  const nodePointerAreaPaint = useCallback((node, color, ctx) => {
    const size = getNodeSize(node);
    ctx.beginPath();
    ctx.arc(node.x, node.y, size + 4, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
  }, []);

  // Double-click detection via timing (react-force-graph has no onNodeDoubleClick)
  const lastClickRef = useRef({ nodeId: null, time: 0 });
  const DOUBLE_CLICK_MS = 350;

  const handleNodeClick = useCallback((node, event) => {
    const now = Date.now();
    const last = lastClickRef.current;
    if (last.nodeId === node.id && now - last.time < DOUBLE_CLICK_MS) {
      // Double click detected
      graphState.handleNodeDoubleClick(node);
      lastClickRef.current = { nodeId: null, time: 0 };
      return;
    }
    lastClickRef.current = { nodeId: node.id, time: now };
    graphState.handleNodeClick(node, event);
  }, [graphState]);

  const handleNodeRightClick = useCallback((node, event) => {
    event.preventDefault?.();
    graphState.setContextMenu({ x: event.clientX || event.pageX, y: event.clientY || event.pageY, node });
  }, [graphState]);

  // Throttle tooltip updates
  const tooltipRafRef = useRef(null);

  const handleNodeHover = useCallback((node) => {
    hoverRef.current.nodeId = node?.id || null;
    if (tooltipRafRef.current) cancelAnimationFrame(tooltipRafRef.current);

    if (node && node.id && graphRef.current) {
      tooltipRafRef.current = requestAnimationFrame(() => {
        const [type] = node.id.split('-');
        const screenPos = graphRef.current?.graph2ScreenCoords(node.x, node.y);
        if (screenPos) {
          setTooltip({
            x: screenPos.x, y: screenPos.y,
            title: node.title || node.id,
            type: type || node.type || 'unknown',
            connections: node.val || node.connections || 0,
            community: node.metadata?.communityId != null ? node.metadata.communityColor : null,
            tagCount: type === 'tag' ? node.metadata?.note_count : null,
            imageSize: node.metadata?.width ? `${node.metadata.width}\u00d7${node.metadata.height}` : null,
            modified: node.metadata?.updated_at || node.metadata?.updatedAt,
            depth: node.depth,
          });
        }
      });
    } else {
      setTooltip(null);
    }
  }, [hoverRef]);

  const handleLinkClick = useCallback((link) => {
    graphState.handleEdgeClick(link);
  }, [graphState]);

  const handleBackgroundClick = useCallback(() => {
    graphState.clearSelection();
    graphState.setContextMenu(null);
    setTooltip(null);
  }, [graphState]);

  // Drag handlers
  const dragStartRef = useRef({ x: 0, y: 0 });

  const handleNodeDrag = useCallback((node) => {
    if (node && dragStartRef.current.x === 0) {
      dragStartRef.current = { x: node.x, y: node.y };
    }
  }, []);

  const handleNodeDragEnd = useCallback((node) => {
    if (node) {
      const dx = node.x - dragStartRef.current.x;
      const dy = node.y - dragStartRef.current.y;
      if (Math.sqrt(dx * dx + dy * dy) > 10) {
        node.fx = node.x;
        node.fy = node.y;
      }
      dragStartRef.current = { x: 0, y: 0 };
    }
  }, []);

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
        onNodeRightClick={handleNodeRightClick}
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
        d3AlphaDecay={forceConfig.alphaDecay}
        d3VelocityDecay={forceConfig.velocityDecay}
        d3AlphaMin={forceConfig.alphaMin}
        warmupTicks={50}
        cooldownTicks={200}
        onEngineStop={stopAnimation}
      />
      <GraphTooltip tooltip={tooltip} />
      <ContextMenu menu={graphState.contextMenu} graphState={graphState} onViewChange={onViewChange} />
      <Minimap graphRef={graphRef} graphData={filteredData} layout={layout} />
    </div>
  );
}

export default GraphCanvas;
