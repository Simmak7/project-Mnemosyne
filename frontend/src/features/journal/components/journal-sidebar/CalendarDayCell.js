import React from 'react';
import { format, isSameDay, isSameMonth, isToday } from '../../utils/calendarHelpers';

/**
 * CalendarDayCell - Single day cell with indicator dots.
 *
 * Dot logic:
 * - Amber: has_entry (a daily note exists)
 * - Red: has pending tasks (task_count > completed_tasks)
 * - Green: all tasks done (task_count > 0 && task_count === completed_tasks)
 * - Blue: has wikilinks (wikilink_count > 0)
 * - Violet: has mood set
 */
function CalendarDayCell({ date, monthDate, selectedDate, daySummary, onSelect }) {
  const dateStr = format(date, 'yyyy-MM-dd');
  const isCurrentMonth = isSameMonth(date, monthDate);
  const isSelected = selectedDate === dateStr;
  const isTodayDate = isToday(date);

  const dots = [];
  if (daySummary) {
    if (daySummary.has_entry) {
      dots.push('amber');
    }
    if (daySummary.task_count > 0) {
      if (daySummary.completed_tasks < daySummary.task_count) {
        dots.push('red');
      } else {
        dots.push('green');
      }
    }
    if (daySummary.capture_count > 0 && !dots.includes('amber')) {
      dots.push('amber');
    }
    if (daySummary.wikilink_count > 0) {
      dots.push('blue');
    }
    if (daySummary.mood) {
      dots.push('violet');
    }
  }

  const classNames = [
    'calendar-day',
    !isCurrentMonth && 'calendar-day--other-month',
    isSelected && 'calendar-day--selected',
    isTodayDate && 'calendar-day--today',
  ].filter(Boolean).join(' ');

  return (
    <button
      className={classNames}
      onClick={() => onSelect(dateStr)}
      aria-label={`${format(date, 'MMMM d, yyyy')}${isTodayDate ? ' (today)' : ''}`}
      aria-pressed={isSelected}
    >
      <span className="calendar-day-number">{date.getDate()}</span>
      {dots.length > 0 && (
        <div className="calendar-day-dots">
          {dots.slice(0, 5).map((color, i) => (
            <span key={i} className={`calendar-dot calendar-dot--${color}`} />
          ))}
        </div>
      )}
    </button>
  );
}

export default CalendarDayCell;
