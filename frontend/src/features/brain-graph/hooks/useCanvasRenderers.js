/**
 * useCanvasRenderers - Canvas rendering callbacks for GraphCanvas
 *
 * Extracts paintNode and paintLink from GraphCanvas to keep file sizes manageable.
 * Contains LOD-aware node rendering with depth dimming, image thumbnails,
 * and edge rendering with weight-based opacity and semantic glow.
 */

import { useCallback, useRef, useEffect } from 'react';
import { isLightTheme, getNodeColor, getNodeSize, renderNodeLabel, renderImageNode } from '../utils/nodeRendering';
import { imageCache } from '../utils/imageCache';
import { getEdgeColor, getEdgeWidth, getEdgeDash } from '../utils/edgeRendering';
import { getLODSettings } from '../utils/layoutPresets';

const PULSE_DURATION = 2000;

export function useCanvasRenderers(graphState, layout) {
  const hoverRef = useRef({ nodeId: null });
  const themeRef = useRef(isLightTheme());
  const animationRef = useRef({ active: false, frameId: null, phase: 0, startTime: 0 });

  useEffect(() => { themeRef.current = isLightTheme(); });

  // Pulse animation for focused node
  useEffect(() => {
    const needsAnimation = !!graphState.focusNodeId;
    if (needsAnimation && !animationRef.current.active) {
      animationRef.current.active = true;
      animationRef.current.startTime = Date.now();
      const animate = () => {
        if (!animationRef.current.active) return;
        const elapsed = Date.now() - animationRef.current.startTime;
        animationRef.current.phase = (elapsed % PULSE_DURATION) / PULSE_DURATION;
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
      if (animationRef.current.frameId) cancelAnimationFrame(animationRef.current.frameId);
    };
  }, [graphState.focusNodeId]);

  const paintNode = useCallback((node, ctx, globalScale) => {
    const isSelected = graphState.selectedNode?.id === node.id;
    const isHovered = hoverRef.current.nodeId === node.id;
    const isFocused = graphState.focusNodeId === node.id || node.isFocus;
    const isPinned = graphState.isPinned(node.id);
    const isHub = node.isHub;
    const lod = getLODSettings(globalScale);
    const colors = getNodeColor(node);
    const size = Math.max(getNodeSize(node), lod.nodeMinSize);

    // Depth-aware opacity
    const depthOpacity = node.depth != null && node.depth < 99
      ? [1.0, 0.85, 0.65, 0.45][Math.min(node.depth, 3)] : 1.0;
    if (depthOpacity < 1.0) ctx.globalAlpha = depthOpacity;

    const pulseScale = Math.sin(animationRef.current.phase * Math.PI * 2) * 0.5 + 0.5;

    // Pulse ring for focused node
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

    // Glow for selected/hovered
    if (isSelected || isHovered) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, size + 8, 0, 2 * Math.PI);
      ctx.fillStyle = colors.glow;
      ctx.fill();
    }

    // Image thumbnail at medium+ zoom
    const nodeType = node.id?.split('-')[0];
    let drewThumbnail = false;
    if (nodeType === 'image' && lod.showHubLabels) {
      const img = imageCache.get(node.id);
      if (img) drewThumbnail = renderImageNode(ctx, node, size, img);
    }

    // Normal circle (skip if thumbnail drawn)
    if (!drewThumbnail) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
      ctx.fillStyle = isSelected || isFocused ? colors.base : colors.border;
      ctx.fill();
      ctx.strokeStyle = colors.base;
      ctx.lineWidth = isSelected ? 2 : 1;
      ctx.stroke();
    }

    // Pin indicator
    if (isPinned && lod.showHubLabels) {
      ctx.beginPath();
      ctx.arc(node.x, node.y - size - 4, 3, 0, 2 * Math.PI);
      ctx.fillStyle = themeRef.current ? '#374151' : '#f9fafb';
      ctx.fill();
    }

    // Search highlight ring (amber dashed)
    if (graphState.highlightedNodeIds?.has(node.id)) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, size + 6, 0, 2 * Math.PI);
      ctx.strokeStyle = '#fbbf24';
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 3]);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Connection badge (top-right, medium+ zoom, >2 connections)
    if (lod.showHubLabels && (node.connections || 0) > 2) {
      const bR = Math.max(5, 7 / globalScale), bX = node.x + size * 0.7, bY = node.y - size * 0.7;
      ctx.beginPath(); ctx.arc(bX, bY, bR, 0, 2 * Math.PI);
      ctx.fillStyle = 'rgba(99, 102, 241, 0.85)'; ctx.fill();
      ctx.font = `bold ${Math.max(7, 9 / globalScale)}px Inter, sans-serif`;
      ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(String(node.connections), bX, bY);
    }

    // Label
    const shouldShowLabel = isSelected || isHovered || isFocused ||
      (isHub && lod.showHubLabels) || (lod.showAllLabels && node.title);
    if (shouldShowLabel && node.title) {
      renderNodeLabel(ctx, node, globalScale, {
        isSelected, isHovered, isFocused,
        showAllLabels: lod.showAllLabels, isLight: themeRef.current,
      });
    }

    if (depthOpacity < 1.0) ctx.globalAlpha = 1.0;
  }, [graphState.selectedNode, graphState.focusNodeId, graphState.isPinned, graphState.highlightedNodeIds]);

  const paintLink = useCallback((link, ctx, globalScale) => {
    const lod = getLODSettings(globalScale);
    const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
    const targetId = typeof link.target === 'object' ? link.target.id : link.target;
    const isHighlighted = hoverRef.current.nodeId === sourceId || hoverRef.current.nodeId === targetId;
    const isSelected = graphState.selectedEdge === link;

    if (!lod.renderEdges && !isHighlighted && !isSelected) return;

    const colors = getEdgeColor(link, themeRef.current);
    const edgeWidth = Math.max(getEdgeWidth(link), lod.edgeMinWidth);
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

    // Highlight glow
    if (isSelected || isHighlighted) {
      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      useCurved ? ctx.quadraticCurveTo(ctrlX, ctrlY, end.x, end.y) : ctx.lineTo(end.x, end.y);
      ctx.strokeStyle = colors.glow;
      ctx.lineWidth = edgeWidth + 6;
      ctx.stroke();
    }

    // Weight-based opacity
    const weight = link.weight ?? 0.5;
    if (!isSelected && !isHighlighted) {
      ctx.globalAlpha = Math.max(0.3, Math.min(1.0, weight));
    }

    // Semantic glow for strong connections
    if (link.type === 'semantic' && weight > 0.5 && (isHighlighted || isSelected)) {
      ctx.save();
      ctx.shadowColor = colors.glow;
      ctx.shadowBlur = weight * 8;
      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      useCurved ? ctx.quadraticCurveTo(ctrlX, ctrlY, end.x, end.y) : ctx.lineTo(end.x, end.y);
      ctx.strokeStyle = colors.highlight;
      ctx.lineWidth = edgeWidth + 2;
      ctx.stroke();
      ctx.restore();
    }

    // Draw edge
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    useCurved ? ctx.quadraticCurveTo(ctrlX, ctrlY, end.x, end.y) : ctx.lineTo(end.x, end.y);
    ctx.strokeStyle = isSelected || isHighlighted ? colors.highlight : colors.base;
    ctx.lineWidth = isSelected ? edgeWidth + 1 : edgeWidth;
    ctx.setLineDash(dash);
    ctx.stroke();
    ctx.setLineDash([]);

    // Edge label at midpoint when highlighted/selected
    if (isHighlighted || isSelected) {
      const lx = useCurved ? ctrlX : midX, ly = useCurved ? ctrlY : midY;
      const label = link.type === 'semantic' ? `${Math.round((weight || 0) * 100)}%` : link.type || 'link';
      const fs = Math.max(9, 10 / globalScale);
      ctx.font = `${fs}px Inter, sans-serif`;
      const tw = ctx.measureText(label).width, p = 4;
      ctx.fillStyle = themeRef.current ? 'rgba(255,255,255,0.85)' : 'rgba(0,0,0,0.75)';
      ctx.beginPath();
      ctx.roundRect(lx - tw / 2 - p, ly - fs / 2 - 2, tw + p * 2, fs + 4, 3);
      ctx.fill();
      ctx.fillStyle = themeRef.current ? '#1f2937' : '#e5e7eb';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(label, lx, ly);
    }

    ctx.globalAlpha = 1.0;
  }, [graphState.selectedEdge, layout.edgeBundling]);

  const stopAnimation = useCallback(() => {
    if (animationRef.current.active) {
      animationRef.current.active = false;
      if (animationRef.current.frameId) {
        cancelAnimationFrame(animationRef.current.frameId);
        animationRef.current.frameId = null;
      }
    }
  }, []);

  return { paintNode, paintLink, hoverRef, stopAnimation };
}
