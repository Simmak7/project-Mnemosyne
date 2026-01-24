import React, { useState, useCallback, useEffect } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { format } from 'date-fns';
import MDEditor from '@uiw/react-md-editor';
import { Plus, Edit2, Trash2, X, Save } from 'lucide-react';
import './VirtualizedNoteList.css';

function VirtualizedNoteList({ selectedNoteId, searchQuery, onNavigateToGraph }) {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedNote, setSelectedNote] = useState(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const parentRef = React.useRef(null);

  // Editor state
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editingNote, setEditingNote] = useState(null);
  const [editorTitle, setEditorTitle] = useState('');
  const [editorContent, setEditorContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Fetch notes from API
  const fetchNotes = useCallback(async (pageNum) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No token found');
        return [];
      }

      const response = await fetch(
        `http://localhost:8000/notes/?skip=${(pageNum - 1) * 50}&limit=50`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        return data;
      } else if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.reload();
      }
      return [];
    } catch (error) {
      console.error('Error fetching notes:', error);
      return [];
    }
  }, []);

  // Initial load
  useEffect(() => {
    const loadInitialNotes = async () => {
      setLoading(true);
      const initialNotes = await fetchNotes(1);
      setNotes(initialNotes);
      setHasMore(initialNotes.length === 50);
      setLoading(false);
    };
    loadInitialNotes();
  }, [fetchNotes]);

  // Auto-select note from search results
  useEffect(() => {
    if (selectedNoteId && notes.length > 0) {
      const noteToSelect = notes.find(note => note.id === selectedNoteId);
      if (noteToSelect) {
        setSelectedNote(noteToSelect);
      }
    }
  }, [selectedNoteId, notes]);

  // Load more notes
  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;

    setLoading(true);
    const nextPage = page + 1;
    const newNotes = await fetchNotes(nextPage);

    if (newNotes.length === 0) {
      setHasMore(false);
    } else {
      setNotes(prev => [...prev, ...newNotes]);
      setPage(nextPage);
      setHasMore(newNotes.length === 50);
    }
    setLoading(false);
  }, [fetchNotes, page, loading, hasMore]);

  // Open editor for new note
  const handleCreateNote = () => {
    setEditingNote(null);
    setEditorTitle('');
    setEditorContent('');
    setIsEditorOpen(true);
    setShowDeleteConfirm(false);
  };

  // Open editor for existing note
  const handleEditNote = (note, e) => {
    e?.stopPropagation();
    setEditingNote(note);
    setEditorTitle(note.title);
    setEditorContent(note.content);
    setIsEditorOpen(true);
    setShowDeleteConfirm(false);
  };

  // Close editor with unsaved changes warning
  const handleCloseEditor = () => {
    const hasChanges = editingNote
      ? (editorTitle !== editingNote.title || editorContent !== editingNote.content)
      : (editorTitle || editorContent);

    if (hasChanges) {
      const confirmed = window.confirm('You have unsaved changes. Are you sure you want to close?');
      if (!confirmed) return;
    }

    setIsEditorOpen(false);
    setEditingNote(null);
    setEditorTitle('');
    setEditorContent('');
    setShowDeleteConfirm(false);
  };

  // Save note (create or update)
  const handleSaveNote = async () => {
    if (!editorTitle.trim()) {
      alert('Please enter a title for your note');
      return;
    }

    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        alert('Please login first');
        return;
      }

      const url = editingNote
        ? `http://localhost:8000/notes/${editingNote.id}`
        : 'http://localhost:8000/notes/';

      const method = editingNote ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: editorTitle,
          content: editorContent,
        }),
      });

      if (response.ok) {
        const savedNote = await response.json();

        // Update notes list
        if (editingNote) {
          setNotes(prev =>
            prev.map(note => (note.id === editingNote.id ? savedNote : note))
          );
        } else {
          setNotes(prev => [savedNote, ...prev]);
        }

        // Close editor
        setIsEditorOpen(false);
        setEditingNote(null);
        setEditorTitle('');
        setEditorContent('');
        setSelectedNote(savedNote);
      } else if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.reload();
      } else {
        const errorData = await response.json();
        alert(`Error saving note: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error saving note:', error);
      alert(`Error saving note: ${error.message}`);
    } finally {
      setSaving(false);
    }
  };

  // Delete note
  const handleDeleteNote = async () => {
    if (!editingNote) return;

    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        alert('Please login first');
        return;
      }

      const response = await fetch(`http://localhost:8000/notes/${editingNote.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        // Remove note from list
        setNotes(prev => prev.filter(note => note.id !== editingNote.id));

        // Close editor
        setIsEditorOpen(false);
        setEditingNote(null);
        setEditorTitle('');
        setEditorContent('');
        setShowDeleteConfirm(false);
        setSelectedNote(null);
      } else if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.reload();
      } else {
        const errorData = await response.json();
        alert(`Error deleting note: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error deleting note:', error);
      alert(`Error deleting note: ${error.message}`);
    } finally {
      setSaving(false);
    }
  };

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

    if (
      lastItem.index >= notes.length - 1 &&
      hasMore &&
      !loading
    ) {
      loadMore();
    }
  }, [virtualizer.getVirtualItems(), notes.length, hasMore, loading, loadMore]);

  const virtualItems = virtualizer.getVirtualItems();

  // Format date helper
  const formatDate = (dateString) => {
    try {
      return format(new Date(dateString), 'MMM dd, yyyy');
    } catch {
      return 'Unknown date';
    }
  };

  // Extract snippet from content
  const getSnippet = (content, maxLength = 150) => {
    if (!content) return 'No content';
    // eslint-disable-next-line no-useless-escape
    const stripped = content.replace(/[#*`\[\]]/g, '').trim();
    return stripped.length > maxLength
      ? stripped.substring(0, maxLength) + '...'
      : stripped;
  };

  // Highlight search query in text
  const highlightText = (text, query) => {
    if (!query || !text) return text;

    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, index) =>
      part.toLowerCase() === query.toLowerCase() ? (
        <mark key={index} style={{ backgroundColor: '#ffd700', padding: '2px 4px', borderRadius: '3px' }}>
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

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
          <div className="empty-icon">📝</div>
          <h3>No notes yet</h3>
          <p>Upload and analyze images to create smart notes!</p>
        </div>
      ) : (
        <div className="notes-layout">
          {/* Virtual scrolling list */}
          <div
            ref={parentRef}
            className="notes-list-scroll"
            style={{
              height: '100%',
              overflow: 'auto',
            }}
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
                    className={`virtual-note-item ${
                      selectedNote?.id === note?.id ? 'active' : ''
                    }`}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      transform: `translateY(${virtualItem.start}px)`,
                    }}
                    onClick={() => !isLoaderRow && setSelectedNote(note)}
                  >
                    {isLoaderRow ? (
                      hasMore ? (
                        <div className="note-loader">
                          <div className="loading-spinner"></div>
                          <span>Loading more notes...</span>
                        </div>
                      ) : null
                    ) : (
                      <div className="note-card">
                        <div className="note-card-header">
                          <h3 className="note-title">{note.title}</h3>
                          <button
                            className="edit-note-btn"
                            onClick={(e) => handleEditNote(note, e)}
                            aria-label="Edit note"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                        </div>
                        <p className="note-snippet">{getSnippet(note.content)}</p>
                        <div className="note-meta">
                          <span className="note-date">
                            {formatDate(note.created_at)}
                          </span>
                          {note.tags && note.tags.length > 0 && (
                            <div className="note-tags">
                              {note.tags.slice(0, 3).map((tag, idx) => (
                                <span key={idx} className="tag-chip">
                                  {tag.name || tag}
                                </span>
                              ))}
                              {note.tags.length > 3 && (
                                <span className="tag-more">
                                  +{note.tags.length - 3}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Note detail panel */}
          {selectedNote && (
            <div className="note-detail-panel">
              <div className="note-detail-header">
                <h2>{selectedNote.title}</h2>
                <div className="note-detail-actions">
                  <button
                    className="edit-note-icon-btn"
                    onClick={(e) => handleEditNote(selectedNote, e)}
                    aria-label="Edit note"
                  >
                    <Edit2 className="w-5 h-5" />
                  </button>
                  <button
                    className="close-button"
                    onClick={() => setSelectedNote(null)}
                    aria-label="Close note"
                  >
                    ×
                  </button>
                </div>
              </div>
              <div className="note-detail-meta">
                <span>Created {formatDate(selectedNote.created_at)}</span>
                {selectedNote.updated_at && (
                  <span> • Updated {formatDate(selectedNote.updated_at)}</span>
                )}
              </div>
              <div className="note-detail-content">
                {searchQuery ? highlightText(selectedNote.content, searchQuery) : selectedNote.content}
              </div>
              {selectedNote.tags && selectedNote.tags.length > 0 && (
                <div className="note-detail-tags">
                  <h4>Tags</h4>
                  <div className="tag-list">
                    {selectedNote.tags.map((tag, idx) => (
                      <span key={idx} className="tag-chip">
                        {tag.name || tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Note Editor Modal */}
      {isEditorOpen && (
        <div className="note-editor-overlay" onClick={handleCloseEditor}>
          <div className="note-editor-modal" onClick={(e) => e.stopPropagation()}>
            <div className="editor-header">
              <h2>{editingNote ? 'Edit Note' : 'Create New Note'}</h2>
              <button
                className="close-button"
                onClick={handleCloseEditor}
                aria-label="Close editor"
                disabled={saving}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="editor-content">
              <div className="editor-field">
                <label htmlFor="note-title">Title</label>
                <input
                  id="note-title"
                  type="text"
                  value={editorTitle}
                  onChange={(e) => setEditorTitle(e.target.value)}
                  placeholder="Enter note title..."
                  disabled={saving}
                  autoFocus
                />
              </div>

              <div className="editor-field editor-md">
                <label>Content</label>
                <div className="md-editor-hint">
                  Use <code>[[Note Title]]</code> for wikilinks and <code>#tag</code> for tags
                </div>
                <MDEditor
                  value={editorContent}
                  onChange={setEditorContent}
                  preview="live"
                  height={400}
                  disabled={saving}
                  textareaProps={{
                    placeholder: 'Write your note content here...\n\nTip: Use [[Note Title]] to link to other notes and #tag for tags',
                  }}
                />
              </div>
            </div>

            <div className="editor-footer">
              <div className="editor-footer-left">
                {editingNote && (
                  showDeleteConfirm ? (
                    <div className="delete-confirm">
                      <span>Delete this note?</span>
                      <button
                        className="btn-delete-confirm"
                        onClick={handleDeleteNote}
                        disabled={saving}
                      >
                        Yes, Delete
                      </button>
                      <button
                        className="btn-cancel"
                        onClick={() => setShowDeleteConfirm(false)}
                        disabled={saving}
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      className="btn-delete"
                      onClick={() => setShowDeleteConfirm(true)}
                      disabled={saving}
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  )
                )}
              </div>
              <div className="editor-footer-right">
                <button
                  className="btn-cancel"
                  onClick={handleCloseEditor}
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  className="btn-save"
                  onClick={handleSaveNote}
                  disabled={saving || !editorTitle.trim()}
                >
                  <Save className="w-4 h-4" />
                  {saving ? 'Saving...' : 'Save Note'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Memoize component to prevent unnecessary re-renders
export default React.memo(VirtualizedNoteList);
