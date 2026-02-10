import React from 'react';
import { MessageSquare, CheckSquare, Link2, Type } from 'lucide-react';

/**
 * DayStats - 4 stat cards showing captures, tasks, links, words.
 */
function DayStats({ stats }) {
  const { captures, tasks, wikilinks, wordCount } = stats;

  const completedTasks = tasks.filter(t => t.checked).length;

  const cards = [
    { icon: MessageSquare, label: 'Captures', value: captures.length, color: 'amber' },
    { icon: CheckSquare, label: 'Tasks', value: `${completedTasks}/${tasks.length}`, color: tasks.length > 0 && completedTasks === tasks.length ? 'green' : 'default' },
    { icon: Link2, label: 'Links', value: wikilinks.length, color: 'blue' },
    { icon: Type, label: 'Words', value: wordCount, color: 'default' },
  ];

  return (
    <div className="day-stats">
      {cards.map(card => (
        <div key={card.label} className={`day-stat-card day-stat--${card.color}`}>
          <card.icon size={16} className="day-stat-icon" />
          <div className="day-stat-info">
            <span className="day-stat-value">{card.value}</span>
            <span className="day-stat-label">{card.label}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default DayStats;
