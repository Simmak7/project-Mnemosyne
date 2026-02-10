import React, { lazy, Suspense } from 'react';
import { Loader2, BookOpen } from 'lucide-react';
import { api } from '../../../../utils/api';
import { useJournalContext } from '../../hooks/JournalContext';
import { useJournalEditor } from '../../hooks/useJournalEditor';
import DayHeader from './DayHeader';
import DayCaption from './DayCaption';
import CaptureSection from './CaptureSection';
import ContentRenderer from './ContentRenderer';
import DayTaskSummary from './DayTaskSummary';
import EditorToggle from './EditorToggle';
import './JournalDayView.css';

const BlockEditor = lazy(() =>
  import('../../../editor/components/BlockEditor').then(m => ({
    default: m.BlockEditor || m.default
  }))
);

/**
 * JournalDayView - Center panel showing the daily note content.
 * Supports view mode (NoteContentRenderer) and edit mode (BlockEditor).
 */
function JournalDayView({ onNavigateToNote }) {
  const { dailyNote, isLoading, error } = useJournalContext();
  const { isEditing, handleSave, handleCancel } = useJournalEditor();

  const handleWikilinkClick = (title) => {
    if (!onNavigateToNote) return;
    api.get('/notes/')
      .then(notes => {
        const found = notes.find(n =>
          n.title?.toLowerCase() === title.toLowerCase()
        );
        if (found) onNavigateToNote(found.id);
      })
      .catch(() => {});
  };

  return (
    <div className="journal-day-view">
      <DayHeader />
      <DayCaption />

      <div className="journal-day-body">
        {/* Capture stream - only for today */}
        <CaptureSection />

        {/* Editor toggle + task summary row */}
        {dailyNote && (
          <div className="journal-day-toolbar">
            <DayTaskSummary />
            <EditorToggle />
          </div>
        )}

        {/* Content area */}
        <div className="journal-day-content">
          {isLoading ? (
            <div className="journal-day-loading">
              <Loader2 size={24} className="ng-animate-spin" />
              <span>Loading daily note...</span>
            </div>
          ) : error ? (
            <div className="journal-day-error">
              <p>Failed to load: {error}</p>
            </div>
          ) : dailyNote && isEditing ? (
            <Suspense fallback={<Loader2 size={20} className="ng-animate-spin" />}>
              <BlockEditor
                note={dailyNote}
                onSave={handleSave}
                onCancel={handleCancel}
              />
            </Suspense>
          ) : dailyNote ? (
            <ContentRenderer onWikilinkClick={handleWikilinkClick} />
          ) : (
            <div className="journal-day-empty">
              <BookOpen size={48} opacity={0.3} />
              <h3>No entry for this day</h3>
              <p>Select today to start writing, or click a day with an entry.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default JournalDayView;
