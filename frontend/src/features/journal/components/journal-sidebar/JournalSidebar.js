import React from 'react';
import { BookOpen, ChevronLeft } from 'lucide-react';
import { useJournalContext } from '../../hooks/JournalContext';
import { useCalendarData } from '../../hooks/useCalendarData';
import MiniCalendar from './MiniCalendar';
import EntryList from './EntryList';
import './JournalSidebar.css';

/**
 * JournalSidebar - Left panel with calendar + recent entries.
 */
function JournalSidebar({ isCollapsed, onCollapse }) {
  const {
    selectedDate,
    selectDate,
    calendarMonth,
    setCalendarMonth,
    navigateToToday,
    entries,
    entriesLoading,
  } = useJournalContext();

  const { calendarData, isLoading: calLoading } = useCalendarData(calendarMonth);

  if (isCollapsed) return null;

  return (
    <div className="journal-sidebar">
      {/* Header */}
      <div className="journal-sidebar-header">
        <div className="journal-sidebar-title">
          <BookOpen size={18} />
          <h3>Journal</h3>
        </div>
        <button
          className="journal-sidebar-collapse"
          onClick={onCollapse}
          title="Collapse sidebar"
        >
          <ChevronLeft size={16} />
        </button>
      </div>

      {/* Today button */}
      <button className="journal-today-btn" onClick={navigateToToday}>
        Go to Today
      </button>

      {/* Mini Calendar */}
      <MiniCalendar
        calendarMonth={calendarMonth}
        onMonthChange={setCalendarMonth}
        selectedDate={selectedDate}
        onSelectDate={selectDate}
        calendarData={calendarData}
      />

      {/* Divider */}
      <div className="journal-sidebar-divider" />

      {/* Entry List */}
      <div className="journal-sidebar-entries">
        <EntryList
          entries={entries}
          selectedDate={selectedDate}
          onSelectDate={selectDate}
          isLoading={entriesLoading}
        />
      </div>
    </div>
  );
}

export default JournalSidebar;
