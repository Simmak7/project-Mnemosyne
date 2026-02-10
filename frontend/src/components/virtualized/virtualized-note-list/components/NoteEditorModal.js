/**
 * NoteEditorModal - Note editor modal for create/edit
 */
import React, { useState } from 'react';
import MDEditor from '@uiw/react-md-editor';
import { X, Save, Trash2 } from 'lucide-react';

function NoteEditorModal({
  note,
  initialTitle,
  initialContent,
  onSave,
  onDelete,
  onClose,
}) {
  const [title, setTitle] = useState(initialTitle);
  const [content, setContent] = useState(initialContent);
  const [saving, setSaving] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const isEditing = !!note;

  const handleClose = () => {
    const hasChanges = isEditing
      ? (title !== note.title || content !== note.content)
      : (title || content);

    if (hasChanges) {
      const confirmed = window.confirm('You have unsaved changes. Are you sure you want to close?');
      if (!confirmed) return;
    }
    onClose();
  };

  const handleSave = async () => {
    if (!title.trim()) {
      alert('Please enter a title for your note');
      return;
    }

    setSaving(true);
    try {
      await onSave({ title, content });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    setSaving(true);
    try {
      await onDelete();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="note-editor-overlay" onClick={handleClose}>
      <div className="note-editor-modal" onClick={(e) => e.stopPropagation()}>
        <div className="editor-header">
          <h2>{isEditing ? 'Edit Note' : 'Create New Note'}</h2>
          <button
            className="close-button"
            onClick={handleClose}
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
              value={title}
              onChange={(e) => setTitle(e.target.value)}
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
              value={content}
              onChange={setContent}
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
            {isEditing && (
              showDeleteConfirm ? (
                <div className="delete-confirm">
                  <span>Delete this note?</span>
                  <button
                    className="btn-delete-confirm"
                    onClick={handleDelete}
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
              onClick={handleClose}
              disabled={saving}
            >
              Cancel
            </button>
            <button
              className="btn-save"
              onClick={handleSave}
              disabled={saving || !title.trim()}
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save Note'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default NoteEditorModal;
