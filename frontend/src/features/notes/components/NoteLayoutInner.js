import React, { useState, useRef, useCallback } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { DndContext, DragOverlay, closestCenter } from '@dnd-kit/core';
import { ChevronRight } from 'lucide-react';
import { useNotes } from '../hooks/useNotes';
import { useCustomNoteOrder } from '../hooks/useCustomNoteOrder';
import { useNoteDragDrop } from '../hooks/useNoteDragDrop';
import { useCollections } from '../hooks/useCollections';
import NoteSidebar from './NoteSidebar';
import NoteList from './NoteList';
import NoteDetail from './NoteDetail';
import NoteCard from './NoteCard';
import './NoteLayout.css';
import './NoteListDnd.css';

/**
 * NoteLayoutInner - Panel layout with DndContext for drag-and-drop.
 * Must be rendered inside NoteProvider.
 */
function NoteLayoutInner({ onNavigateToGraph, onNavigateToImage, onNavigateToAI, onNavigateToDocument }) {
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [dropToast, setDropToast] = useState(null);
  const sidebarPanelRef = useRef(null);

  const { notes } = useNotes();
  const { addNoteToCollection, collections } = useCollections();
  const { orderedNotes, orderedIds, handleReorder, initializeOrder, isCustomSort } =
    useCustomNoteOrder(notes);

  // Toast helper for collection drops
  const showDropToast = useCallback((noteId, collectionId) => {
    const note = notes.find(n => n.id === noteId);
    const col = collections.find(c => c.id === collectionId);
    if (note && col) {
      setDropToast(`Added "${note.title || 'Untitled'}" to ${col.name}`);
      setTimeout(() => setDropToast(null), 2500);
    }
  }, [notes, collections]);

  const handleDropToCollection = useCallback((noteId, collectionId) => {
    addNoteToCollection({ collectionId, noteId });
    showDropToast(noteId, collectionId);
  }, [addNoteToCollection, showDropToast]);

  const { sensors, activeId, handleDragStart, handleDragEnd, handleDragCancel } =
    useNoteDragDrop({
      onReorder: handleReorder,
      onDropToCollection: handleDropToCollection,
      initializeOrder,
    });

  const handleCollapseSidebar = useCallback(() => {
    sidebarPanelRef.current?.collapse();
  }, []);

  const handleExpandSidebar = useCallback(() => {
    sidebarPanelRef.current?.expand();
  }, []);

  const activeNote = activeId ? notes.find(n => n.id === activeId) : null;

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <div className="note-layout ng-theme">
        <PanelGroup direction="horizontal" className="note-panel-group">
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

          <Panel
            defaultSize={35}
            minSize={25}
            className="note-panel note-list-panel"
            id="note-list"
          >
            <NoteList
              orderedNotes={orderedNotes}
              orderedIds={orderedIds}
              isCustomSort={isCustomSort}
            />
          </Panel>

          <PanelResizeHandle className="note-resize-handle" />

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
              onNavigateToDocument={onNavigateToDocument}
            />
          </Panel>
        </PanelGroup>

        {/* Drag ghost overlay */}
        <DragOverlay dropAnimation={null}>
          {activeNote ? (
            <div className="note-drag-overlay">
              <NoteCard note={activeNote} isSelected={false} />
            </div>
          ) : null}
        </DragOverlay>

        {/* Drop feedback toast */}
        {dropToast && (
          <div className="note-drop-toast">{dropToast}</div>
        )}
      </div>
    </DndContext>
  );
}

export default NoteLayoutInner;
