import React from 'react';
import { format, addDays, subDays, isToday as checkIsToday } from 'date-fns';
import { ChevronLeft, ChevronRight, Calendar, Sun, Sunset, Moon } from 'lucide-react';
import './DailyHeader.css';

/**
 * DailyHeader - Shows personalized greeting and date navigation
 */
function DailyHeader({ date, onDateChange, username }) {
  const hour = new Date().getHours();

  // Get greeting based on time of day
  const getGreeting = () => {
    if (hour < 12) return { text: 'Good morning', icon: Sun };
    if (hour < 17) return { text: 'Good afternoon', icon: Sunset };
    return { text: 'Good evening', icon: Moon };
  };

  const greeting = getGreeting();
  const GreetingIcon = greeting.icon;
  const isToday = checkIsToday(date);
  const formattedDate = format(date, 'EEEE, MMMM d, yyyy');

  const handlePrevDay = () => {
    onDateChange(subDays(date, 1));
  };

  const handleNextDay = () => {
    onDateChange(addDays(date, 1));
  };

  const handleToday = () => {
    onDateChange(new Date());
  };

  return (
    <header className="daily-header ng-animate-fade-up">
      {/* Greeting */}
      <div className="daily-greeting">
        <GreetingIcon className="greeting-icon" size={24} />
        <div className="greeting-text">
          <h1>
            {greeting.text}, <span className="username">{username || 'there'}</span>
          </h1>
          <p className="greeting-subtitle">
            {isToday ? "What's on your mind today?" : 'Reviewing past notes'}
          </p>
        </div>
      </div>

      {/* Date Navigation */}
      <div className="daily-date-nav">
        <button
          className="date-nav-btn ng-glass-interactive"
          onClick={handlePrevDay}
          aria-label="Previous day"
        >
          <ChevronLeft size={18} />
        </button>

        <button
          className="date-display ng-glass-interactive"
          onClick={handleToday}
          aria-label={isToday ? 'Today' : 'Go to today'}
        >
          <Calendar size={16} />
          <span className="date-text">{formattedDate}</span>
          {isToday && <span className="today-badge">Today</span>}
        </button>

        <button
          className="date-nav-btn ng-glass-interactive"
          onClick={handleNextDay}
          disabled={isToday}
          aria-label="Next day"
        >
          <ChevronRight size={18} />
        </button>
      </div>
    </header>
  );
}

export default DailyHeader;
