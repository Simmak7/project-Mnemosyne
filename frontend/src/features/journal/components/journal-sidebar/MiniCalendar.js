import React, { useMemo } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { getMonthGrid, parseCalendarMonth, navigateMonth, format } from '../../utils/calendarHelpers';
import CalendarDayCell from './CalendarDayCell';
import CalendarLegend from './CalendarLegend';
import './MiniCalendar.css';

const DAY_HEADERS = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

/**
 * MiniCalendar - Month-view calendar grid with navigation.
 */
function MiniCalendar({ calendarMonth, onMonthChange, selectedDate, onSelectDate, calendarData }) {
  const { year, month } = parseCalendarMonth(calendarMonth);
  const monthDate = new Date(year, month - 1);
  const monthLabel = format(monthDate, 'MMMM yyyy');

  const gridDays = useMemo(
    () => getMonthGrid(year, month),
    [year, month]
  );

  const handlePrev = () => onMonthChange(navigateMonth(calendarMonth, -1));
  const handleNext = () => onMonthChange(navigateMonth(calendarMonth, 1));

  const handleTodayClick = () => {
    const today = new Date();
    onMonthChange(format(today, 'yyyy-MM'));
    onSelectDate(format(today, 'yyyy-MM-dd'));
  };

  return (
    <div className="mini-calendar">
      {/* Month navigation header */}
      <div className="mini-calendar-header">
        <button
          className="mini-calendar-nav"
          onClick={handlePrev}
          aria-label="Previous month"
        >
          <ChevronLeft size={16} />
        </button>

        <button
          className="mini-calendar-title"
          onClick={handleTodayClick}
          title="Go to today"
        >
          {monthLabel}
        </button>

        <button
          className="mini-calendar-nav"
          onClick={handleNext}
          aria-label="Next month"
        >
          <ChevronRight size={16} />
        </button>
      </div>

      {/* Day-of-week headers */}
      <div className="mini-calendar-grid">
        {DAY_HEADERS.map((d, i) => (
          <div key={i} className="calendar-weekday">{d}</div>
        ))}

        {/* Day cells */}
        {gridDays.map((date, i) => {
          const dateStr = format(date, 'yyyy-MM-dd');
          const daySummary = calendarData.get(dateStr) || null;
          return (
            <CalendarDayCell
              key={i}
              date={date}
              monthDate={monthDate}
              selectedDate={selectedDate}
              daySummary={daySummary}
              onSelect={onSelectDate}
            />
          );
        })}
      </div>

      <CalendarLegend />
    </div>
  );
}

export default MiniCalendar;
