import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import './CalendarLegend.css';

const LEGEND_ITEMS = [
  { color: 'amber', label: 'Entry' },
  { color: 'green', label: 'Tasks Done' },
  { color: 'red', label: 'Pending Tasks' },
  { color: 'blue', label: 'Has Links' },
  { color: 'violet', label: 'Has Mood' },
];

/**
 * CalendarLegend - Compact collapsible legend below the calendar grid.
 */
function CalendarLegend() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="calendar-legend">
      <button
        className="calendar-legend-toggle"
        onClick={() => setIsOpen(prev => !prev)}
        aria-expanded={isOpen}
      >
        <span className="calendar-legend-toggle-label">Legend</span>
        {isOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>

      {isOpen && (
        <div className="calendar-legend-items">
          {LEGEND_ITEMS.map(({ color, label }) => (
            <div key={color} className="calendar-legend-item">
              <span className={`calendar-dot calendar-dot--${color}`} />
              <span className="calendar-legend-label">{label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default CalendarLegend;
