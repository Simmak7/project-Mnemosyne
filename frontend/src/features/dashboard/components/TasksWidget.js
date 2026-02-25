/**
 * TasksWidget - Shows open journal tasks with inline completion toggle
 */
import React from 'react';
import { CheckSquare } from 'lucide-react';
import WidgetShell from './WidgetShell';
import { useDashboardTasks } from '../hooks/useDashboardTasks';
import './TasksWidget.css';

function TasksWidget({ onTabChange }) {
  const { tasks, allTasks, loading, toggleTask } = useDashboardTasks();
  const completedCount = allTasks.filter(t => t.checked).length;
  const totalCount = allTasks.length;

  return (
    <WidgetShell
      icon={CheckSquare}
      title="Tasks"
      action={() => onTabChange('journal')}
      actionLabel="Open Journal"
      isLoading={loading}
    >
      {totalCount === 0 ? (
        <p className="widget-empty">No tasks in recent daily notes</p>
      ) : (
        <>
          {totalCount > 0 && (
            <div className="tasks-progress-label">
              {completedCount}/{totalCount} completed
            </div>
          )}
          <div className="tasks-list">
            {tasks.slice(0, 6).map((task, i) => (
              <label key={`${task.noteId}-${i}`} className="tasks-item">
                <input
                  type="checkbox"
                  className="tasks-checkbox"
                  checked={task.checked}
                  onChange={() => toggleTask(task)}
                />
                <span className="tasks-text">{task.text}</span>
              </label>
            ))}
            {tasks.length === 0 && totalCount > 0 && (
              <p className="tasks-all-done">All tasks completed!</p>
            )}
          </div>
        </>
      )}
    </WidgetShell>
  );
}

export default TasksWidget;
