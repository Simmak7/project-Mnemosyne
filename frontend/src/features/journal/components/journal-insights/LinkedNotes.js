import React from 'react';
import { FileText } from 'lucide-react';
import { api } from '../../../../utils/api';

/**
 * LinkedNotes - Shows extracted [[wikilinks]] as clickable pills.
 */
function LinkedNotes({ wikilinks, onNavigateToNote }) {
  if (!wikilinks || wikilinks.length === 0) {
    return null;
  }

  const handleClick = async (title) => {
    if (!onNavigateToNote) return;
    try {
      const notes = await api.get('/notes/?limit=5000');
      const found = notes.find(n =>
        n.title?.toLowerCase() === title.toLowerCase()
      );
      if (found) onNavigateToNote(found.id);
    } catch {
      // Silently fail
    }
  };

  return (
    <div className="insight-section">
      <h4 className="insight-section-title">Linked Notes</h4>
      <div className="linked-notes-list">
        {wikilinks.map(link => (
          <button
            key={link.title}
            className="linked-note-pill"
            onClick={() => handleClick(link.title)}
            title={`Navigate to ${link.title}`}
          >
            <FileText size={12} />
            <span>{link.alias || link.title}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default LinkedNotes;
