/**
 * TopTagsWidget - Top tags sorted by usage count
 *
 * Each tag is clickable and navigates to Notes filtered by that tag.
 */
import React from 'react';
import { Tag } from 'lucide-react';
import WidgetShell from './WidgetShell';

function TopTagsWidget({ tags, isLoading, onNavigateToTag, onTabChange }) {
  const sorted = Array.isArray(tags)
    ? [...tags].sort((a, b) => (b.note_count || 0) - (a.note_count || 0)).slice(0, 8)
    : [];

  return (
    <WidgetShell
      icon={Tag}
      title="Top Tags"
      action={() => onTabChange('notes')}
      actionLabel="View all"
      isLoading={isLoading}
    >
      {sorted.length === 0 ? (
        <p className="widget-empty">No tags yet</p>
      ) : (
        <div className="widget-tags">
          {sorted.map((tag) => (
            <button
              key={tag.id || tag.name}
              className="widget-tag-pill"
              onClick={() => onNavigateToTag?.(tag.name)}
              title={`View notes tagged #${tag.name}`}
            >
              #{tag.name}
              <span className="widget-tag-count">{tag.note_count || 0}</span>
            </button>
          ))}
        </div>
      )}
    </WidgetShell>
  );
}

export default TopTagsWidget;
