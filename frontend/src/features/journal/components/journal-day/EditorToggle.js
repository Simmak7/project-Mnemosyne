import React from 'react';
import { Eye, Pencil } from 'lucide-react';
import { useJournalEditor } from '../../hooks/useJournalEditor';

/**
 * EditorToggle - View/Edit mode switch button.
 */
function EditorToggle() {
  const { isEditing, toggleEdit } = useJournalEditor();

  return (
    <button
      className="editor-toggle-btn"
      onClick={toggleEdit}
      title={isEditing ? 'Switch to view mode' : 'Switch to edit mode'}
      aria-label={isEditing ? 'View mode' : 'Edit mode'}
    >
      {isEditing ? <Eye size={16} /> : <Pencil size={16} />}
      <span>{isEditing ? 'View' : 'Edit'}</span>
    </button>
  );
}

export default EditorToggle;
