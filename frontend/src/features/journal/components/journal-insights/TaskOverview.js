import React from 'react';
import { Circle, CheckCircle2 } from 'lucide-react';
import { useJournalContext } from '../../hooks/JournalContext';

/**
 * TaskOverview - Lists pending and completed tasks with clickable checkboxes.
 */
function TaskOverview({ tasks }) {
  const { toggleCheckbox } = useJournalContext();

  const pending = tasks.filter(t => !t.checked);
  const completed = tasks.filter(t => t.checked);

  if (tasks.length === 0) {
    return (
      <div className="insight-section">
        <h4 className="insight-section-title">Tasks</h4>
        <p className="insight-empty">No tasks today. Use /todo to add one.</p>
      </div>
    );
  }

  return (
    <div className="insight-section">
      <h4 className="insight-section-title">
        Tasks ({completed.length}/{tasks.length})
      </h4>

      {pending.length > 0 && (
        <div className="task-group">
          {pending.map((task, i) => (
            <button
              key={`p-${i}`}
              className="task-item task-item--pending"
              onClick={() => toggleCheckbox(task.lineText, true)}
            >
              <Circle size={16} className="task-icon" />
              <span>{task.text}</span>
            </button>
          ))}
        </div>
      )}

      {completed.length > 0 && (
        <div className="task-group task-group--done">
          {completed.map((task, i) => (
            <button
              key={`c-${i}`}
              className="task-item task-item--completed"
              onClick={() => toggleCheckbox(task.lineText, false)}
            >
              <CheckCircle2 size={16} className="task-icon" />
              <span>{task.text}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default TaskOverview;
