import React, { useState } from 'react';
import { ListTodo, ChevronDown, ChevronUp, Circle, Calendar } from 'lucide-react';
import { useJournalContext } from '../../hooks/JournalContext';
import './OpenTasksPanel.css';

/**
 * OpenTasksPanel - Shows all uncompleted tasks across all journal days.
 * Grouped by date, most recent first.
 * Clicking a task or its date navigates to that day's note.
 */
function OpenTasksPanel({ openTasks }) {
  const [isExpanded, setIsExpanded] = useState(true);
  const { selectDate, setCalendarMonth } = useJournalContext();

  if (!openTasks || openTasks.length === 0) return null;

  // Group tasks by date
  const grouped = {};
  for (const task of openTasks) {
    const key = task.date || 'Unknown';
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(task);
  }
  const dateKeys = Object.keys(grouped).sort((a, b) => b.localeCompare(a));

  const navigateToDate = (dateStr) => {
    selectDate(dateStr);
    const [y, m] = dateStr.split('-');
    if (y && m) {
      setCalendarMonth(`${y}-${m}`);
    }
  };

  const formatDate = (dateStr) => {
    try {
      const [y, m, d] = dateStr.split('-').map(Number);
      const dt = new Date(y, m - 1, d);
      return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="insight-section open-tasks-panel">
      <button
        className="open-tasks-header"
        onClick={() => setIsExpanded(prev => !prev)}
      >
        <ListTodo size={14} />
        <h4 className="insight-section-title">
          Open Tasks ({openTasks.length})
        </h4>
        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {isExpanded && (
        <div className="open-tasks-body">
          {dateKeys.map(dateStr => (
            <div key={dateStr} className="open-tasks-date-group">
              <button
                className="open-tasks-date-label"
                onClick={() => navigateToDate(dateStr)}
                title={`Go to ${dateStr}`}
              >
                <Calendar size={11} />
                <span>{formatDate(dateStr)}</span>
              </button>
              {grouped[dateStr].map((task, i) => (
                <button
                  key={`${dateStr}-${i}`}
                  className="open-task-item"
                  onClick={() => navigateToDate(dateStr)}
                  title={`Go to ${formatDate(dateStr)}`}
                >
                  <Circle size={12} className="open-task-circle" />
                  <span className="open-task-text">{task.text}</span>
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default OpenTasksPanel;
