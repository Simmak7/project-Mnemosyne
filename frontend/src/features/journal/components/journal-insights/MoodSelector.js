import React from 'react';
import { useJournalContext } from '../../hooks/JournalContext';

const MOODS = [
  { emoji: '😊', label: 'Great' },
  { emoji: '🙂', label: 'Good' },
  { emoji: '😐', label: 'Okay' },
  { emoji: '😔', label: 'Low' },
  { emoji: '😤', label: 'Frustrated' },
];

/**
 * MoodSelector - 5 emoji buttons, saves as "Mood: emoji" line in note content.
 */
function MoodSelector({ currentMood }) {
  const { dailyNote, updateContent } = useJournalContext();

  const handleMoodSelect = async (emoji) => {
    if (!dailyNote?.content) return;

    let content = dailyNote.content;
    const moodLine = `Mood: ${emoji}`;

    // Replace existing mood line or append
    if (content.match(/^Mood:\s*.+$/m)) {
      content = content.replace(/^Mood:\s*.+$/m, moodLine);
    } else {
      content = content.trimEnd() + '\n\n' + moodLine;
    }

    await updateContent(content);
  };

  return (
    <div className="insight-section">
      <h4 className="insight-section-title">Mood</h4>
      <div className="mood-selector">
        {MOODS.map(mood => (
          <button
            key={mood.emoji}
            className={`mood-btn ${currentMood === mood.emoji ? 'mood-btn--active' : ''}`}
            onClick={() => handleMoodSelect(mood.emoji)}
            title={mood.label}
            aria-label={`Set mood to ${mood.label}`}
          >
            <span className="mood-emoji">{mood.emoji}</span>
          </button>
        ))}
      </div>
      {currentMood && (
        <span className="mood-current">
          Current: {currentMood} {MOODS.find(m => m.emoji === currentMood)?.label || ''}
        </span>
      )}
    </div>
  );
}

export default MoodSelector;
