/**
 * RecentNotesWidget - Last 5 recently updated notes
 */
import React from 'react';
import { FileText } from 'lucide-react';
import WidgetShell from './WidgetShell';

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function RecentNotesWidget({ recentNotes, isLoading, onNavigateToNote, onTabChange }) {
  const raw = recentNotes?.notes ?? recentNotes;
  const notes = Array.isArray(raw) ? raw.slice(0, 5) : [];

  return (
    <WidgetShell
      icon={FileText}
      title="Recent Notes"
      action={() => onTabChange('notes')}
      actionLabel="View all"
      isLoading={isLoading}
    >
      {notes.length === 0 ? (
        <p className="widget-empty">No recent notes</p>
      ) : (
        <div className="widget-list">
          {notes.map((note) => (
            <button
              key={note.id}
              className="widget-list-item"
              onClick={() => onNavigateToNote(note.id)}
            >
              <span className="widget-list-title">
                {note.title || 'Untitled'}
              </span>
              <span className="widget-list-meta">
                {timeAgo(note.updated_at || note.created_at)}
              </span>
            </button>
          ))}
        </div>
      )}
    </WidgetShell>
  );
}

export default RecentNotesWidget;
