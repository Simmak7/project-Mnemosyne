import React from 'react';
import { format, parseISO, differenceInCalendarDays } from 'date-fns';
import { CheckSquare, MessageCircle } from 'lucide-react';

/**
 * EntryListItem - Single row in the journal entry list.
 * Shows relative date, content preview, and metadata badges.
 */
function EntryListItem({ entry, isSelected, onSelect }) {
  const dateStr = entry.date || '';
  const { displayDate, relativeLabel } = getDateDisplay(dateStr);

  // Parse metadata from content
  const meta = getMetadata(entry.content || '');
  const caption = getCaption(entry.content || '');
  const preview = caption || getPreview(entry.content || '');

  return (
    <button
      className={`entry-list-item ${isSelected ? 'entry-list-item--selected' : ''}`}
      onClick={() => onSelect(dateStr)}
      aria-current={isSelected ? 'true' : undefined}
    >
      <div className="entry-item-header">
        <span className="entry-date">{displayDate}</span>
        {relativeLabel && (
          <span className="entry-relative">{relativeLabel}</span>
        )}
      </div>
      {preview && (
        <span className={`entry-preview ${caption ? 'entry-preview--caption' : ''}`}>
          {preview}
        </span>
      )}
      {(meta.taskCount > 0 || meta.captureCount > 0) && (
        <div className="entry-meta">
          {meta.taskCount > 0 && (
            <span className="entry-badge entry-badge--tasks" title={`${meta.completedTasks}/${meta.taskCount} tasks`}>
              <CheckSquare size={11} />
              <span>{meta.completedTasks}/{meta.taskCount}</span>
            </span>
          )}
          {meta.captureCount > 0 && (
            <span className="entry-badge entry-badge--captures" title={`${meta.captureCount} captures`}>
              <MessageCircle size={11} />
              <span>{meta.captureCount}</span>
            </span>
          )}
          {meta.mood && (
            <span className="entry-badge entry-badge--mood" title="Mood">
              {meta.mood}
            </span>
          )}
        </div>
      )}
    </button>
  );
}

function getDateDisplay(dateStr) {
  try {
    const d = parseISO(dateStr);
    const today = new Date();
    const diff = differenceInCalendarDays(today, d);

    let relativeLabel = null;
    if (diff === 0) relativeLabel = 'Today';
    else if (diff === 1) relativeLabel = 'Yesterday';
    else if (diff < 7) relativeLabel = `${diff}d ago`;

    const displayDate = format(d, 'EEE, MMM d');
    return { displayDate, relativeLabel };
  } catch {
    return { displayDate: dateStr, relativeLabel: null };
  }
}

function getCaption(content) {
  const match = content.match(/^Caption:\s*(.+)$/m);
  return match ? match[1].trim() : '';
}

function getPreview(content) {
  const lines = content.split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    if (trimmed.startsWith('#')) continue;
    if (trimmed.startsWith('---')) continue;
    if (trimmed.startsWith('Mood:')) continue;
    if (trimmed.startsWith('Caption:')) continue;
    const cleaned = trimmed.replace(/^[-*]\s*(\[[ xX]\]\s*)?/, '').trim();
    if (cleaned && cleaned.length > 2) {
      return cleaned.length > 55 ? cleaned.slice(0, 52) + '...' : cleaned;
    }
  }
  return null;
}

function getMetadata(content) {
  const lines = content.split('\n');
  let taskCount = 0;
  let completedTasks = 0;
  let captureCount = 0;
  let mood = null;

  for (const line of lines) {
    const trimmed = line.trim();
    // Tasks
    if (trimmed.match(/^-\s*\[[ ]\]/)) taskCount++;
    if (trimmed.match(/^-\s*\[[xX]\]/)) { taskCount++; completedTasks++; }
    // Captures (timestamped entries)
    if (trimmed.match(/^-\s*\[\d{2}:\d{2}\]/)) captureCount++;
    // Mood
    const moodMatch = trimmed.match(/^Mood:\s*(.+)$/);
    if (moodMatch) mood = moodMatch[1].trim();
  }

  return { taskCount, completedTasks, captureCount, mood };
}

export default EntryListItem;
