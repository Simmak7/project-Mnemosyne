import React from 'react';
import { FileText, Image, Zap, Link2, CheckSquare, Edit3 } from 'lucide-react';
import './TodayOverview.css';

/**
 * TodayOverview - Summary statistics for today's activity
 */
function TodayOverview({
  noteCount = 0,
  captureCount = 0,
  imageCount = 0,
  linkCount = 0,
  todoCount = 0,
  onEditClick
}) {
  const stats = [
    {
      icon: FileText,
      label: 'Notes',
      value: noteCount,
      color: 'note',
    },
    {
      icon: Zap,
      label: 'Captures',
      value: captureCount,
      color: 'ai',
    },
    {
      icon: Link2,
      label: 'Links',
      value: linkCount,
      color: 'link',
    },
    {
      icon: CheckSquare,
      label: 'Todos',
      value: todoCount,
      color: 'todo',
    },
  ];

  // Only show if there's at least one stat
  const hasStats = noteCount > 0 || captureCount > 0 || linkCount > 0 || todoCount > 0;

  if (!hasStats) {
    return null;
  }

  return (
    <div className="today-overview ng-animate-fade-up ng-delay-100">
      <div className="overview-header">
        <h3 className="overview-title">Today's Activity</h3>
        {onEditClick && (
          <button
            className="overview-edit-btn"
            onClick={onEditClick}
            title="Edit daily note"
            aria-label="Edit daily note"
          >
            <Edit3 size={16} />
            <span>Edit</span>
          </button>
        )}
      </div>
      <div className="overview-stats">
        {stats.map((stat) => {
          if (stat.value === 0) return null;
          const Icon = stat.icon;
          return (
            <div key={stat.label} className={`stat-item stat-${stat.color}`}>
              <Icon size={16} className="stat-icon" />
              <span className="stat-value">{stat.value}</span>
              <span className="stat-label">{stat.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default TodayOverview;
