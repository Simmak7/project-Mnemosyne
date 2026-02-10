import React from 'react';
import { BarChart3 } from 'lucide-react';
import { useJournalContext } from '../../hooks/JournalContext';
import { useDayStats } from '../../hooks/useDayStats';
import { useOpenTasks } from '../../hooks/useOpenTasks';
import DayStats from './DayStats';
import TaskOverview from './TaskOverview';
import LinkedNotes from './LinkedNotes';
import MoodSelector from './MoodSelector';
import OpenTasksPanel from './OpenTasksPanel';
import './JournalInsights.css';

/**
 * JournalInsights - Right panel with stats, tasks, links, mood, and open tasks.
 */
function JournalInsights({ onNavigateToNote }) {
  const { dailyNote, entries } = useJournalContext();
  const stats = useDayStats(dailyNote?.content);
  const { openTasks } = useOpenTasks(entries);

  if (!dailyNote) {
    return (
      <div className="journal-insights">
        <div className="insights-header">
          <BarChart3 size={18} />
          <h3>Insights</h3>
        </div>
        <div className="insights-body">
          <div className="insights-empty">
            <p>Select a day with an entry to see insights.</p>
          </div>
          <OpenTasksPanel openTasks={openTasks} />
        </div>
      </div>
    );
  }

  return (
    <div className="journal-insights">
      <div className="insights-header">
        <BarChart3 size={18} />
        <h3>Insights</h3>
      </div>

      <div className="insights-body">
        <DayStats stats={stats} />
        <TaskOverview tasks={stats.tasks} />
        <LinkedNotes
          wikilinks={stats.wikilinks}
          onNavigateToNote={onNavigateToNote}
        />
        <MoodSelector currentMood={stats.mood} />
        <OpenTasksPanel openTasks={openTasks} />
      </div>
    </div>
  );
}

export default JournalInsights;
