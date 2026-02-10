import React from 'react';
import NoteContentRenderer from '../../../../components/common/NoteContentRenderer';
import { useJournalContext } from '../../hooks/JournalContext';

/**
 * ContentRenderer - Renders the daily note content in read mode.
 * Delegates to NoteContentRenderer with checkbox toggle support.
 */
function ContentRenderer({ onWikilinkClick }) {
  const { dailyNote, toggleCheckbox } = useJournalContext();

  if (!dailyNote) return null;

  // Strip the Caption: line from rendered content (it's shown in DayCaption)
  const displayContent = (dailyNote.content || '')
    .replace(/^Caption:\s*.+\n?/m, '');

  return (
    <div className="journal-content-renderer">
      <NoteContentRenderer
        content={displayContent}
        htmlContent={dailyNote.html_content}
        onCheckboxToggle={(lineText, checked) => {
          toggleCheckbox(lineText, checked);
        }}
        onWikilinkClick={onWikilinkClick}
        className="journal-note-content"
      />
    </div>
  );
}

export default ContentRenderer;
