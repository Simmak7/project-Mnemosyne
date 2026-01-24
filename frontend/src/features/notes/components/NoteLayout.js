import React, { useState, useRef, useCallback } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { ChevronRight } from 'lucide-react';
import { NoteProvider } from '../hooks/NoteContext';
import NoteSidebar from './NoteSidebar';
import NoteList from './NoteList';
import NoteDetail from './NoteDetail';
import './NoteLayout.css';

/**
 * NoteLayout - Main 3-column notes container
 * Inspired by Notion/Obsidian with Neural Glass design
 *
 * Layout: [Sidebar | Note List | Note Detail]
 */
function NoteLayout({ onNavigateToGraph, onNavigateToImage, onNavigateToAI, selectedNoteId }) {
  // Panel collapse state
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);

  // Panel refs for programmatic collapse/expand
  const sidebarPanelRef = useRef(null);

  // Collapse/expand handlers for sidebar
  const handleCollapseSidebar = useCallback(() => {
    if (sidebarPanelRef.current) {
      sidebarPanelRef.current.collapse();
    }
  }, []);

  const handleExpandSidebar = useCallback(() => {
    if (sidebarPanelRef.current) {
      sidebarPanelRef.current.expand();
    }
  }, []);

  return (
    <NoteProvider initialNoteId={selectedNoteId}>
      <div className="note-layout ng-theme">
        <PanelGroup direction="horizontal" className="note-panel-group">
          {/* Left Panel - Navigation Sidebar */}
          <Panel
            ref={sidebarPanelRef}
            defaultSize={leftCollapsed ? 0 : 18}
            minSize={leftCollapsed ? 0 : 14}
            maxSize={25}
            collapsible={true}
            collapsedSize={0}
            onCollapse={() => setLeftCollapsed(true)}
            onExpand={() => setLeftCollapsed(false)}
            className="note-panel note-sidebar-panel"
            id="note-sidebar"
          >
            <NoteSidebar
              isCollapsed={leftCollapsed}
              onCollapse={handleCollapseSidebar}
            />
          </Panel>

          {/* Floating expand button when sidebar is collapsed */}
          {leftCollapsed && (
            <button
              className="sidebar-expand-floating"
              onClick={handleExpandSidebar}
              title="Expand sidebar"
            >
              <ChevronRight size={20} />
            </button>
          )}

          <PanelResizeHandle className="note-resize-handle" />

          {/* Center Panel - Note List */}
          <Panel
            defaultSize={35}
            minSize={25}
            className="note-panel note-list-panel"
            id="note-list"
          >
            <NoteList />
          </Panel>

          <PanelResizeHandle className="note-resize-handle" />

          {/* Right Panel - Note Detail */}
          <Panel
            defaultSize={rightCollapsed ? 0 : 47}
            minSize={rightCollapsed ? 0 : 30}
            collapsible={true}
            collapsedSize={0}
            onCollapse={() => setRightCollapsed(true)}
            onExpand={() => setRightCollapsed(false)}
            className="note-panel note-detail-panel"
            id="note-detail"
          >
            <NoteDetail
              onNavigateToGraph={onNavigateToGraph}
              onNavigateToImage={onNavigateToImage}
              onNavigateToAI={onNavigateToAI}
            />
          </Panel>
        </PanelGroup>
      </div>
    </NoteProvider>
  );
}

export default NoteLayout;
