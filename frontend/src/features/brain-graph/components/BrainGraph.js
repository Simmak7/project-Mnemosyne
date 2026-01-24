/**
 * BrainGraph - Main container for Neural Glass knowledge graph
 *
 * Navigation-first design with view switching between:
 * - Explore: Local neighborhood navigation
 * - Map: Clustered overview for insight
 * - Media: Visual content filter
 * - PathFinder: Find paths between nodes
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Compass, Map, Image, GitBranch } from 'lucide-react';

import { ViewSwitcher } from './ViewSwitcher';
import { LeftPanel } from './LeftPanel';
import { Inspector } from './Inspector';
import { ExploreView } from '../views/ExploreView';
import { MapView } from '../views/MapView';
import { MediaView } from '../views/MediaView';
import { PathFinderView } from '../views/PathFinderView';

import { useGraphState } from '../hooks/useGraphState';
import { useGraphFilters } from '../hooks/useGraphFilters';
import { useGraphLayout } from '../hooks/useGraphLayout';

import './BrainGraph.css';

// View configuration
const VIEWS = [
  { id: 'explore', label: 'Explore', icon: Compass },
  { id: 'map', label: 'Map', icon: Map },
  { id: 'media', label: 'Media', icon: Image },
  { id: 'pathfinder', label: 'Path', icon: GitBranch },
];

export function BrainGraph({
  initialNodeId = null,
  defaultView = 'explore',
  showLeftPanel = true,
  showInspector = true,
  onNavigate = null,
  className = '',
}) {
  // Use provided navigate handler or log to console as fallback
  const navigate = onNavigate || ((path) => console.log('Navigate to:', path));
  const [currentView, setCurrentView] = useState(defaultView);

  // Initialize hooks
  const graphState = useGraphState((path) => navigate(path));
  const filters = useGraphFilters();
  const layout = useGraphLayout(currentView === 'map' ? 'map' : 'explore');

  // Set initial focus node
  useEffect(() => {
    if (initialNodeId && !graphState.focusNodeId) {
      graphState.setFocusNodeId(initialNodeId);
    }
  }, [initialNodeId, graphState]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't handle if typing in input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
      }

      graphState.handleKeyDown(e);
      layout.handleLayoutKeyDown(e);

      // View switching shortcuts
      if (e.key === '1') setCurrentView('explore');
      if (e.key === '2') setCurrentView('map');
      if (e.key === '3') setCurrentView('media');
      if (e.key === '4') setCurrentView('pathfinder');
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [graphState, layout]);

  // Handle view change
  const handleViewChange = useCallback((viewId) => {
    setCurrentView(viewId);
    // Update layout preset for the view
    if (viewId === 'map') {
      layout.changePreset('map');
    } else {
      layout.changePreset('explore');
    }
  }, [layout]);

  // Handle exploring a node from Map view
  const handleExploreNode = useCallback((nodeId) => {
    graphState.setFocusNodeId(nodeId);
    handleViewChange('explore');
  }, [graphState, handleViewChange]);

  // Render current view
  const renderView = () => {
    const viewProps = {
      graphState,
      filters,
      layout,
    };

    switch (currentView) {
      case 'explore':
        return <ExploreView {...viewProps} />;
      case 'map':
        return <MapView {...viewProps} onExploreNode={handleExploreNode} />;
      case 'media':
        return <MediaView {...viewProps} />;
      case 'pathfinder':
        return <PathFinderView {...viewProps} />;
      default:
        return <ExploreView {...viewProps} />;
    }
  };

  return (
    <div className={`brain-graph ${className}`}>
      {/* View Switcher Header */}
      <ViewSwitcher
        views={VIEWS}
        currentView={currentView}
        onViewChange={handleViewChange}
        layout={layout}
      />

      {/* Main Content Area */}
      <div className="brain-graph__content">
        {/* Left Panel - Legend, Layers, Filters */}
        {showLeftPanel && (
          <LeftPanel
            filters={filters}
            layout={layout}
            currentView={currentView}
          />
        )}

        {/* Canvas Area */}
        <div className="brain-graph__canvas-container">
          {renderView()}
        </div>

        {/* Inspector - Right Panel */}
        {showInspector && (
          <Inspector
            selectedNode={graphState.selectedNode}
            selectedEdge={graphState.selectedEdge}
            onClose={graphState.clearSelection}
            onNavigate={(path) => navigate(path)}
            onExpandNeighbors={graphState.expandSelected}
            onPin={graphState.pinSelected}
            onSetFocus={(node) => graphState.setFocusNodeId(node.id)}
            onFindPath={(node) => {
              graphState.setPathSource(node.id);
              setCurrentView('pathfinder');
            }}
            isPinned={graphState.selectedNode && graphState.isPinned(graphState.selectedNode.id)}
          />
        )}
      </div>
    </div>
  );
}

export default BrainGraph;
