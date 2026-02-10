import React from 'react';
import { Save, X, Eye, EyeOff } from 'lucide-react';

/**
 * Header toolbar with title input and actions
 */
function EditorToolbar({
  title,
  setTitle,
  hasChanges,
  setHasChanges,
  isPreview,
  setIsPreview,
  onSave,
  onCancel,
}) {
  return (
    <div className="ng-block-editor-toolbar">
      <input
        type="text"
        className="ng-block-editor-title"
        value={title}
        onChange={(e) => {
          setTitle(e.target.value);
          setHasChanges(true);
        }}
        placeholder="Untitled"
      />

      <div className="ng-block-editor-actions">
        <button
          onClick={() => setIsPreview(!isPreview)}
          className="ng-btn ng-btn-icon"
          title={isPreview ? 'Edit mode' : 'Preview mode'}
        >
          {isPreview ? <Eye size={18} /> : <EyeOff size={18} />}
        </button>
        <button
          onClick={onSave}
          className="ng-btn ng-btn-primary"
          disabled={!hasChanges}
        >
          <Save size={16} />
          Save
        </button>
        <button
          onClick={onCancel}
          className="ng-btn ng-btn-ghost"
        >
          <X size={16} />
          Cancel
        </button>
      </div>
    </div>
  );
}

export default EditorToolbar;
