import React from 'react';
import { format, parseISO } from 'date-fns';
import { ChevronLeft, ChevronRight, Sun, Moon, Sunset } from 'lucide-react';
import { useJournalContext } from '../../hooks/JournalContext';
import './DayHeader.css';

/**
 * DayHeader - Shows greeting (today) or date display (past), with day navigation.
 */
function DayHeader() {
  const { selectedDate, selectDate, isToday } = useJournalContext();

  const dateObj = parseISO(selectedDate);
  const hour = new Date().getHours();

  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  const GreetingIcon = hour < 12 ? Sun : hour < 17 ? Sunset : Moon;

  const handlePrevDay = () => {
    const prev = new Date(dateObj);
    prev.setDate(prev.getDate() - 1);
    selectDate(format(prev, 'yyyy-MM-dd'));
  };

  const handleNextDay = () => {
    const next = new Date(dateObj);
    next.setDate(next.getDate() + 1);
    selectDate(format(next, 'yyyy-MM-dd'));
  };

  return (
    <div className="day-header">
      <div className="day-header-nav">
        <button className="day-nav-btn" onClick={handlePrevDay} aria-label="Previous day">
          <ChevronLeft size={18} />
        </button>

        <div className="day-header-center">
          {isToday ? (
            <div className="day-greeting">
              <GreetingIcon size={20} className="greeting-icon" />
              <h2>{greeting}</h2>
            </div>
          ) : (
            <h2 className="day-date-title">{format(dateObj, 'EEEE, MMMM d, yyyy')}</h2>
          )}
          <span className="day-date-sub">
            {isToday ? format(dateObj, 'EEEE, MMMM d') : (
              isYesterday(dateObj) ? 'Yesterday' : format(dateObj, 'MMMM d, yyyy')
            )}
          </span>
        </div>

        <button className="day-nav-btn" onClick={handleNextDay} aria-label="Next day">
          <ChevronRight size={18} />
        </button>
      </div>
    </div>
  );
}

function isYesterday(date) {
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  return date.toDateString() === yesterday.toDateString();
}

export default DayHeader;
