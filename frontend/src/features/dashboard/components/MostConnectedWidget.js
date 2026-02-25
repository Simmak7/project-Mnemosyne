/**
 * MostConnectedWidget - Top 5 most-linked notes
 */
import React from 'react';
import { Link2 } from 'lucide-react';
import WidgetShell from './WidgetShell';

function MostConnectedWidget({ mostLinked, isLoading, onNavigateToSearch, onTabChange }) {
  const items = Array.isArray(mostLinked) ? mostLinked.slice(0, 5) : [];

  return (
    <WidgetShell
      icon={Link2}
      title="Most Connected"
      action={() => onTabChange('graph')}
      actionLabel="View graph"
      isLoading={isLoading}
    >
      {items.length === 0 ? (
        <p className="widget-empty">No linked notes yet</p>
      ) : (
        <div className="widget-list">
          {items.map((item) => (
            <button
              key={item.note_id ?? item.id}
              className="widget-list-item"
              onClick={() => onNavigateToSearch(item.title || 'Untitled')}
            >
              <span className="widget-list-title">
                {item.title || 'Untitled'}
              </span>
              <span className="widget-list-badge">
                {item.backlink_count ?? item.link_count ?? 0} links
              </span>
            </button>
          ))}
        </div>
      )}
    </WidgetShell>
  );
}

export default MostConnectedWidget;
