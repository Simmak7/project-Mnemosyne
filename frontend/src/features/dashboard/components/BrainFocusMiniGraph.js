/**
 * BrainFocusMiniGraph - Small force-directed graph preview
 *
 * Fetches depth=1 neighborhood for the focused node and renders
 * a compact 120px canvas. Zoom/pan disabled (static preview).
 * Click navigates to the Brain graph tab.
 */
import React, { useRef, useCallback, useEffect } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { useLocalGraph } from '../../brain-graph/hooks/useGraphData';
import './BrainFocusMiniGraph.css';

const NODE_COLORS = {
  note: '#fbbf24',
  tag: '#34d399',
  image: '#22d3ee',
  entity: '#818cf8',
};

const GRAPH_HEIGHT = 120;

function BrainFocusMiniGraph({ focusNodeId, onTabChange }) {
  const graphRef = useRef();
  const { data } = useLocalGraph(focusNodeId, 1);

  const graphData = React.useMemo(() => {
    if (!data?.nodes) return { nodes: [], links: [] };
    return {
      nodes: data.nodes.map(n => ({ ...n })),
      links: (data.edges || data.links || []).map(e => ({
        source: e.source,
        target: e.target,
      })),
    };
  }, [data]);

  // Disable zoom/pan and settle quickly
  useEffect(() => {
    const fg = graphRef.current;
    if (!fg) return;
    fg.d3Force('charge')?.strength(-20);
    fg.d3Force('link')?.distance(25);
    fg.zoom(1.5, 0);
  }, [graphData]);

  const paintNode = useCallback((node, ctx) => {
    const isFocus = node.id === focusNodeId;
    const r = isFocus ? 6 : 4;
    const type = (node.id || '').split('-')[0];
    ctx.beginPath();
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
    ctx.fillStyle = NODE_COLORS[type] || '#818cf8';
    ctx.fill();
  }, [focusNodeId]);

  const handleClick = useCallback(() => {
    onTabChange?.('graph');
  }, [onTabChange]);

  if (!focusNodeId || graphData.nodes.length === 0) return null;

  return (
    <div className="brain-mini-graph" onClick={handleClick} title="View in Brain Graph">
      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        width={260}
        height={GRAPH_HEIGHT}
        nodeCanvasObject={paintNode}
        nodePointerAreaPaint={(node, color, ctx) => {
          ctx.beginPath();
          ctx.arc(node.x, node.y, 6, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        }}
        linkColor={() => 'rgba(255,255,255,0.15)'}
        linkWidth={1}
        enableZoomInteraction={false}
        enablePanInteraction={false}
        enableNodeDrag={false}
        d3VelocityDecay={0.8}
        d3AlphaDecay={0.1}
        warmupTicks={30}
        cooldownTicks={20}
      />
    </div>
  );
}

export default BrainFocusMiniGraph;
