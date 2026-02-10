import React from 'react';
import { Calendar } from 'lucide-react';
import EntryListItem from './EntryListItem';

/**
 * EntryList - Recent journal entries list below the calendar.
 */
function EntryList({ entries, selectedDate, onSelectDate, isLoading }) {
  if (isLoading) {
    return (
      <div className="entry-list">
        <div className="entry-list-header">
          <Calendar size={14} />
          <span>Recent Entries</span>
        </div>
        <div className="entry-list-loading">Loading entries...</div>
      </div>
    );
  }

  if (!entries || entries.length === 0) {
    return (
      <div className="entry-list">
        <div className="entry-list-header">
          <Calendar size={14} />
          <span>Recent Entries</span>
        </div>
        <div className="entry-list-empty">
          No journal entries yet. Select today to start writing.
        </div>
      </div>
    );
  }

  return (
    <div className="entry-list">
      <div className="entry-list-header">
        <Calendar size={14} />
        <span>Recent Entries ({entries.length})</span>
      </div>
      <div className="entry-list-items">
        {entries.map(entry => (
          <EntryListItem
            key={entry.id}
            entry={entry}
            isSelected={selectedDate === entry.date}
            onSelect={onSelectDate}
          />
        ))}
      </div>
    </div>
  );
}

export default EntryList;
