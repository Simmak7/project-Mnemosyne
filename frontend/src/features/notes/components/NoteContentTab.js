import React, { useState, useCallback } from 'react';
import { Hash, Plus, X } from 'lucide-react';
import NoteContentRenderer from '../../../components/common/NoteContentRenderer';
import { api } from '../../../utils/api';

/**
 * NoteContentTab - Content tab showing note body and tags
 */
function NoteContentTab({ note, onWikilinkClick, onTagClick }) {
  const [tags, setTags] = useState(note.tags || []);
  const [tagInput, setTagInput] = useState('');
  const [isAddingTag, setIsAddingTag] = useState(false);

  // Add tag to note
  const addTag = useCallback(async (tagName) => {
    if (!tagName.trim()) return;

    // Remove # if user typed it
    const cleanTagName = tagName.replace(/^#/, '').trim();
    if (!cleanTagName) return;

    try {
      const result = await api.post(`/notes/${note.id}/tags/${encodeURIComponent(cleanTagName)}`);
      // API returns { status: "success", tag_id: id, tag_name: name }
      setTags(prev => [...prev, { id: result.tag_id, name: result.tag_name }]);
      setTagInput('');
      setIsAddingTag(false);
    } catch (err) {
      console.error('Error adding tag:', err);
    }
  }, [note.id]);

  // Remove tag from note
  const removeTag = useCallback(async (tagId) => {
    try {
      await api.delete(`/notes/${note.id}/tags/${tagId}`);
      setTags(prev => prev.filter(t => t.id !== tagId));
    } catch (err) {
      console.error('Error removing tag:', err);
    }
  }, [note.id]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && tagInput) {
      e.preventDefault();
      addTag(tagInput);
    }
    if (e.key === 'Escape') {
      setIsAddingTag(false);
      setTagInput('');
    }
  };

  return (
    <div className="note-content-tab">
      {/* Note content */}
      <div className="note-body">
        <NoteContentRenderer
          content={note.content}
          htmlContent={note.html_content}
          onWikilinkClick={onWikilinkClick}
          onHashtagClick={onTagClick}
          className="note-content-main"
        />
      </div>

      {/* Tags section */}
      <div className="note-tags-section">
        <div className="tags-header">
          <Hash size={14} />
          <span>Tags</span>
        </div>

        <div className="tags-list">
          {tags.map(tag => (
            <span key={tag.id} className="tag-pill" onClick={() => onTagClick && onTagClick(tag.name)}>
              <Hash size={10} />
              {tag.name}
              <button
                className="tag-remove"
                onClick={(e) => {
                  e.stopPropagation();
                  removeTag(tag.id);
                }}
              >
                <X size={10} />
              </button>
            </span>
          ))}

          {/* Add tag */}
          {isAddingTag ? (
            <div className="tag-input-wrapper">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleKeyDown}
                onBlur={() => {
                  if (!tagInput) setIsAddingTag(false);
                }}
                placeholder="tag name"
                className="tag-input"
                autoFocus
              />
            </div>
          ) : (
            <button className="add-tag-btn" onClick={() => setIsAddingTag(true)}>
              <Plus size={12} />
              Add Tag
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default NoteContentTab;
