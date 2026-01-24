import React from 'react';
import NoteHierarchy from './NoteHierarchy';

/**
 * LeftPane - Navigation and note hierarchy
 */
function LeftPane() {
  return (
    <nav className="workspace-left-pane" aria-label="Note hierarchy">
      <NoteHierarchy />
    </nav>
  );
}

export default LeftPane;
