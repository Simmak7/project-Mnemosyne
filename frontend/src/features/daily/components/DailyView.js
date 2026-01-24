import React, { useState, useMemo, useContext } from 'react';
import { Loader2, FileText, AlertCircle } from 'lucide-react';
import DailyHeader from './DailyHeader';
import CaptureStream from './CaptureStream';
import TodayOverview from './TodayOverview';
import NoteContentRenderer from '../../../components/common/NoteContentRenderer';
import { useDailyNote } from '../hooks/useDailyNote';
import { useCapture } from '../hooks/useCapture';
import { WorkspaceContext } from '../../../contexts/WorkspaceContext';
import './DailyView.css';

/**
 * DailyView - Main container for daily workflow
 * Shows greeting, capture stream, and today's note content
 */
function DailyView({ username }) {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const { selectNote, setBucket } = useContext(WorkspaceContext);

  const {
    dailyNote,
    isLoading,
    error,
    appendContent,
    toggleCheckbox,
    isToday,
  } = useDailyNote(selectedDate);

  const { capture, isCapturing } = useCapture(async (type, content) => {
    await appendContent(type, content);
  });

  // Handle edit button click - navigate to the note in workspace
  const handleEditClick = () => {
    if (dailyNote?.id) {
      selectNote(dailyNote.id);
      setBucket('inbox'); // Switch to inbox to show the editor
    }
  };

  // Calculate today's statistics from note content
  const stats = useMemo(() => {
    if (!dailyNote?.content) {
      return { captureCount: 0, linkCount: 0, todoCount: 0 };
    }

    const content = dailyNote.content;

    // Count captures (lines starting with "- [HH:MM]" but not tasks)
    const captureMatches = content.match(/^- \[\d{2}:\d{2}\]/gm);
    const captureCount = captureMatches ? captureMatches.length : 0;

    // Count wikilinks
    const linkMatches = content.match(/\[\[[^\]]+\]\]/g);
    const linkCount = linkMatches ? linkMatches.length : 0;

    // Count todos (checkbox items)
    const todoMatches = content.match(/^- \[[ xX]\]/gm);
    const todoCount = todoMatches ? todoMatches.length : 0;

    return { captureCount, linkCount, todoCount };
  }, [dailyNote?.content]);

  const handleDateChange = (newDate) => {
    setSelectedDate(newDate);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="daily-view daily-view-loading">
        <div className="loading-content">
          <Loader2 size={32} className="ng-animate-spin" />
          <p>Loading daily note...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="daily-view daily-view-error">
        <div className="error-content">
          <AlertCircle size={32} />
          <h2>Failed to load daily note</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  // Empty state (no note for past date)
  if (!dailyNote && !isToday) {
    return (
      <div className="daily-view">
        <DailyHeader
          date={selectedDate}
          onDateChange={handleDateChange}
          username={username}
        />
        <div className="daily-view-empty">
          <FileText size={48} className="empty-icon" />
          <h2>No note for this date</h2>
          <p>Navigate to today to start capturing thoughts.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="daily-view">
      <DailyHeader
        date={selectedDate}
        onDateChange={handleDateChange}
        username={username}
      />

      {/* Only show capture stream for today */}
      {isToday && (
        <div className="daily-capture-section">
          <CaptureStream
            onCapture={capture}
            disabled={isCapturing}
          />
        </div>
      )}

      {/* Today's statistics */}
      {isToday && (
        <TodayOverview
          noteCount={1}
          captureCount={stats.captureCount}
          linkCount={stats.linkCount}
          todoCount={stats.todoCount}
          onEditClick={handleEditClick}
        />
      )}

      {/* Note content */}
      <div className="daily-content ng-scrollbar">
        {dailyNote?.content || dailyNote?.html_content ? (
          <div className="daily-note-content ng-animate-fade-up ng-delay-150">
            <NoteContentRenderer
              content={dailyNote.content}
              htmlContent={dailyNote.html_content}
              onCheckboxToggle={toggleCheckbox}
            />
          </div>
        ) : (
          <div className="daily-content-empty">
            <p className="empty-hint">
              {isToday
                ? "Start capturing your thoughts above..."
                : "This note is empty."}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default DailyView;
