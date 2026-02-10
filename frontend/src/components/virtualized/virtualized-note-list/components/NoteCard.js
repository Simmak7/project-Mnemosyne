/**
 * NoteCard - Individual note card in the list
 */
import React from 'react';
import { Edit2 } from 'lucide-react';
import { formatDate, getSnippet } from '../utils/noteUtils';

function NoteCard({ note, isActive, onClick, onEdit }) {
  return (
    <div
      className={`note-card ${isActive ? 'active' : ''}`}
      onClick={onClick}
    >
      <div className="note-card-header">
        <h3 className="note-title">{note.title}</h3>
        <button
          className="edit-note-btn"
          onClick={(e) => {
            e.stopPropagation();
            onEdit(note);
          }}
          aria-label="Edit note"
        >
          <Edit2 className="w-4 h-4" />
        </button>
      </div>
      <p className="note-snippet">{getSnippet(note.content)}</p>
      <div className="note-meta">
        <span className="note-date">{formatDate(note.created_at)}</span>
        {note.tags && note.tags.length > 0 && (
          <div className="note-tags">
            {note.tags.slice(0, 3).map((tag, idx) => (
              <span key={idx} className="tag-chip">
                {tag.name || tag}
              </span>
            ))}
            {note.tags.length > 3 && (
              <span className="tag-more">+{note.tags.length - 3}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default NoteCard;
