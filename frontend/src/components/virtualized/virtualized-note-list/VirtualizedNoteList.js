/**
 * VirtualizedNoteList - Main component with virtualized note list
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Plus } from 'lucide-react';
import { useNoteList } from './hooks/useNoteList';
import NoteCard from './components/NoteCard';
import NoteDetailPanel from './components/NoteDetailPanel';
import NoteEditorModal from './components/NoteEditorModal';
import { API_URL } from '../../../utils/api';
import '../VirtualizedNoteList.css';

function VirtualizedNoteList({ selectedNoteId, searchQuery, onNavigateToGraph }) {
  const parentRef = React.useRef(null);
  const [selectedNote, setSelectedNote] = useState(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editingNote, setEditingNote] = useState(null);

  const {
    notes,
    loading,
    hasMore,
    loadMore,
    addNote,
    updateNote,
    removeNote,
  } = useNoteList();

  // Auto-select note from search results
  useEffect(() => {
    if (selectedNoteId && notes.length > 0) {
      const noteToSelect = notes.find(note => note.id === selectedNoteId);
      if (noteToSelect) {
        setSelectedNote(noteToSelect);
      }
    }
  }, [selectedNoteId, notes]);

  // Virtualizer setup
  const virtualizer = useVirtualizer({
    count: hasMore ? notes.length + 1 : notes.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 120,
    overscan: 5,
  });

  // Handle scroll for infinite loading
  useEffect(() => {
    const [lastItem] = [...virtualizer.getVirtualItems()].reverse();
    if (!lastItem) return;

    if (lastItem.index >= notes.length - 1 && hasMore && !loading) {
      loadMore();
    }
  }, [virtualizer.getVirtualItems(), notes.length, hasMore, loading, loadMore]);

  const virtualItems = virtualizer.getVirtualItems();

  const handleCreateNote = () => {
    setEditingNote(null);
    setIsEditorOpen(true);
  };

  const handleEditNote = (note) => {
    setEditingNote(note);
    setIsEditorOpen(true);
  };

  const handleCloseEditor = () => {
    setIsEditorOpen(false);
    setEditingNote(null);
  };

  const handleSaveNote = useCallback(async ({ title, content }) => {
    const token = localStorage.getItem('token');
    if (!token) {
      alert('Please login first');
      return;
    }

    const url = editingNote
      ? `${API_URL}/notes/${editingNote.id}`
      : `${API_URL}/notes/`;

    const method = editingNote ? 'PUT' : 'POST';

    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ title, content }),
    });

    if (response.ok) {
      const savedNote = await response.json();
      if (editingNote) {
        updateNote(savedNote);
      } else {
        addNote(savedNote);
      }
      setSelectedNote(savedNote);
      handleCloseEditor();
    } else if (response.status === 401 || response.status === 403) {
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      window.location.reload();
    } else {
      const errorData = await response.json();
      alert(`Error saving note: ${errorData.detail || 'Unknown error'}`);
    }
  }, [editingNote, addNote, updateNote]);

  const handleDeleteNote = useCallback(async () => {
    if (!editingNote) return;

    const token = localStorage.getItem('token');
    if (!token) {
      alert('Please login first');
      return;
    }

    const response = await fetch(`${API_URL}/notes/${editingNote.id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` },
    });

    if (response.ok) {
      removeNote(editingNote.id);
      handleCloseEditor();
      setSelectedNote(null);
    } else if (response.status === 401 || response.status === 403) {
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      window.location.reload();
    } else {
      const errorData = await response.json();
      alert(`Error deleting note: ${errorData.detail || 'Unknown error'}`);
    }
  }, [editingNote, removeNote]);

  return (
    <div className="virtualized-note-list-container">
      <div className="note-list-header">
        <div className="header-left">
          <h2>Smart Notes</h2>
          <div className="note-count">
            {notes.length} note{notes.length !== 1 ? 's' : ''}
            {loading && ' (loading...)'}
          </div>
        </div>
        <button className="create-note-btn" onClick={handleCreateNote}>
          <Plus className="w-4 h-4" />
          Create Note
        </button>
      </div>

      {notes.length === 0 && !loading ? (
        <div className="empty-state">
          <div className="empty-icon">&#128221;</div>
          <h3>No notes yet</h3>
          <p>Upload and analyze images to create smart notes!</p>
        </div>
      ) : (
        <div className="notes-layout">
          <div
            ref={parentRef}
            className="notes-list-scroll"
            style={{ height: '100%', overflow: 'auto' }}
          >
            <div
              style={{
                height: `${virtualizer.getTotalSize()}px`,
                width: '100%',
                position: 'relative',
              }}
            >
              {virtualItems.map((virtualItem) => {
                const isLoaderRow = virtualItem.index > notes.length - 1;
                const note = notes[virtualItem.index];

                return (
                  <div
                    key={virtualItem.key}
                    data-index={virtualItem.index}
                    ref={virtualizer.measureElement}
                    className={`virtual-note-item ${selectedNote?.id === note?.id ? 'active' : ''}`}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      transform: `translateY(${virtualItem.start}px)`,
                    }}
                  >
                    {isLoaderRow ? (
                      hasMore ? (
                        <div className="note-loader">
                          <div className="loading-spinner"></div>
                          <span>Loading more notes...</span>
                        </div>
                      ) : null
                    ) : (
                      <NoteCard
                        note={note}
                        isActive={selectedNote?.id === note?.id}
                        onClick={() => setSelectedNote(note)}
                        onEdit={handleEditNote}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {selectedNote && (
            <NoteDetailPanel
              note={selectedNote}
              searchQuery={searchQuery}
              onEdit={handleEditNote}
              onClose={() => setSelectedNote(null)}
            />
          )}
        </div>
      )}

      {isEditorOpen && (
        <NoteEditorModal
          note={editingNote}
          initialTitle={editingNote?.title || ''}
          initialContent={editingNote?.content || ''}
          onSave={handleSaveNote}
          onDelete={handleDeleteNote}
          onClose={handleCloseEditor}
        />
      )}
    </div>
  );
}

export default React.memo(VirtualizedNoteList);
