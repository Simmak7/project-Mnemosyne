import React, { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileScan } from 'lucide-react';
import { useNoteContext } from '../../hooks/NoteContext';
import { useNotes } from '../../hooks/useNotes';
import NoteDetailHeader from '../NoteDetailHeader';
import NoteDetailTabs from '../NoteDetailTabs';
import NoteMediaPreview from '../NoteMediaPreview';
import NoteContentTab from '../NoteContentTab';
import NoteContextTab from '../NoteContextTab';
import NoteInfoTab from '../NoteInfoTab';
import AIToolsPanel from '../AIToolsPanel';
import { BlockEditor } from '../../../editor';
import { useNoteActions, useNoteEditor } from './hooks';
import { EmptyState, LoadingState, ErrorState } from './components';
import { api } from '../../../../utils/api';
import '../NoteDetail.css';

/**
 * NoteDetail - Right panel showing full note content with tabs
 */
function NoteDetail({ onNavigateToGraph, onNavigateToImage, onNavigateToAI, onNavigateToDocument }) {
  const { selectedNoteId, selectNote, refreshCounts, editAfterSelect, setEditAfterSelect } = useNoteContext();
  const { allNotes } = useNotes();

  const [note, setNote] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('content');
  const [showMediaPreview, setShowMediaPreview] = useState(true);

  // Custom hooks
  const noteActions = useNoteActions({
    note,
    setNote,
    selectedNoteId,
    selectNote,
    refreshCounts,
  });

  const noteEditor = useNoteEditor({
    note,
    setNote,
    selectNote,
  });

  // Fetch tags for autocomplete
  const { data: allTags = [] } = useQuery({
    queryKey: ['tags'],
    queryFn: () => api.get('/tags/'),
    staleTime: 60000,
  });

  // Check if this note was created from a document
  const { data: sourceDocData } = useQuery({
    queryKey: ['note-source-document', selectedNoteId],
    queryFn: () => api.get(`/notes/${selectedNoteId}/source-document`),
    enabled: !!selectedNoteId,
    staleTime: 60000,
  });
  const sourceDocument = sourceDocData?.source_document;

  // Fetch full note details when selected (with abort for stale requests)
  useEffect(() => {
    if (!selectedNoteId) {
      setNote(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    const controller = new AbortController();

    const fetchNote = async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await api.get(`/notes/${selectedNoteId}/enhanced`, {
          signal: controller.signal,
        });
        if (!cancelled) setNote(data);
      } catch (err) {
        if (cancelled || err.name === 'AbortError') return;
        console.error('Error fetching note:', err);
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchNote();
    return () => { cancelled = true; controller.abort(); };
  }, [selectedNoteId]);

  // Auto-enter edit mode when a new note is created
  const prevNoteId = useRef(null);
  useEffect(() => {
    if (editAfterSelect && note && note.id !== prevNoteId.current) {
      prevNoteId.current = note.id;
      setEditAfterSelect(false);
      noteEditor.handleEditStart();
    }
  }, [editAfterSelect, note, setEditAfterSelect, noteEditor]);

  // Empty state
  if (!selectedNoteId) {
    return <EmptyState />;
  }

  // Loading state
  if (loading) {
    return <LoadingState />;
  }

  // Error state
  if (error) {
    return <ErrorState error={error} />;
  }

  if (!note) return null;

  return (
    <div className="note-detail">
      <NoteDetailHeader
        note={note}
        onNavigateToGraph={onNavigateToGraph}
        onNavigateToAI={onNavigateToAI}
        onToggleFavorite={noteActions.handleToggleFavorite}
        onMoveToTrash={noteActions.handleMoveToTrash}
        onToggleReviewed={noteActions.handleToggleReviewed}
        onRestoreFromTrash={noteActions.handleRestoreFromTrash}
        onEdit={noteEditor.handleEditStart}
        isEditing={noteEditor.isEditing}
      />

      {sourceDocument && onNavigateToDocument && (
        <button
          className="note-source-doc-banner"
          onClick={() => onNavigateToDocument(sourceDocument.id)}
        >
          <FileScan size={14} />
          <span>From: {sourceDocument.display_name || sourceDocument.filename}</span>
          {sourceDocument.page_count && <span className="note-source-doc-pages">{sourceDocument.page_count}p</span>}
        </button>
      )}

      {noteEditor.isEditing ? (
        <div className="note-detail-editor">
          <BlockEditor
            note={note}
            allNotes={allNotes}
            allTags={allTags}
            onSave={noteEditor.handleSave}
            onCancel={noteEditor.handleCancelEdit}
            onWikilinkClick={noteEditor.handleWikilinkClick}
            onHashtagClick={noteEditor.handleTagClick}
          />
        </div>
      ) : (
        <>
          <NoteDetailTabs
            activeTab={activeTab}
            onTabChange={setActiveTab}
            contextCount={(note.backlinks?.length || 0) + (note.linked_notes?.length || 0)}
          />

          <div className="note-detail-content">
            {activeTab === 'content' && (
              <>
                {note.image_ids && note.image_ids.length > 0 && showMediaPreview && (
                  <NoteMediaPreview
                    imageIds={note.image_ids}
                    onHide={() => setShowMediaPreview(false)}
                    onImageClick={onNavigateToImage}
                  />
                )}

                <NoteContentTab
                  note={note}
                  onWikilinkClick={noteEditor.handleWikilinkClick}
                  onTagClick={noteEditor.handleTagClick}
                />
              </>
            )}

            {activeTab === 'context' && (
              <NoteContextTab
                note={note}
                onNoteClick={selectNote}
                onImageClick={onNavigateToImage}
              />
            )}

            {activeTab === 'ai' && (
              <AIToolsPanel
                note={note}
                onTitleUpdate={(newTitle) => setNote(prev => ({ ...prev, title: newTitle }))}
                onNavigateToNote={selectNote}
                onRefreshNote={noteActions.handleRefreshNote}
              />
            )}

            {activeTab === 'info' && (
              <NoteInfoTab note={note} />
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default NoteDetail;
