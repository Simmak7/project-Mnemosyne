/**
 * NoteDetailPanel - Note detail view panel
 */
import React from 'react';
import { Edit2 } from 'lucide-react';
import { formatDate, highlightText } from '../utils/noteUtils';

function NoteDetailPanel({ note, searchQuery, onEdit, onClose }) {
  return (
    <div className="note-detail-panel">
      <div className="note-detail-header">
        <h2>{note.title}</h2>
        <div className="note-detail-actions">
          <button
            className="edit-note-icon-btn"
            onClick={() => onEdit(note)}
            aria-label="Edit note"
          >
            <Edit2 className="w-5 h-5" />
          </button>
          <button
            className="close-button"
            onClick={onClose}
            aria-label="Close note"
          >
            &times;
          </button>
        </div>
      </div>
      <div className="note-detail-meta">
        <span>Created {formatDate(note.created_at)}</span>
        {note.updated_at && (
          <span> &bull; Updated {formatDate(note.updated_at)}</span>
        )}
      </div>
      <div className="note-detail-content">
        {searchQuery ? highlightText(note.content, searchQuery) : note.content}
      </div>
      {note.tags && note.tags.length > 0 && (
        <div className="note-detail-tags">
          <h4>Tags</h4>
          <div className="tag-list">
            {note.tags.map((tag, idx) => (
              <span key={idx} className="tag-chip">
                {tag.name || tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default NoteDetailPanel;
