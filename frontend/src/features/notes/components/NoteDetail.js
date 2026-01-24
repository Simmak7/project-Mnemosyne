import React, { useState, useEffect, useCallback } from 'react';
import { useQueryClient, useQuery } from '@tanstack/react-query';
import { useNoteContext } from '../hooks/NoteContext';
import { useNotes } from '../hooks/useNotes';
import NoteDetailHeader from './NoteDetailHeader';
import NoteDetailTabs from './NoteDetailTabs';
import NoteMediaPreview from './NoteMediaPreview';
import NoteContentTab from './NoteContentTab';
import NoteContextTab from './NoteContextTab';
import NoteInfoTab from './NoteInfoTab';
import AIToolsPanel from './AIToolsPanel';
import { BlockEditor } from '../../editor';
import './NoteDetail.css';

const API_BASE = 'http://localhost:8000';

/**
 * NoteDetail - Right panel showing full note content with tabs
 * Tabs: Content | Context | Info
 */
function NoteDetail({ onNavigateToGraph, onNavigateToImage, onNavigateToAI }) {
  const { selectedNoteId, selectNote, refreshCounts } = useNoteContext();
  const queryClient = useQueryClient();
  const { allNotes } = useNotes();

  const [note, setNote] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('content');
  const [showMediaPreview, setShowMediaPreview] = useState(true);
  const [isEditing, setIsEditing] = useState(false);

  // Fetch tags for autocomplete
  const { data: allTags = [] } = useQuery({
    queryKey: ['tags'],
    queryFn: async () => {
      const token = localStorage.getItem('token');
      if (!token) return [];
      const response = await fetch(`${API_BASE}/tags/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) return [];
      return response.json();
    },
    staleTime: 60000,
  });

  // Fetch full note details when selected
  useEffect(() => {
    if (!selectedNoteId) {
      setNote(null);
      return;
    }

    const fetchNote = async () => {
      setLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem('token');
        if (!token) throw new Error('Not authenticated');

        const response = await fetch(`${API_BASE}/notes/${selectedNoteId}/enhanced`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch note');
        }

        const data = await response.json();
        setNote(data);
      } catch (err) {
        console.error('Error fetching note:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchNote();
  }, [selectedNoteId]);

  // Handle wikilink navigation
  const handleWikilinkClick = useCallback(async (title) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/notes/?search=${encodeURIComponent(title)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const notes = await response.json();
        const target = notes.find(n =>
          n.title?.toLowerCase() === title.toLowerCase() ||
          n.slug === title.toLowerCase().replace(/\s+/g, '-')
        );
        if (target) {
          selectNote(target.id);
        }
      }
    } catch (err) {
      console.error('Error navigating to wikilink:', err);
    }
  }, [selectNote]);

  // Handle tag click - filter by tag
  const handleTagClick = useCallback((tagName) => {
    // Could navigate to notes filtered by this tag
    console.log('Tag clicked:', tagName);
  }, []);

  // Refresh current note data (used after AI tools modify the note)
  const handleRefreshNote = useCallback(async () => {
    if (!selectedNoteId) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/notes/${selectedNoteId}/enhanced`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setNote(data);
      }
    } catch (err) {
      console.error('Error refreshing note:', err);
    }
  }, [selectedNoteId]);

  // Handle favorite toggle
  const handleToggleFavorite = useCallback(async () => {
    if (!note) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/notes/${note.id}/favorite`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const updatedNote = await response.json();
        setNote(prev => ({ ...prev, is_favorite: updatedNote.is_favorite }));
        // Refresh counts for favorites category
        queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
        refreshCounts();
      }
    } catch (err) {
      console.error('Error toggling favorite:', err);
    }
  }, [note, queryClient, refreshCounts]);

  // Handle move to trash
  const handleMoveToTrash = useCallback(async () => {
    if (!note) return;

    if (!window.confirm('Move this note to trash?')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/notes/${note.id}/trash`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        // Clear selection and trigger refresh
        selectNote(null);
        // Invalidate queries to refresh note lists
        queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
        queryClient.invalidateQueries({ queryKey: ['notes-trash'] });
        refreshCounts();
      }
    } catch (err) {
      console.error('Error moving note to trash:', err);
    }
  }, [note, selectNote, queryClient, refreshCounts]);

  // Handle toggle reviewed
  const handleToggleReviewed = useCallback(async () => {
    if (!note) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/notes/${note.id}/reviewed`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const updatedNote = await response.json();
        setNote(prev => ({ ...prev, is_reviewed: updatedNote.is_reviewed }));
        // Refresh counts for review queue
        queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
        refreshCounts();
      }
    } catch (err) {
      console.error('Error toggling reviewed:', err);
    }
  }, [note, queryClient, refreshCounts]);

  // Handle restore from trash
  const handleRestoreFromTrash = useCallback(async () => {
    if (!note) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/notes/${note.id}/restore`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        // Invalidate queries to refresh note lists
        queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
        queryClient.invalidateQueries({ queryKey: ['notes-trash'] });
        refreshCounts();
        // Deselect the note after restore
        selectNote(null);
      }
    } catch (err) {
      console.error('Error restoring note from trash:', err);
    }
  }, [note, selectNote, queryClient, refreshCounts]);

  // Handle edit start
  const handleEditStart = useCallback(() => {
    setIsEditing(true);
  }, []);

  // Handle save from editor
  const handleSave = useCallback(async (editData) => {
    if (!note) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/notes/${note.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: editData.title,
          content: editData.content,
          html_content: editData.html
        })
      });

      if (response.ok) {
        const updatedNote = await response.json();
        setNote(prev => ({
          ...prev,
          title: updatedNote.title,
          content: updatedNote.content,
          html_content: updatedNote.html_content,
          updated_at: updatedNote.updated_at
        }));
        setIsEditing(false);
        // Invalidate note list to show updated title
        queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
      }
    } catch (err) {
      console.error('Error saving note:', err);
    }
  }, [note, queryClient]);

  // Handle cancel editing
  const handleCancelEdit = useCallback(() => {
    setIsEditing(false);
  }, []);

  // Empty state
  if (!selectedNoteId) {
    return (
      <div className="note-detail note-detail-empty">
        <div className="empty-state">
          <span className="empty-icon">📄</span>
          <h3>Select a note</h3>
          <p>Choose a note from the list to view its contents</p>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="note-detail note-detail-loading">
        <div className="loading-skeleton">
          <div className="skeleton-header">
            <div className="skeleton-title" />
            <div className="skeleton-meta" />
          </div>
          <div className="skeleton-tabs" />
          <div className="skeleton-content">
            <div className="skeleton-line" />
            <div className="skeleton-line" />
            <div className="skeleton-line short" />
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="note-detail note-detail-error">
        <div className="error-state">
          <span className="error-icon">⚠️</span>
          <h3>Failed to load note</h3>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!note) return null;

  return (
    <div className="note-detail">
      {/* Header with title, metadata, and actions */}
      <NoteDetailHeader
        note={note}
        onNavigateToGraph={onNavigateToGraph}
        onNavigateToAI={onNavigateToAI}
        onToggleFavorite={handleToggleFavorite}
        onMoveToTrash={handleMoveToTrash}
        onToggleReviewed={handleToggleReviewed}
        onRestoreFromTrash={handleRestoreFromTrash}
        onEdit={handleEditStart}
        isEditing={isEditing}
      />

      {/* Editing mode - show BlockEditor */}
      {isEditing ? (
        <div className="note-detail-editor">
          <BlockEditor
            note={note}
            allNotes={allNotes}
            allTags={allTags}
            onSave={handleSave}
            onCancel={handleCancelEdit}
            onWikilinkClick={handleWikilinkClick}
            onHashtagClick={handleTagClick}
          />
        </div>
      ) : (
        <>
          {/* Tab navigation */}
          <NoteDetailTabs
            activeTab={activeTab}
            onTabChange={setActiveTab}
            contextCount={(note.backlinks?.length || 0) + (note.linked_notes?.length || 0)}
          />

          {/* Tab content */}
          <div className="note-detail-content">
            {activeTab === 'content' && (
              <>
                {/* Media preview (if note has images) */}
                {note.image_ids && note.image_ids.length > 0 && showMediaPreview && (
                  <NoteMediaPreview
                    imageIds={note.image_ids}
                    onHide={() => setShowMediaPreview(false)}
                    onImageClick={onNavigateToImage}
                  />
                )}

                {/* Note content */}
                <NoteContentTab
                  note={note}
                  onWikilinkClick={handleWikilinkClick}
                  onTagClick={handleTagClick}
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
                onRefreshNote={handleRefreshNote}
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
