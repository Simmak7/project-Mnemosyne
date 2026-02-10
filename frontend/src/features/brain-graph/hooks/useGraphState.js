/**
 * useGraphState - State management for graph interactions
 *
 * Manages selected node, hovered node, focus, pinned nodes,
 * navigation history, and keyboard shortcuts.
 */

import { useState, useCallback, useMemo, useRef } from 'react';
import { usePersistedState } from '../../../hooks/usePersistedState';

export function useGraphState(onNavigate) {
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [focusNodeId, setFocusNodeId] = usePersistedState('brain:focusNodeId', null);
  const historyRef = useRef({ stack: [], index: -1, navigating: false });
  const [expandedDepth, setExpandedDepth] = useState(0);
  const [pinnedArray, setPinnedArray] = usePersistedState('brain:pinnedNodes', []);
  const pinnedNodes = useMemo(() => new Set(pinnedArray), [pinnedArray]);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [edgeBreakdown, setEdgeBreakdown] = useState(null);
  const [pathSourceId, setPathSourceId] = useState(null);
  const [pathTargetId, setPathTargetId] = useState(null);
  const [contextMenu, setContextMenu] = useState(null);
  const [highlightedNodeIds, setHighlightedNodeIds] = useState(new Set());

  const handleNodeClick = useCallback((node, event) => {
    setSelectedNode(node);
    setSelectedEdge(null);
    if (event?.shiftKey) setFocusNodeId(node.id);
  }, []);

  const handleNodeDoubleClick = useCallback((node) => {
    if (!node || !onNavigate) return;
    const [type, id] = node.id.split('-');
    switch (type) {
      case 'note': onNavigate(`/notes/${id}`); break;
      case 'image': onNavigate(`/gallery?image=${id}`); break;
      case 'tag': onNavigate(`/tags/${id}`); break;
      case 'document': onNavigate(`/documents/${id}`); break;
      default: console.warn('Unknown node type:', type);
    }
  }, [onNavigate]);

  const handleNodeHover = useCallback((node) => setHoveredNode(node), []);
  const handleEdgeClick = useCallback((edge) => { setSelectedEdge(edge); setSelectedNode(null); }, []);
  const clearSelection = useCallback(() => { setSelectedNode(null); setSelectedEdge(null); }, []);

  // Set focus node - resets expanded depth, tracks history
  const setFocus = useCallback((nodeId) => {
    if (!nodeId) return;
    const h = historyRef.current;
    if (h.navigating) {
      h.navigating = false;
    } else if (nodeId !== focusNodeId) {
      h.stack = h.stack.slice(0, h.index + 1);
      h.stack.push(nodeId);
      if (h.stack.length > 20) h.stack.shift();
      h.index = h.stack.length - 1;
    }
    setFocusNodeId(nodeId);
    setExpandedDepth(0);
    clearSelection();
  }, [clearSelection, focusNodeId]);

  const navigateBack = useCallback(() => {
    const h = historyRef.current;
    if (h.index > 0) {
      h.index -= 1;
      h.navigating = true;
      setFocusNodeId(h.stack[h.index]);
      setExpandedDepth(0);
    }
  }, []);

  const navigateForward = useCallback(() => {
    const h = historyRef.current;
    if (h.index < h.stack.length - 1) {
      h.index += 1;
      h.navigating = true;
      setFocusNodeId(h.stack[h.index]);
      setExpandedDepth(0);
    }
  }, []);

  const getHistory = useCallback(() => {
    const h = historyRef.current;
    return {
      stack: h.stack.slice(0, h.index + 1),
      index: h.index,
      canGoBack: h.index > 0,
      canGoForward: h.index < h.stack.length - 1,
    };
  }, []);

  const togglePin = useCallback((nodeId) => {
    setPinnedArray((prev) =>
      prev.includes(nodeId) ? prev.filter((id) => id !== nodeId) : [...prev, nodeId]
    );
  }, [setPinnedArray]);

  const pinSelected = useCallback(() => {
    if (selectedNode) togglePin(selectedNode.id);
  }, [selectedNode, togglePin]);

  const isPinned = useCallback((nodeId) => pinnedNodes.has(nodeId), [pinnedNodes]);
  const expandSelected = useCallback(() => setExpandedDepth((p) => Math.min(p + 1, 3)), []);
  const resetExpandedDepth = useCallback(() => setExpandedDepth(0), []);
  const setPathSource = useCallback((nodeId) => setPathSourceId(nodeId), []);
  const setPathTarget = useCallback((nodeId) => setPathTargetId(nodeId), []);
  const clearPath = useCallback(() => { setPathSourceId(null); setPathTargetId(null); }, []);

  const setHighlightedNodes = useCallback((ids) => {
    setHighlightedNodeIds(ids instanceof Set ? ids : new Set(ids || []));
  }, []);

  // Keyboard shortcuts
  const handleKeyDown = useCallback((event) => {
    if (event.altKey && event.key === 'ArrowLeft') { navigateBack(); event.preventDefault(); return; }
    if (event.altKey && event.key === 'ArrowRight') { navigateForward(); event.preventDefault(); return; }
    switch (event.key) {
      case 'Escape': clearSelection(); break;
      case 'p': case 'P': pinSelected(); break;
      case 'f': case 'F': expandSelected(); break;
      default: break;
    }
  }, [clearSelection, pinSelected, expandSelected, navigateBack, navigateForward]);

  const state = useMemo(() => ({
    selectedNode, hoveredNode, focusNodeId, selectedEdge, edgeBreakdown,
    pinnedNodes: Array.from(pinnedNodes),
    hasSelection: selectedNode !== null || selectedEdge !== null,
    pathSourceId, pathTargetId, expandedDepth,
    contextMenu, highlightedNodeIds,
  }), [selectedNode, hoveredNode, focusNodeId, selectedEdge, pinnedNodes,
    pathSourceId, pathTargetId, expandedDepth, edgeBreakdown,
    contextMenu, highlightedNodeIds]);

  const actions = useMemo(() => ({
    handleNodeClick, handleNodeDoubleClick, handleNodeHover, handleEdgeClick,
    clearSelection, setFocus, togglePin, pinSelected, isPinned,
    expandSelected, resetExpandedDepth, handleKeyDown,
    setSelectedNode, setFocusNodeId, setEdgeBreakdown,
    setPathSource, setPathTarget, clearPath,
    navigateBack, navigateForward, getHistory,
    setContextMenu, setHighlightedNodes,
  }), [
    handleNodeClick, handleNodeDoubleClick, handleNodeHover, handleEdgeClick,
    clearSelection, setFocus, togglePin, pinSelected, isPinned,
    expandSelected, resetExpandedDepth, handleKeyDown,
    setPathSource, setPathTarget, clearPath,
    navigateBack, navigateForward, getHistory,
    setHighlightedNodes,
  ]);

  return { ...state, ...actions };
}

export default useGraphState;
