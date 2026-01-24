import React, { useEffect, useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { X, Plus, Hash, Network } from 'lucide-react';
import './NoteViewer.css';

function NoteViewer({ notes, onNavigateToGraph }) {
  const [notesList, setNotesList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedNote, setSelectedNote] = useState(null);
  const [tags, setTags] = useState([]);
  const [tagInput, setTagInput] = useState('');
  const [availableTags, setAvailableTags] = useState([]);
  const [backlinks, setBacklinks] = useState([]);
  const [linkedNotes, setLinkedNotes] = useState([]);

  useEffect(() => {
    fetchNotes();
    fetchAvailableTags();
  }, []);

  // Fetch all available tags
  const fetchAvailableTags = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch('http://localhost:8000/tags/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAvailableTags(data);
      }
    } catch (error) {
      console.error('Error fetching tags:', error);
    }
  };

  const fetchNotes = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No token found, user needs to login');
        setLoading(false);
        return;
      }

      // Use the enhanced notes endpoint
      const response = await fetch('http://localhost:8000/notes-enhanced/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setNotesList(data);
      } else if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.reload();
      } else {
        console.error('Failed to fetch notes:', response.status);
      }
    } catch (error) {
      console.error('Error fetching notes:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch note details with backlinks when selected
  const handleNoteSelect = useCallback(async (note) => {
    setSelectedNote(note);
    setTags(note.tags || []);
    setLinkedNotes(note.linked_notes || []);

    // Fetch backlinks details if available
    if (note.backlinks && note.backlinks.length > 0) {
      fetchBacklinks(note.backlinks);
    } else {
      setBacklinks([]);
    }
  }, []);

  const fetchBacklinks = async (backlinkIds) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      // Add null/empty check before .map()
      if (!backlinkIds || backlinkIds.length === 0) {
        setBacklinks([]);
        return;
      }

      const promises = backlinkIds.map(id =>
        fetch(`http://localhost:8000/notes/${id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }).then(r => r.ok ? r.json() : null)
      );

      const notes = await Promise.all(promises);
      setBacklinks(notes.filter(n => n !== null));
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Error fetching backlinks:', error);
      }
      setBacklinks([]);
    }
  };

  // Add tag to note
  const addTag = async (tagName) => {
    if (!selectedNote || !tagName.trim()) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/notes/${selectedNote.id}/tags/${tagName}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const newTag = await response.json();
        setTags([...tags, newTag]);
        setTagInput('');
        // Refresh available tags
        fetchAvailableTags();
      }
    } catch (error) {
      console.error('Error adding tag:', error);
    }
  };

  // Remove tag from note
  const removeTag = async (tagId) => {
    if (!selectedNote) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/notes/${selectedNote.id}/tags/${tagId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        setTags(tags.filter(t => t.id !== tagId));
      }
    } catch (error) {
      console.error('Error removing tag:', error);
    }
  };

  // Handle wikilink click
  const handleWikilinkClick = useCallback((noteTitle) => {
    // Find note by title (slug)
    const targetNote = notesList.find(n =>
      n.title.toLowerCase() === noteTitle.toLowerCase() ||
      n.slug === noteTitle.toLowerCase()
    );

    if (targetNote) {
      handleNoteSelect(targetNote);
    }
  }, [notesList, handleNoteSelect]);

  // Custom markdown components with wikilink support
  const markdownComponents = {
    p: ({ children }) => {
      // Parse wikilinks in paragraph text
      if (typeof children === 'string') {
        const parts = children.split(/(\[\[.*?\]\])/g);
        return (
          <p>
            {parts.map((part, i) => {
              if (part.startsWith('[[') && part.endsWith(']]')) {
                const target = part.slice(2, -2);
                const [noteTitle, alias] = target.split('|');
                return (
                  <span
                    key={i}
                    className="wikilink"
                    onClick={() => handleWikilinkClick(noteTitle)}
                  >
                    {alias || noteTitle}
                  </span>
                );
              }
              return part;
            })}
          </p>
        );
      }
      return <p>{children}</p>;
    },
  };

  return (
    <div className="component-container">
      <h2>Smart Notes</h2>
      {loading ? (
        <div className="loading-container">
          <div className="loading"></div>
          <p>Loading notes...</p>
        </div>
      ) : notesList.length === 0 ? (
        <p className="no-notes">No notes yet. Upload and analyze images to create smart notes!</p>
      ) : (
        <div className="notes-container">
          <div className="notes-list">
            {notesList.map((note) => (
              <div
                key={note.id}
                className={`note-item ${selectedNote?.id === note.id ? 'active' : ''}`}
                onClick={() => handleNoteSelect(note)}
              >
                <h3>{note.title}</h3>
                <p className="note-preview">{note.content.substring(0, 100)}...</p>

                {/* Show tags on note preview */}
                {note.tags && note.tags.length > 0 && (
                  <div className="note-preview-tags">
                    {note.tags.slice(0, 3).map(tag => (
                      <span key={tag.id} className="preview-tag">
                        #{tag.name}
                      </span>
                    ))}
                    {note.tags.length > 3 && (
                      <span className="preview-tag-more">+{note.tags.length - 3}</span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {selectedNote && (
            <div className="note-detail">
              <div className="note-header">
                <div className="note-header-left">
                  <h2>{selectedNote.title}</h2>

                  {/* View in Graph Button */}
                  {onNavigateToGraph && (
                    <button
                      className="open-in-graph-btn"
                      onClick={() => onNavigateToGraph(selectedNote.id)}
                      title="Open in knowledge graph"
                    >
                      <Network className="w-4 h-4" />
                      View in Graph
                    </button>
                  )}
                </div>

                <button
                  className="close-button"
                  onClick={() => setSelectedNote(null)}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Tags Section */}
              <div className="note-tags">
                <div className="tags-header">
                  <Hash className="w-4 h-4" />
                  <span>Tags</span>
                </div>
                <div className="tags-container">
                  {tags.map(tag => (
                    <span key={tag.id} className="tag">
                      <Hash className="w-3 h-3" />
                      {tag.name}
                      <button onClick={() => removeTag(tag.id)} className="tag-remove">
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}

                  {/* Tag Input */}
                  <div className="tag-input-wrapper">
                    <input
                      type="text"
                      value={tagInput}
                      onChange={(e) => setTagInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && tagInput) {
                          addTag(tagInput);
                        }
                      }}
                      placeholder="Add tag..."
                      className="tag-input"
                      list="available-tags"
                    />
                    {tagInput && (
                      <button
                        onClick={() => addTag(tagInput)}
                        className="tag-add-btn"
                        title="Add tag"
                      >
                        <Plus className="w-3 h-3" />
                      </button>
                    )}
                    <datalist id="available-tags">
                      {availableTags.map(tag => (
                        <option key={tag.id} value={tag.name} />
                      ))}
                    </datalist>
                  </div>
                </div>
              </div>

              {/* Note Content with Markdown and Wikilinks */}
              <div className="note-content">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={markdownComponents}
                >
                  {selectedNote.content}
                </ReactMarkdown>
              </div>

              {/* Linked Notes Section */}
              {linkedNotes && linkedNotes.length > 0 && (
                <div className="linked-notes-panel">
                  <h3>Linked Notes ({linkedNotes.length})</h3>
                  {linkedNotes.map(note => (
                    <div
                      key={note.id}
                      className="linked-note-item"
                      onClick={() => handleNoteSelect(note)}
                    >
                      <div className="linked-note-title">{note.title}</div>
                      <div className="linked-note-preview">{note.content.substring(0, 100)}...</div>
                    </div>
                  ))}
                </div>
              )}

              {/* Backlinks Panel */}
              <div className="backlinks-panel">
                <h3>Linked References ({backlinks.length})</h3>
                {backlinks.map(note => (
                  <div
                    key={note.id}
                    className="backlink-item"
                    onClick={() => handleNoteSelect(note)}
                  >
                    <div className="backlink-title">{note.title}</div>
                    <div className="backlink-preview">{note.content.substring(0, 100)}...</div>
                  </div>
                ))}
                {backlinks.length === 0 && (
                  <div className="no-backlinks">No notes link to this one yet</div>
                )}
              </div>

              {/* Related Images */}
              {selectedNote.images && selectedNote.images.length > 0 && (
                <div className="related-images-panel">
                  <h3>Related Images ({selectedNote.images.length})</h3>
                  <div className="related-images-grid">
                    {selectedNote.images.map(image => (
                      <div key={image.id} className="related-image">
                        <img
                          src={`http://localhost:8000/image/${image.id}`}
                          alt={image.filename}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default NoteViewer;
