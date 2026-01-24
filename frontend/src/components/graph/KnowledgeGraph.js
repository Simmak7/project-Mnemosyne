import React, { useState, useEffect, useCallback, useRef } from 'react';
// Import AFRAME first to ensure it's available as a global before force-graph loads
import 'aframe';
import { ForceGraph2D } from 'react-force-graph';
import { Sparkles, HelpCircle } from 'lucide-react';
import useDebounce from '../../hooks/useDebounce';
import GraphControls from './GraphControls';
import NodePreview from './NodePreview';
import GraphHelp from './GraphHelp';
import RAGChat from '../../features/rag_chat/components/RAGChat';
import { transformToGraphData } from '../../utils/graphDataTransform';
import './KnowledgeGraph.css';

/**
 * Interactive force-directed knowledge graph visualization
 *
 * Features:
 * - WebGL-powered rendering for 1000+ nodes
 * - Zoom, pan, and drag interactions
 * - Node types: Notes (blue circles), Tags (orange hexagons), Images (thumbnails)
 * - Edge types: Wikilinks (solid), Tag relationships (dashed)
 * - Search highlight and focus
 * - Cluster detection with auto-coloring
 */
function KnowledgeGraph({ onNavigateToNote, onNavigateToImage, onNavigateToTag }) {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showChat, setShowChat] = useState(false);
  const [chatContext, setChatContext] = useState(null);
  const [showHelp, setShowHelp] = useState(false);
  const [filters, setFilters] = useState({
    showNotes: true,
    showTags: true,
    showImages: true,
    showWikilinks: true,
    showTagLinks: true,
    showImageLinks: true,
  });

  const graphRef = useRef();
  const debouncedSearchTerm = useDebounce(searchTerm, 300);

  // Fetch graph data from API
  const fetchGraphData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('token');

      if (!token) {
        throw new Error('No authentication token found');
      }

      // Fetch all notes with their relationships (enhanced with tags, wikilinks, backlinks)
      const notesResponse = await fetch('http://localhost:8000/notes-enhanced/', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!notesResponse.ok) {
        if (notesResponse.status === 401 || notesResponse.status === 403) {
          localStorage.removeItem('token');
          localStorage.removeItem('username');
          window.location.reload();
          return;
        }
        throw new Error('Failed to fetch notes');
      }

      const notes = await notesResponse.json();

      // Fetch all tags
      const tagsResponse = await fetch('http://localhost:8000/tags/', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      const tags = tagsResponse.ok ? await tagsResponse.json() : [];

      // Fetch all images
      const imagesResponse = await fetch('http://localhost:8000/images/', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      const images = imagesResponse.ok ? await imagesResponse.json() : [];

      // Transform data into graph format
      const graphData = transformToGraphData(notes, tags, images);
      setGraphData(graphData);
    } catch (err) {
      console.error('Error fetching graph data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchGraphData();
  }, [fetchGraphData]);

  // Filter graph data based on active filters
  const filteredGraphData = React.useMemo(() => {
    if (!graphData.nodes.length) return graphData;

    const filteredNodes = graphData.nodes.filter((node) => {
      if (node.type === 'note' && !filters.showNotes) return false;
      if (node.type === 'tag' && !filters.showTags) return false;
      if (node.type === 'image' && !filters.showImages) return false;
      return true;
    });

    const nodeIds = new Set(filteredNodes.map((n) => n.id));

    // Helper to get node ID from link source/target
    // ForceGraph2D mutates links: source/target become objects after rendering
    const getLinkNodeId = (linkNode) => {
      if (typeof linkNode === 'string') return linkNode;
      if (linkNode && typeof linkNode === 'object') return linkNode.id;
      return null;
    };

    const filteredLinks = graphData.links.filter((link) => {
      const sourceId = getLinkNodeId(link.source);
      const targetId = getLinkNodeId(link.target);
      if (!sourceId || !targetId) return false;
      if (!nodeIds.has(sourceId) || !nodeIds.has(targetId)) return false;
      if (link.type === 'wikilink' && !filters.showWikilinks) return false;
      if (link.type === 'tag' && !filters.showTagLinks) return false;
      if (link.type === 'image' && !filters.showImageLinks) return false;
      return true;
    });

    return { nodes: filteredNodes, links: filteredLinks };
  }, [graphData, filters]);

  // Highlight nodes matching search term
  const highlightedNodes = React.useMemo(() => {
    if (!debouncedSearchTerm) return new Set();

    const term = debouncedSearchTerm.toLowerCase();
    return new Set(
      filteredGraphData.nodes
        .filter((node) => node.name.toLowerCase().includes(term))
        .map((node) => node.id)
    );
  }, [debouncedSearchTerm, filteredGraphData]);

  // Handle node click
  const handleNodeClick = useCallback((node) => {
    setSelectedNode(node);

    // Set context for AI chat
    if (node.type === 'note') {
      setChatContext({
        type: 'note',
        noteId: node.noteId,
        title: node.name,
        content: node.content || ''
      });
    } else if (node.type === 'tag') {
      setChatContext({
        type: 'tag',
        tagName: node.name
      });
    } else if (node.type === 'image') {
      setChatContext({
        type: 'image',
        imageId: node.imageId,
        title: node.name
      });
    }

    // Navigate based on node type
    if (node.type === 'note' && node.noteId && onNavigateToNote) {
      onNavigateToNote(node.noteId);
    } else if (node.type === 'image' && node.imageId && onNavigateToImage) {
      onNavigateToImage(node.imageId);
    } else if (node.type === 'tag' && node.name && onNavigateToTag) {
      onNavigateToTag(node.name);
    }
  }, [onNavigateToNote, onNavigateToImage, onNavigateToTag]);

  // Handle node hover
  const handleNodeHover = useCallback((node) => {
    setHoveredNode(node);
  }, []);

  // Handle search and focus
  const handleSearch = useCallback((term) => {
    setSearchTerm(term);

    if (term && graphRef.current) {
      // Find first matching node and center view on it
      const match = filteredGraphData.nodes.find((node) =>
        node.name.toLowerCase().includes(term.toLowerCase())
      );

      if (match) {
        graphRef.current.centerAt(match.x, match.y, 1000);
        graphRef.current.zoom(3, 1000);
      }
    }
  }, [filteredGraphData]);

  // Node rendering function
  const nodeCanvasObject = useCallback(
    (node, ctx, globalScale) => {
      const label = node.name;
      const fontSize = 12 / globalScale;
      ctx.font = `${fontSize}px Sans-Serif`;

      // Detect theme for label color
      const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
      const labelColor = isDarkMode ? '#e0e0e0' : '#333';

      // Determine node color and shape
      let color = '#999';
      if (node.type === 'note') color = '#4A90E2'; // Blue
      if (node.type === 'tag') color = '#F5A623'; // Orange
      if (node.type === 'image') color = '#7ED321'; // Green

      // Highlight if searched or selected
      if (highlightedNodes.has(node.id)) {
        color = '#FF3B30'; // Red highlight
      }
      if (selectedNode?.id === node.id) {
        ctx.strokeStyle = '#FF3B30';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.size + 2, 0, 2 * Math.PI);
        ctx.stroke();
      }

      // Draw node
      ctx.fillStyle = color;
      ctx.beginPath();

      if (node.type === 'tag') {
        // Hexagon for tags
        const sides = 6;
        const radius = node.size;
        for (let i = 0; i < sides; i++) {
          const angle = (Math.PI / 3) * i;
          const x = node.x + radius * Math.cos(angle);
          const y = node.y + radius * Math.sin(angle);
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.closePath();
      } else {
        // Circle for notes and images
        ctx.arc(node.x, node.y, node.size, 0, 2 * Math.PI);
      }

      ctx.fill();

      // Draw label
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = labelColor;
      ctx.fillText(label, node.x, node.y + node.size + 2);
    },
    [highlightedNodes, selectedNode]
  );

  // Link rendering function
  const linkCanvasObject = useCallback((link, ctx) => {
    const start = link.source;
    const end = link.target;

    // Determine line style based on link type
    if (link.type === 'wikilink') {
      // Solid line for wikilinks (note → note)
      ctx.strokeStyle = '#999';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([]);
    } else if (link.type === 'tag') {
      // Dashed line for tags (note → tag)
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 1;
      ctx.setLineDash([5, 5]);
    } else if (link.type === 'image') {
      // Dotted line for images (note → image)
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 1;
      ctx.setLineDash([2, 4]);
    } else {
      // Default fallback
      ctx.strokeStyle = '#CCC';
      ctx.lineWidth = 0.5;
      ctx.setLineDash([]);
    }

    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
    ctx.stroke();

    // Reset dash after drawing
    ctx.setLineDash([]);
  }, []);

  if (loading) {
    return (
      <div className="knowledge-graph-container">
        <div className="graph-loading">
          <div className="loading-spinner"></div>
          <p>Loading knowledge graph...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="knowledge-graph-container">
        <div className="graph-error">
          <div className="error-icon">⚠️</div>
          <h3>Failed to load graph</h3>
          <p>{error}</p>
          <button onClick={fetchGraphData} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="knowledge-graph-container">
      <GraphControls
        searchTerm={searchTerm}
        onSearch={handleSearch}
        filters={filters}
        onFilterChange={setFilters}
        onRefresh={fetchGraphData}
        nodeCount={filteredGraphData.nodes.length}
        linkCount={filteredGraphData.links.length}
      />

      {/* Enhanced Info Panel */}
      <div className="graph-info-panel">
        <h3>Knowledge Graph</h3>
        <div className="graph-stats">
          <div className="stat-item">
            <div className="stat-icon note-icon">📝</div>
            <div className="stat-content">
              <span className="stat-value">{filteredGraphData.nodes.filter(n => n.type === 'note').length}</span>
              <span className="stat-label">Notes</span>
            </div>
          </div>
          <div className="stat-item">
            <div className="stat-icon tag-icon">🏷️</div>
            <div className="stat-content">
              <span className="stat-value">{filteredGraphData.nodes.filter(n => n.type === 'tag').length}</span>
              <span className="stat-label">Tags</span>
            </div>
          </div>
          <div className="stat-item">
            <div className="stat-icon image-icon">🖼️</div>
            <div className="stat-content">
              <span className="stat-value">{filteredGraphData.nodes.filter(n => n.type === 'image').length}</span>
              <span className="stat-label">Images</span>
            </div>
          </div>
          <div className="stat-item">
            <div className="stat-icon connection-icon">🔗</div>
            <div className="stat-content">
              <span className="stat-value">{filteredGraphData.links.length}</span>
              <span className="stat-label">Connections</span>
            </div>
          </div>
        </div>
        <div className="graph-legend">
          <div className="legend-item">
            <div className="legend-color note-color"></div>
            <span>Notes</span>
          </div>
          <div className="legend-item">
            <div className="legend-color tag-color"></div>
            <span>Tags</span>
          </div>
          <div className="legend-item">
            <div className="legend-color image-color"></div>
            <span>Images</span>
          </div>
        </div>
      </div>

      <div className="graph-canvas">
        <ForceGraph2D
          ref={graphRef}
          graphData={filteredGraphData}
          nodeId="id"
          nodeLabel="name"
          nodeCanvasObject={nodeCanvasObject}
          linkCanvasObject={linkCanvasObject}
          onNodeClick={handleNodeClick}
          onNodeHover={handleNodeHover}
          enableNodeDrag={true}
          enableZoomInteraction={true}
          enablePanInteraction={true}
          cooldownTime={3000}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
          warmupTicks={100}
          cooldownTicks={0}
        />
      </div>

      {hoveredNode && (
        <NodePreview
          node={hoveredNode}
          position={{ x: window.innerWidth / 2, y: 100 }}
        />
      )}

      {filteredGraphData.nodes.length === 0 && (
        <div className="graph-empty-state">
          <div className="empty-icon">🕸️</div>
          <h3>No graph data</h3>
          <p>Create notes with wikilinks and tags to build your knowledge graph!</p>
          <button onClick={() => setShowHelp(true)} className="empty-help-btn">
            <HelpCircle className="w-5 h-5" />
            Learn How to Build Your Graph
          </button>
        </div>
      )}

      {/* Help Button FAB */}
      <button
        className={`graph-help-fab ${showChat ? 'chat-open' : ''}`}
        onClick={() => setShowHelp(true)}
        title="Show help and tips"
      >
        <HelpCircle className="fab-icon" />
      </button>

      {/* AI Chat FAB Button */}
      <button
        className={`brain-chat-fab ${showChat ? 'chat-open' : ''}`}
        onClick={() => setShowChat(!showChat)}
        title="Chat with AI about your knowledge graph"
      >
        <Sparkles className="fab-icon" />
        <span className="fab-text">{showChat ? 'Close' : 'Ask AI'}</span>
      </button>

      {/* Help Modal */}
      <GraphHelp isOpen={showHelp} onClose={() => setShowHelp(false)} />

      {/* AI Chat Overlay */}
      {showChat && (
        <div className="brain-chat-overlay">
          <RAGChat
            mode="overlay"
            onClose={() => setShowChat(false)}
          />
        </div>
      )}
    </div>
  );
}

export default KnowledgeGraph;
