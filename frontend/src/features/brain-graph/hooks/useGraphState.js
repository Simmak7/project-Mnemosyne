/**
 * useGraphState - State management for graph interactions
 *
 * Manages selected node, hovered node, focus, and pinned nodes.
 * Provides handlers for click, hover, and keyboard events.
 */

import { useState, useCallback, useMemo } from 'react';

/**
 * Graph interaction state hook
 */
export function useGraphState(onNavigate) {
  // Selected node (clicked, shown in Inspector)
  const [selectedNode, setSelectedNode] = useState(null);

  // Hovered node (for highlighting)
  const [hoveredNode, setHoveredNode] = useState(null);

  // Focus node (center of local graph)
  const [focusNodeId, setFocusNodeId] = useState(null);

  // Expanded depth (temporary increase for Expand action)
  const [expandedDepth, setExpandedDepth] = useState(0);

  // Pinned nodes (position locked)
  const [pinnedNodes, setPinnedNodes] = useState(new Set());

  // Selected edge (for "Why connected?")
  const [selectedEdge, setSelectedEdge] = useState(null);

  // Path finder source and target
  const [pathSourceId, setPathSourceId] = useState(null);
  const [pathTargetId, setPathTargetId] = useState(null);

  // Node click - set as selected, update Inspector
  const handleNodeClick = useCallback((node, event) => {
    setSelectedNode(node);
    setSelectedEdge(null);

    // If shift-click, add to focus
    if (event?.shiftKey) {
      setFocusNodeId(node.id);
    }
  }, []);

  // Node double-click - navigate to the item
  const handleNodeDoubleClick = useCallback((node) => {
    if (!node || !onNavigate) return;

    // Backend uses hyphen format: note-123, tag-456
    const [type, id] = node.id.split('-');

    switch (type) {
      case 'note':
        onNavigate(`/notes/${id}`);
        break;
      case 'image':
        onNavigate(`/gallery?image=${id}`);
        break;
      case 'tag':
        onNavigate(`/tags/${id}`);
        break;
      default:
        console.warn('Unknown node type:', type);
    }
  }, [onNavigate]);

  // Node hover - highlight connected edges
  const handleNodeHover = useCallback((node) => {
    setHoveredNode(node);
  }, []);

  // Edge click - show "Why connected?" info
  const handleEdgeClick = useCallback((edge) => {
    setSelectedEdge(edge);
    setSelectedNode(null);
  }, []);

  // Clear selection
  const clearSelection = useCallback(() => {
    setSelectedNode(null);
    setSelectedEdge(null);
  }, []);

  // Set focus node (center of local graph) - resets expanded depth
  const setFocus = useCallback((nodeId) => {
    setFocusNodeId(nodeId);
    setExpandedDepth(0); // Reset depth when changing focus
    clearSelection();
  }, [clearSelection]);

  // Toggle pin status
  const togglePin = useCallback((nodeId) => {
    setPinnedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  }, []);

  // Pin selected node
  const pinSelected = useCallback(() => {
    if (selectedNode) {
      togglePin(selectedNode.id);
    }
  }, [selectedNode, togglePin]);

  // Check if node is pinned
  const isPinned = useCallback((nodeId) => {
    return pinnedNodes.has(nodeId);
  }, [pinnedNodes]);

  // Expand: Increase depth to show more neighbors (without changing focus)
  const expandSelected = useCallback(() => {
    // Increase expanded depth by 1 (max 3)
    setExpandedDepth((prev) => Math.min(prev + 1, 3));
  }, []);

  // Reset expanded depth (e.g., when focus changes)
  const resetExpandedDepth = useCallback(() => {
    setExpandedDepth(0);
  }, []);

  // Set path source (for PathFinder)
  const setPathSource = useCallback((nodeId) => {
    setPathSourceId(nodeId);
  }, []);

  // Set path target (for PathFinder)
  const setPathTarget = useCallback((nodeId) => {
    setPathTargetId(nodeId);
  }, []);

  // Clear path selection
  const clearPath = useCallback(() => {
    setPathSourceId(null);
    setPathTargetId(null);
  }, []);

  // Keyboard handlers
  const handleKeyDown = useCallback((event) => {
    switch (event.key) {
      case 'Escape':
        clearSelection();
        break;
      case 'p':
      case 'P':
        pinSelected();
        break;
      case 'f':
      case 'F':
        expandSelected();
        break;
      case 'Delete':
      case 'Backspace':
        // Could be used for removing nodes from view
        break;
      default:
        break;
    }
  }, [clearSelection, pinSelected, expandSelected]);

  // Computed state
  const state = useMemo(() => ({
    selectedNode,
    hoveredNode,
    focusNodeId,
    selectedEdge,
    pinnedNodes: Array.from(pinnedNodes),
    hasSelection: selectedNode !== null || selectedEdge !== null,
    pathSourceId,
    pathTargetId,
    expandedDepth, // Additional depth from Expand action
  }), [selectedNode, hoveredNode, focusNodeId, selectedEdge, pinnedNodes, pathSourceId, pathTargetId, expandedDepth]);

  // Action handlers
  const actions = useMemo(() => ({
    handleNodeClick,
    handleNodeDoubleClick,
    handleNodeHover,
    handleEdgeClick,
    clearSelection,
    setFocus,
    togglePin,
    pinSelected,
    isPinned,
    expandSelected,
    resetExpandedDepth,
    handleKeyDown,
    setSelectedNode,
    setFocusNodeId,
    setPathSource,
    setPathTarget,
    clearPath,
  }), [
    handleNodeClick,
    handleNodeDoubleClick,
    handleNodeHover,
    handleEdgeClick,
    clearSelection,
    setFocus,
    togglePin,
    pinSelected,
    isPinned,
    expandSelected,
    resetExpandedDepth,
    handleKeyDown,
    setPathSource,
    setPathTarget,
    clearPath,
  ]);

  return { ...state, ...actions };
}

export default useGraphState;
