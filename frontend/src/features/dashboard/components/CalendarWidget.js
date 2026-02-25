/**
 * CalendarWidget - Month-view calendar for the dashboard
 *
 * Reuses MiniCalendar from Journal with compact overrides.
 * Clicking a day selects it and shows a brief summary tooltip.
 * "Open Journal" button in the header navigates to Journal.
 */
import React, { useState, useCallback, useMemo } from 'react';
import { Calendar } from 'lucide-react';
import { format } from 'date-fns';
import WidgetShell from './WidgetShell';
import MiniCalendar from '../../journal/components/journal-sidebar/MiniCalendar';
import { useCalendarData } from '../../journal/hooks/useCalendarData';
import './CalendarWidget.css';

function DaySummaryBar({ dateStr, calendarData }) {
  const summary = calendarData.get(dateStr);
  if (!summary) {
    return <p className="calendar-day-info calendar-day-info--empty">No activity</p>;
  }

  const parts = [];
  if (summary.capture_count > 0) parts.push(`${summary.capture_count} capture${summary.capture_count > 1 ? 's' : ''}`);
  if (summary.task_count > 0) parts.push(`${summary.completed_tasks}/${summary.task_count} tasks`);
  if (summary.wikilink_count > 0) parts.push(`${summary.wikilink_count} link${summary.wikilink_count > 1 ? 's' : ''}`);
  if (summary.mood) parts.push(summary.mood);

  if (parts.length === 0 && summary.has_entry) {
    return <p className="calendar-day-info">Entry exists</p>;
  }

  return parts.length > 0
    ? <p className="calendar-day-info">{parts.join(' \u00b7 ')}</p>
    : <p className="calendar-day-info calendar-day-info--empty">No activity</p>;
}

function CalendarWidget({ onTabChange }) {
  const today = new Date();
  const [calendarMonth, setCalendarMonth] = useState(format(today, 'yyyy-MM'));
  const [selectedDate, setSelectedDate] = useState(format(today, 'yyyy-MM-dd'));
  const { calendarData } = useCalendarData(calendarMonth);

  const handleSelectDate = useCallback((dateStr) => {
    setSelectedDate(dateStr);
  }, []);

  const selectedLabel = useMemo(() => {
    try {
      const d = new Date(selectedDate + 'T00:00:00');
      return format(d, 'EEE, MMM d');
    } catch { return selectedDate; }
  }, [selectedDate]);

  return (
    <WidgetShell
      icon={Calendar}
      title="Calendar"
      action={() => onTabChange?.('journal')}
      actionLabel="Open Journal"
    >
      <div className="calendar-widget">
        <MiniCalendar
          calendarMonth={calendarMonth}
          onMonthChange={setCalendarMonth}
          selectedDate={selectedDate}
          onSelectDate={handleSelectDate}
          calendarData={calendarData}
        />
        <div className="calendar-widget-info">
          <span className="calendar-widget-date">{selectedLabel}</span>
          <DaySummaryBar dateStr={selectedDate} calendarData={calendarData} />
        </div>
      </div>
    </WidgetShell>
  );
}

export default CalendarWidget;
