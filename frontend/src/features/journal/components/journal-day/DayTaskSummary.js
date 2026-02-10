import React, { useMemo } from 'react';
import { CheckSquare } from 'lucide-react';
import { parseTasks } from '../../utils/contentParsers';
import { useJournalContext } from '../../hooks/JournalContext';

/**
 * DayTaskSummary - Progress bar showing task completion.
 */
function DayTaskSummary() {
  const { dailyNote } = useJournalContext();

  const tasks = useMemo(
    () => parseTasks(dailyNote?.content),
    [dailyNote?.content]
  );

  if (tasks.length === 0) return null;

  const completed = tasks.filter(t => t.checked).length;
  const total = tasks.length;
  const pct = Math.round((completed / total) * 100);

  return (
    <div className="day-task-summary">
      <div className="day-task-label">
        <CheckSquare size={14} />
        <span>{completed}/{total} tasks complete</span>
      </div>
      <div className="day-task-bar">
        <div
          className="day-task-bar-fill"
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
}

export default DayTaskSummary;
