import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useWorkspaceState } from '../../hooks/useWorkspaceState';
import { useContentAnalysis } from '../../hooks/useContentAnalysis';
import { Link2, ExternalLink, FileText } from 'lucide-react';
import { format } from 'date-fns';
import './ContextPanels.css';

/**
 * BacklinksPanel - Shows notes that link to the current note (Phase 4 - Real-time updates)
 * Uses React Query for data fetching and live updates based on editor content
 */
function BacklinksPanel() {
  const { selectedNoteId, selectNote, editorState } = useWorkspaceState();

  // Fetch backlinks using React Query
  const { data: backlinks = [], isLoading: loading, error } = useQuery({
    queryKey: ['backlinks', selectedNoteId],
    queryFn: async () => {
      if (!selectedNoteId) return [];

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token');
      }

      const response = await fetch(`http://localhost:8000/notes/${selectedNoteId}/backlinks`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch backlinks');
      }

      return response.json();
    },
    enabled: !!selectedNoteId,
    staleTime: 10000, // Consider data fresh for 10 seconds
    refetchOnWindowFocus: false,
  });

  // Real-time analysis of editor content for potential new backlinks
  const editorAnalysis = useContentAnalysis(editorState.editorInstance, editorState.noteTitle);

  // If in edit mode, show preview of potential new backlinks
  const potentialBacklinks = useMemo(() => {
    if (!editorState.isEditMode || !editorAnalysis.noteTitle) return [];

    // In the future, this could query for notes that might link to this one
    // based on content similarity or mentions
    return [];
  }, [editorState.isEditMode, editorAnalysis]);

  const handleBacklinkClick = (noteId) => {
    selectNote(noteId);
  };

  if (!selectedNoteId) {
    return (
      <div className="backlinks-panel">
        <div className="panel-empty">
          <Link2 size={40} className="empty-icon" />
          <p>Select a note to see backlinks</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="backlinks-panel">
        <div className="panel-loading">
          <div className="loading-spinner"></div>
          <p>Loading backlinks...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="backlinks-panel">
        <div className="panel-empty">
          <Link2 size={40} className="empty-icon" />
          <p>Error loading backlinks</p>
          <span className="empty-subtitle">{error.message}</span>
        </div>
      </div>
    );
  }

  if (backlinks.length === 0) {
    return (
      <div className="backlinks-panel">
        <div className="panel-empty">
          <Link2 size={40} className="empty-icon" />
          <p>No backlinks found</p>
          <span className="empty-subtitle">No other notes link to this one yet</span>
          {editorState.isEditMode && (
            <span className="empty-subtitle live-indicator">● Live updates enabled</span>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="backlinks-panel">
      <div className="panel-count">
        {backlinks.length} {backlinks.length === 1 ? 'backlink' : 'backlinks'}
        {editorState.isEditMode && (
          <span className="live-indicator" title="Updates in real-time as you edit">● Live</span>
        )}
      </div>

      <div className="backlinks-list">
        {backlinks.map((note) => (
          <div
            key={note.id}
            className="backlink-item"
            onClick={() => selectNote(note.id)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && selectNote(note.id)}
          >
            <div className="backlink-header">
              <FileText size={14} className="backlink-icon" />
              <span className="backlink-title">{note.title || 'Untitled'}</span>
              <ExternalLink size={12} className="backlink-external" />
            </div>
            <div className="backlink-date">
              {format(new Date(note.created_at), 'MMM d, yyyy')}
            </div>
            {note.content && (
              <div className="backlink-preview">
                {note.content.substring(0, 120)}...
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default BacklinksPanel;
