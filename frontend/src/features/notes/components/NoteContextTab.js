import React, { useState, useEffect } from 'react';
import { ArrowUpRight, ArrowDownLeft, Image, FileText, Link2 } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * NoteContextTab - Shows linked notes, backlinks, and related images
 */
function NoteContextTab({ note, onNoteClick, onImageClick }) {
  const [linkedNotes, setLinkedNotes] = useState([]);
  const [backlinks, setBacklinks] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch linked notes and backlinks details
  useEffect(() => {
    const fetchContext = async () => {
      setLoading(true);
      const token = localStorage.getItem('token');
      if (!token) return;

      try {
        // Fetch linked notes details
        if (note.linked_notes && note.linked_notes.length > 0) {
          const linkedPromises = note.linked_notes.map(id =>
            fetch(`${API_BASE}/notes/${id}`, {
              headers: { 'Authorization': `Bearer ${token}` }
            }).then(r => r.ok ? r.json() : null)
          );
          const linked = await Promise.all(linkedPromises);
          setLinkedNotes(linked.filter(n => n !== null));
        }

        // Fetch backlink details
        if (note.backlinks && note.backlinks.length > 0) {
          const backlinkPromises = note.backlinks.map(id =>
            fetch(`${API_BASE}/notes/${id}`, {
              headers: { 'Authorization': `Bearer ${token}` }
            }).then(r => r.ok ? r.json() : null)
          );
          const backs = await Promise.all(backlinkPromises);
          setBacklinks(backs.filter(n => n !== null));
        }
      } catch (err) {
        console.error('Error fetching context:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchContext();
  }, [note.linked_notes, note.backlinks]);

  const hasContent = linkedNotes.length > 0 || backlinks.length > 0 ||
                     (note.image_ids && note.image_ids.length > 0);

  if (loading) {
    return (
      <div className="note-context-tab loading">
        <div className="context-loading">Loading context...</div>
      </div>
    );
  }

  if (!hasContent) {
    return (
      <div className="note-context-tab empty">
        <div className="context-empty">
          <Link2 size={32} />
          <h4>No connections yet</h4>
          <p>This note isn't linked to any other notes or images</p>
        </div>
      </div>
    );
  }

  return (
    <div className="note-context-tab">
      {/* Outgoing links (this note links to) */}
      {linkedNotes.length > 0 && (
        <section className="context-section">
          <h4 className="section-header">
            <ArrowUpRight size={14} />
            Links to ({linkedNotes.length})
          </h4>
          <div className="note-list">
            {linkedNotes.map(linkedNote => (
              <button
                key={linkedNote.id}
                className="context-note-item"
                onClick={() => onNoteClick(linkedNote.id)}
              >
                <FileText size={14} className="note-icon" />
                <div className="note-info">
                  <span className="note-title">{linkedNote.title}</span>
                  <span className="note-preview">
                    {linkedNote.content?.substring(0, 80)}...
                  </span>
                </div>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Incoming links (backlinks) */}
      {backlinks.length > 0 && (
        <section className="context-section">
          <h4 className="section-header">
            <ArrowDownLeft size={14} />
            Linked from ({backlinks.length})
          </h4>
          <div className="note-list">
            {backlinks.map(backlink => (
              <button
                key={backlink.id}
                className="context-note-item"
                onClick={() => onNoteClick(backlink.id)}
              >
                <FileText size={14} className="note-icon" />
                <div className="note-info">
                  <span className="note-title">{backlink.title}</span>
                  <span className="note-preview">
                    {backlink.content?.substring(0, 80)}...
                  </span>
                </div>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Related images */}
      {note.image_ids && note.image_ids.length > 0 && (
        <section className="context-section">
          <h4 className="section-header">
            <Image size={14} />
            Related Images ({note.image_ids.length})
          </h4>
          <div className="image-grid">
            {note.image_ids.map(imageId => (
              <button
                key={imageId}
                className="context-image-item"
                onClick={() => onImageClick && onImageClick(imageId)}
              >
                <img
                  src={`${API_BASE}/image/${imageId}`}
                  alt="Related"
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default NoteContextTab;
