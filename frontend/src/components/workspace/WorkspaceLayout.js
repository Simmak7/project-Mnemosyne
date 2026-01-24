import React, { useState, useCallback } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { WorkspaceProvider } from '../../contexts/WorkspaceContext';
import LeftPane from './LeftPane';
import CenterPane from './CenterPane';
import RightPane from './RightPane';
import WorkspaceKeyboardShortcuts from './WorkspaceKeyboardShortcuts';
import './WorkspaceLayout.css';

/**
 * WorkspaceLayout - Main 3-pane workspace container
 * Neural Glass design with glassmorphism panels and ambient background
 *
 * Phase 2: Glass Surfaces & Layout
 * - Ambient gradient background
 * - Glass-styled panels with backdrop blur
 * - Enhanced resize handles with glow effect
 */
function WorkspaceLayout() {
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);

  // Handle panel collapse with keyboard shortcuts
  const handleLeftToggle = useCallback(() => {
    setLeftCollapsed(prev => !prev);
  }, []);

  const handleRightToggle = useCallback(() => {
    setRightCollapsed(prev => !prev);
  }, []);

  return (
    <WorkspaceProvider>
      <div
        className="workspace-layout ng-theme ng-ambient-bg"
        role="region"
        aria-label="Workspace"
      >
        <WorkspaceKeyboardShortcuts
          onToggleLeft={handleLeftToggle}
          onToggleRight={handleRightToggle}
        />
        <PanelGroup direction="horizontal" className="workspace-panel-group">
          {/* Left Pane - Navigation/Hierarchy */}
          <Panel
            defaultSize={leftCollapsed ? 0 : 22}
            minSize={leftCollapsed ? 0 : 15}
            maxSize={35}
            collapsible={true}
            collapsedSize={0}
            onCollapse={() => setLeftCollapsed(true)}
            onExpand={() => setLeftCollapsed(false)}
            className="workspace-panel left-panel ng-glass"
            id="left-pane"
          >
            <LeftPane />
          </Panel>

          <PanelResizeHandle className="workspace-resize-handle glass-resize-handle horizontal" />

          {/* Center Pane - Editor */}
          <Panel
            defaultSize={56}
            minSize={30}
            className="workspace-panel center-panel ng-glass-light"
            id="center-pane"
          >
            <CenterPane />
          </Panel>

          <PanelResizeHandle className="workspace-resize-handle glass-resize-handle horizontal" />

          {/* Right Pane - Context Rail */}
          <Panel
            defaultSize={rightCollapsed ? 0 : 22}
            minSize={rightCollapsed ? 0 : 15}
            maxSize={35}
            collapsible={true}
            collapsedSize={0}
            onCollapse={() => setRightCollapsed(true)}
            onExpand={() => setRightCollapsed(false)}
            className="workspace-panel right-panel ng-glass"
            id="right-pane"
          >
            <RightPane />
          </Panel>
        </PanelGroup>
      </div>
    </WorkspaceProvider>
  );
}

export default WorkspaceLayout;
