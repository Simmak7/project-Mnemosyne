import React from 'react';

/**
 * Editor footer with keyboard shortcuts hint and unsaved indicator
 */
function EditorFooter({ hasChanges }) {
  return (
    <div className="ng-block-editor-footer">
      <span className="ng-block-editor-hint">
        <kbd>/</kbd> commands
        <kbd>[[</kbd> link note
        <kbd>#</kbd> tag
      </span>
      {hasChanges && (
        <span className="ng-block-editor-unsaved">Unsaved changes</span>
      )}
    </div>
  );
}

export default EditorFooter;
