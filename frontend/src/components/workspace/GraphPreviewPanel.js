import React, { useMemo, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useWorkspaceState } from '../../hooks/useWorkspaceState';
import { useContentAnalysis } from '../../hooks/useContentAnalysis';
import { Network } from 'lucide-react';
import ForceGraph2D from 'react-force-graph-2d';
import { API_URL } from '../../utils/api';
import './ContextPanels.css';
import './GraphPreviewPanel.css';

// Helper to detect light theme
const isLightTheme = () => {
  if (typeof document === 'undefined') return false;
  return document.documentElement.getAttribute('data-theme') === 'light';
};

/**
 * GraphPreviewPanel - Mini force-directed graph of connected notes (Phase 4)
 * Shows local graph view: current note + directly connected notes
 * Highlights referenced notes from editor in real-time
 */
function GraphPreviewPanel() {
  const { selectedNoteId, selectNote, editorState } = useWorkspaceState();
  const graphRef = useRef();

  // Fetch graph data using React Query
  const { data: graphData, isLoading: loading, error } = useQuery({
    queryKey: ['graphData', selectedNoteId],
    queryFn: async () => {
      if (!selectedNoteId) return null;

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token');
      }

      const response = await fetch(`${API_URL}/graph/data`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch graph data');
      }

      return response.json();
    },
    enabled: !!selectedNoteId,
    staleTime: 30000,
    refetchOnWindowFocus: false,
  });

  // Real-time analysis for highlighting referenced notes
  const editorAnalysis = useContentAnalysis(editorState.editorInstance, editorState.noteTitle);

  // Filter graph data to show only local connections (1-hop from current note)
  const localGraphData = useMemo(() => {
    if (!graphData || !selectedNoteId) {
      return { nodes: [], links: [] };
    }

    // Find the current note node
    const currentNode = graphData.nodes.find(n => n.id === `note-${selectedNoteId}`);
    if (!currentNode) {
      return { nodes: [], links: [] };
    }

    // Find all links connected to current note
    const connectedLinks = graphData.links.filter(
      link =>
        (typeof link.source === 'object' ? link.source.id : link.source) === currentNode.id ||
        (typeof link.target === 'object' ? link.target.id : link.target) === currentNode.id
    );

    // Find all connected node IDs
    const connectedNodeIds = new Set([currentNode.id]);
    connectedLinks.forEach(link => {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;
      connectedNodeIds.add(sourceId);
      connectedNodeIds.add(targetId);
    });

    // Filter nodes to only include connected ones
    const localNodes = graphData.nodes.filter(n => connectedNodeIds.has(n.id));

    return { nodes: localNodes, links: connectedLinks };
  }, [graphData, selectedNoteId]);

  // Zoom to fit when graph data changes
  useEffect(() => {
    if (graphRef.current && localGraphData.nodes.length > 0) {
      // Immediate centering and zoom
      const timer1 = setTimeout(() => {
        if (graphRef.current) {
          // Reset zoom and center
          graphRef.current.zoom(1, 0);
          graphRef.current.centerAt(0, 0, 0);
        }
      }, 50);

      // Let physics settle
      const timer2 = setTimeout(() => {
        if (graphRef.current) {
          graphRef.current.zoomToFit(800, 100);
        }
      }, 500);

      // Final adjustment after physics stops
      const timer3 = setTimeout(() => {
        if (graphRef.current) {
          graphRef.current.zoomToFit(400, 100);
        }
      }, 1500);

      return () => {
        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);
      };
    }
  }, [localGraphData]);

  // Highlight nodes that are referenced in the editor
  const highlightedNodeIds = useMemo(() => {
    if (!editorState.isEditMode || !editorAnalysis.wikilinks.length) {
      return new Set([`note-${selectedNoteId}`]); // Only highlight current note
    }

    const highlighted = new Set([`note-${selectedNoteId}`]);

    // Add referenced wikilinks
    editorAnalysis.wikilinks.forEach(wikilink => {
      // Find node by title
      const node = localGraphData.nodes.find(
        n => n.type === 'note' && n.title === wikilink
      );
      if (node) {
        highlighted.add(node.id);
      }
    });

    return highlighted;
  }, [editorState.isEditMode, editorAnalysis.wikilinks, localGraphData.nodes, selectedNoteId]);

  // Neural Glass node colors
  const getNodeColor = (node) => {
    const isHighlighted = highlightedNodeIds.has(node.id);
    const isCurrent = node.id === `note-${selectedNoteId}`;

    // Neural Glass semantic colors
    if (isCurrent) {
      return '#818cf8'; // Violet - current/AI accent (highlighted central node)
    }
    if (node.type === 'tag') {
      return isHighlighted ? '#34d399' : '#10b981'; // Emerald - link/tag accent
    }
    if (node.type === 'image') {
      return isHighlighted ? '#22d3ee' : '#06b6d4'; // Cyan - image accent
    }
    // Notes - Amber accent
    return isHighlighted ? '#fbbf24' : '#f59e0b';
  };

  // Node size based on type
  const getNodeSize = (node) => {
    if (node.id === `note-${selectedNoteId}`) return 8; // Current note is larger
    if (node.type === 'tag') return 5;
    if (node.type === 'image') return 6;
    return 6; // Other notes
  };

  const handleNodeClick = (node) => {
    if (node.type === 'note') {
      const noteId = parseInt(node.id.replace('note-', ''));
      selectNote(noteId);
    }
  };

  if (!selectedNoteId) {
    return (
      <div className="graph-preview-panel">
        <div className="panel-empty">
          <Network size={40} className="empty-icon" />
          <p>Select a note to see graph</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="graph-preview-panel">
        <div className="panel-loading">
          <div className="loading-spinner"></div>
          <p>Loading graph...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="graph-preview-panel">
        <div className="panel-empty">
          <Network size={40} className="empty-icon" />
          <p>Error loading graph</p>
          <span className="empty-subtitle">{error.message}</span>
        </div>
      </div>
    );
  }

  if (!localGraphData.nodes.length) {
    return (
      <div className="graph-preview-panel">
        <div className="panel-empty">
          <Network size={40} className="empty-icon" />
          <p>No connections</p>
          <span className="empty-subtitle">This note has no connections yet</span>
        </div>
      </div>
    );
  }

  return (
    <div className="graph-preview-panel">
      {editorState.isEditMode && editorAnalysis.wikilinks.length > 0 && (
        <div className="graph-live-indicator">
          <span className="live-badge">Live</span>
          <span className="live-text">
            Highlighting {highlightedNodeIds.size - 1} referenced notes
          </span>
        </div>
      )}

      <div className="graph-preview-container">
        <ForceGraph2D
          ref={graphRef}
          graphData={localGraphData}
          nodeId="id"
          nodeLabel="title"
          nodeVal={getNodeSize}
          linkColor={() => isLightTheme() ? 'rgba(100, 116, 139, 0.4)' : 'rgba(255, 255, 255, 0.15)'}
          linkWidth={1.5}
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={2}
          linkDirectionalParticleColor={() => 'rgba(129, 140, 248, 0.6)'}
          onNodeClick={handleNodeClick}
          enableNodeDrag={true}
          enableZoomInteraction={true}
          enablePanInteraction={true}
          warmupTicks={80}
          cooldownTicks={120}
          d3AlphaDecay={0.03}
          d3VelocityDecay={0.4}
          nodeCanvasObjectMode={() => 'replace'}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const color = getNodeColor(node);
            const size = getNodeSize(node);
            const isCurrent = node.id === `note-${selectedNoteId}`;

            // Draw glow effect for current node
            if (isCurrent) {
              ctx.beginPath();
              ctx.arc(node.x, node.y, size + 4, 0, 2 * Math.PI);
              const gradient = ctx.createRadialGradient(node.x, node.y, size, node.x, node.y, size + 8);
              gradient.addColorStop(0, 'rgba(129, 140, 248, 0.4)');
              gradient.addColorStop(1, 'rgba(129, 140, 248, 0)');
              ctx.fillStyle = gradient;
              ctx.fill();
            }

            // Draw node circle
            ctx.beginPath();
            ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();

            // Draw subtle border - theme aware
            const lightMode = isLightTheme();
            ctx.strokeStyle = lightMode ? 'rgba(0, 0, 0, 0.2)' : 'rgba(255, 255, 255, 0.3)';
            ctx.lineWidth = 0.5;
            ctx.stroke();

            // Draw label
            const label = node.title || node.id;
            const fontSize = Math.max(10, 12 / globalScale);
            ctx.font = `600 ${fontSize}px Inter, system-ui, sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';

            // Draw text background pill - theme aware
            const textWidth = ctx.measureText(label).width;
            const padding = 4;
            const pillHeight = fontSize + 4;
            const yOffset = size + 6;

            ctx.fillStyle = lightMode ? 'rgba(255, 255, 255, 0.95)' : 'rgba(10, 10, 10, 0.85)';
            ctx.beginPath();
            ctx.roundRect(
              node.x - textWidth / 2 - padding,
              node.y + yOffset,
              textWidth + padding * 2,
              pillHeight,
              3
            );
            ctx.fill();

            // Draw text - theme aware
            ctx.fillStyle = lightMode ? '#1f2937' : '#f9fafb';
            ctx.fillText(label, node.x, node.y + yOffset + 2);
          }}
        />
      </div>

      <div className="graph-preview-legend">
        <div className="legend-item">
          <div className="legend-dot" style={{ background: '#818cf8', boxShadow: '0 0 6px #818cf8' }}></div>
          <span>Current</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ background: '#fbbf24' }}></div>
          <span>Notes</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ background: '#34d399' }}></div>
          <span>Tags</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ background: '#22d3ee' }}></div>
          <span>Images</span>
        </div>
      </div>

      <div className="graph-preview-hint">
        <span>💡 Click nodes to navigate</span>
      </div>
    </div>
  );
}

export default GraphPreviewPanel;
