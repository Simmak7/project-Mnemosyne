import React, { useState, useEffect, useCallback, useRef } from 'react';
import 'aframe';
import { ForceGraph2D } from 'react-force-graph';
import { Sparkles, HelpCircle } from 'lucide-react';
import GraphControls from '../GraphControls';
import NodePreview from '../NodePreview';
import GraphHelp from '../GraphHelp';
import RAGChat from '../../../features/rag_chat/components/RAGChat';
import { useGraphData, useGraphFilters, useGraphSearch } from './hooks';
import { LoadingState, ErrorState, EmptyState, GraphInfoPanel } from './components';
import { createNodeCanvasObject, linkCanvasObject } from './utils';
import '../KnowledgeGraph.css';

/**
 * Interactive force-directed knowledge graph visualization
 */
function KnowledgeGraph({ onNavigateToNote, onNavigateToImage, onNavigateToTag }) {
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [showChat, setShowChat] = useState(false);
  const [chatContext, setChatContext] = useState(null);
  const [showHelp, setShowHelp] = useState(false);

  const graphRef = useRef();

  // Custom hooks
  const { graphData, loading, error, fetchGraphData } = useGraphData();
  const { filters, setFilters, filteredGraphData } = useGraphFilters(graphData);
  const { searchTerm, highlightedNodes, handleSearch } = useGraphSearch(
    filteredGraphData,
    graphRef
  );

  // Initial load
  useEffect(() => {
    fetchGraphData();
  }, [fetchGraphData]);

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

  // Create node renderer with current state
  const nodeCanvasObject = useCallback(
    (node, ctx, globalScale) => {
      const renderer = createNodeCanvasObject(highlightedNodes, selectedNode);
      renderer(node, ctx, globalScale);
    },
    [highlightedNodes, selectedNode]
  );

  if (loading) {
    return <LoadingState />;
  }

  if (error) {
    return <ErrorState error={error} onRetry={fetchGraphData} />;
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

      <GraphInfoPanel filteredGraphData={filteredGraphData} />

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
        <EmptyState onShowHelp={() => setShowHelp(true)} />
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
          <RAGChat mode="overlay" onClose={() => setShowChat(false)} />
        </div>
      )}
    </div>
  );
}

export default KnowledgeGraph;
