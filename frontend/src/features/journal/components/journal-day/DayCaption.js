import React, { useState, useRef, useEffect } from 'react';
import { Pencil, Check, X } from 'lucide-react';
import { useJournalContext } from '../../hooks/JournalContext';
import './DayCaption.css';

/**
 * DayCaption - Inline editable caption for the daily note.
 * Stored as "Caption: text" line in the note content.
 */
function DayCaption() {
  const { dailyNote, updateContent } = useJournalContext();
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState('');
  const inputRef = useRef(null);

  const currentCaption = parseCaption(dailyNote?.content || '');

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const startEditing = () => {
    setDraft(currentCaption);
    setIsEditing(true);
  };

  const save = async () => {
    const trimmed = draft.trim();
    if (trimmed === currentCaption) {
      setIsEditing(false);
      return;
    }

    const content = dailyNote?.content || '';
    const updated = upsertCaption(content, trimmed);
    await updateContent(updated);
    setIsEditing(false);
  };

  const cancel = () => {
    setIsEditing(false);
    setDraft('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); save(); }
    if (e.key === 'Escape') { e.preventDefault(); cancel(); }
  };

  if (!dailyNote) return null;

  if (isEditing) {
    return (
      <div className="day-caption day-caption--editing">
        <input
          ref={inputRef}
          className="day-caption-input"
          value={draft}
          onChange={e => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="What's today about?"
          maxLength={80}
        />
        <button className="day-caption-btn day-caption-save" onClick={save} aria-label="Save">
          <Check size={14} />
        </button>
        <button className="day-caption-btn day-caption-cancel" onClick={cancel} aria-label="Cancel">
          <X size={14} />
        </button>
      </div>
    );
  }

  return (
    <button className="day-caption" onClick={startEditing} title="Add a caption for today">
      {currentCaption ? (
        <span className="day-caption-text">{currentCaption}</span>
      ) : (
        <span className="day-caption-placeholder">+ Add caption...</span>
      )}
      <Pencil size={12} className="day-caption-edit-icon" />
    </button>
  );
}

/** Parse "Caption: text" from content */
function parseCaption(content) {
  const match = content.match(/^Caption:\s*(.+)$/m);
  return match ? match[1].trim() : '';
}

/** Insert or update "Caption: text" in content */
function upsertCaption(content, caption) {
  const hasCaption = /^Caption:\s*.+$/m.test(content);

  if (!caption) {
    // Remove existing caption line
    return content.replace(/^Caption:\s*.+\n?/m, '').trim();
  }

  if (hasCaption) {
    return content.replace(/^Caption:\s*.+$/m, `Caption: ${caption}`);
  }

  // Insert after the first heading or at the very top
  const lines = content.split('\n');
  let insertIdx = 0;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].startsWith('#')) { insertIdx = i + 1; break; }
  }

  lines.splice(insertIdx, 0, `Caption: ${caption}`);
  return lines.join('\n');
}

export default DayCaption;
