import React, { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useWorkspaceState } from '../../hooks/useWorkspaceState';
import { FileText, Calendar, Eye, Edit2 } from 'lucide-react';
import { format } from 'date-fns';
import { BlockEditor } from '../../features/editor';
import { DailyView } from '../../features/daily';
import NoteContentRenderer from '../common/NoteContentRenderer';
import { API_URL } from '../../utils/api';
import './CenterPane.css';

/**
 * CenterPane - Editor area with Tiptap (Phase 2, enhanced in Phase 4)
 * Toggle between read-only and edit mode
 * Exposes editor state to WorkspaceContext for real-time context panels
 */
function CenterPane() {
  const { selectedNoteId, selectNote, updateEditorState, noteRefreshTrigger } = useWorkspaceState();
  const queryClient = useQueryClient();
  const [note, setNote] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [allNotes, setAllNotes] = useState([]);
  const [allTags, setAllTags] = useState([]);

  useEffect(() => {
    if (selectedNoteId) {
      fetchNote(selectedNoteId);
      setIsEditMode(false);
      // Reset editor state when switching notes
      updateEditorState({
        editorInstance: null,
        noteTitle: '',
        wikilinks: [],
        hashtags: [],
        wordCount: 0,
        charCount: 0,
        isEditMode: false,
      });
    } else {
      setNote(null);
    }
  }, [selectedNoteId]);

  // Re-fetch note when external refresh is triggered (e.g., from UnlinkedMentionsPanel)
  useEffect(() => {
    if (selectedNoteId && noteRefreshTrigger > 0) {
      fetchNote(selectedNoteId);
    }
  }, [noteRefreshTrigger]);

  // Fetch all notes and tags for autocomplete
  useEffect(() => {
    fetchAllNotes();
    fetchAllTags();
  }, []);

  const fetchNote = async (noteId) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      if (!token) {
        if (process.env.NODE_ENV === 'development') console.error('No token found');
        return;
      }

      const response = await fetch(`${API_URL}/notes/${noteId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setNote(data);
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') console.error('Error fetching note:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllNotes = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch(`${API_URL}/notes/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAllNotes(data);
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') console.error('Error fetching all notes:', error);
    }
  };

  const fetchAllTags = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch(`${API_URL}/tags`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAllTags(data);
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') console.error('Error fetching all tags:', error);
    }
  };

  const handleSave = async (updatedData) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch(`${API_URL}/notes/${note.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: updatedData.title,
          content: updatedData.content,
          html_content: updatedData.html,  // Send HTML content for rich rendering
          tags: updatedData.tags,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setNote(data);
        setIsEditMode(false);

        // Invalidate React Query caches to refresh all context panels
        queryClient.invalidateQueries({ queryKey: ['note', note.id] });
        queryClient.invalidateQueries({ queryKey: ['backlinks', note.id] });
        queryClient.invalidateQueries({ queryKey: ['graphData', note.id] });
        queryClient.invalidateQueries({ queryKey: ['unlinkedMentions', note.id] });
        queryClient.invalidateQueries({ queryKey: ['notes'] }); // Refresh notes list

        // Refresh notes list for autocomplete
        fetchAllNotes();

        // Reset editor state
        updateEditorState({
          editorInstance: null,
          noteTitle: data.title,
          wikilinks: [],
          hashtags: [],
          wordCount: 0,
          charCount: 0,
          isEditMode: false,
        });
      } else {
        alert('Failed to save note');
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') console.error('Error saving note:', error);
      alert('Error saving note');
    }
  };

  const handleCancel = () => {
    setIsEditMode(false);
    // Reset editor state
    updateEditorState({
      editorInstance: null,
      noteTitle: note?.title || '',
      wikilinks: [],
      hashtags: [],
      wordCount: 0,
      charCount: 0,
      isEditMode: false,
    });
  };

  const handleWikilinkClick = (title) => {
    // Find note by title and navigate to it
    const linkedNote = allNotes.find(n => n.title === title);
    if (linkedNote) {
      selectNote(linkedNote.id);
    } else {
      alert(`Note "${title}" not found`);
    }
  };

  const handleHashtagClick = (tag) => {
    // Note: Tag filtering available in main Notes view (NoteViewer component)
    // Workspace view intentionally keeps hashtags as display-only for simplicity
    if (process.env.NODE_ENV === 'development') console.log('Hashtag clicked:', tag);
    alert(`Tag filtering is available in the Notes tab. Workspace view shows hashtags for reference.`);
  };

  // Show Daily View when no note is selected (default landing experience)
  if (!selectedNoteId) {
    // Use displayName if set, otherwise fall back to username
    const displayName = localStorage.getItem('displayName');
    const username = localStorage.getItem('username') || 'there';
    const nameToShow = displayName || username;
    return (
      <main className="workspace-center-pane center-pane-daily" aria-label="Daily view">
        <DailyView username={nameToShow} />
      </main>
    );
  }

  if (loading) {
    return (
      <main className="workspace-center-pane center-pane-loading" aria-label="Note editor" aria-busy="true">
        <div className="loading-spinner"></div>
        <p>Loading note...</p>
      </main>
    );
  }

  if (!note) {
    return (
      <main className="workspace-center-pane center-pane-empty" aria-label="Note editor">
        <FileText size={64} className="empty-icon" />
        <h2>Note not found</h2>
        <p>The selected note could not be loaded</p>
      </main>
    );
  }

  // Show Block Editor in edit mode (Phase 4: Block Canvas)
  if (isEditMode) {
    return (
      <main className="workspace-center-pane center-pane center-pane-edit" aria-label="Note editor">
        <BlockEditor
          note={note}
          allNotes={allNotes}
          allTags={allTags}
          onSave={handleSave}
          onCancel={handleCancel}
          onWikilinkClick={handleWikilinkClick}
          onHashtagClick={handleHashtagClick}
          onEditorReady={(editorInstance) => {
            // Pass editor instance to WorkspaceContext for real-time analysis
            updateEditorState({
              editorInstance,
              noteTitle: note?.title || '',
              isEditMode: true,
            });
          }}
        />
      </main>
    );
  }

  // Read-only view
  return (
    <main className="workspace-center-pane center-pane" aria-label="Note editor">
      {/* Edit button banner */}
      <div className="phase-notice">
        <Eye size={16} />
        <span>Read-only view</span>
        <button
          className="edit-mode-btn"
          onClick={() => setIsEditMode(true)}
        >
          <Edit2 size={16} />
          Edit Note
        </button>
      </div>

      {/* Note header */}
      <div className="note-header">
        <h1 className="note-title">{note.title || 'Untitled Note'}</h1>
        <div className="note-metadata">
          <div className="metadata-item">
            <Calendar size={14} />
            <span>Created: {format(new Date(note.created_at), 'PPP')}</span>
          </div>
          {note.updated_at && note.updated_at !== note.created_at && (
            <div className="metadata-item">
              <Calendar size={14} />
              <span>Updated: {format(new Date(note.updated_at), 'PPP')}</span>
            </div>
          )}
        </div>

        {/* Tags */}
        {note.tags && note.tags.length > 0 && (
          <div className="note-tags">
            {note.tags.map((tag, index) => (
              <span key={index} className="tag">
                #{tag.name || tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Note content */}
      <div className="note-content-container">
        <NoteContentRenderer
          content={note.content}
          htmlContent={note.html_content}
          className="note-content"
          onWikilinkClick={handleWikilinkClick}
          onHashtagClick={handleHashtagClick}
        />
      </div>
    </main>
  );
}

export default CenterPane;
