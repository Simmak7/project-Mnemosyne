/**
 * GraphTooltip - Hover tooltip for graph nodes
 *
 * Extracted from GraphCanvas for file size and separation of concerns.
 * Receives pre-computed screen coordinates from parent.
 * Shows rich metadata: community, tags, image dimensions, depth.
 */

import React from 'react';

/**
 * Format relative time from ISO date string
 */
function formatRelativeTime(dateStr) {
  if (!dateStr) return null;
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return `${Math.floor(days / 30)}mo ago`;
}

export function GraphTooltip({ tooltip }) {
  if (!tooltip) return null;

  const relTime = formatRelativeTime(tooltip.modified);

  return (
    <div
      className="graph-canvas__tooltip"
      style={{
        left: `${tooltip.x + 20}px`,
        top: `${tooltip.y - 60}px`,
      }}
    >
      <div className="graph-canvas__tooltip-title">{tooltip.title}</div>
      <div className="graph-canvas__tooltip-meta">
        <span className="graph-canvas__tooltip-type">{tooltip.type}</span>
        {tooltip.connections > 0 && (
          <span className="graph-canvas__tooltip-connections">
            {tooltip.connections} connections
          </span>
        )}
      </div>

      {/* Extended metadata rows */}
      <div className="graph-canvas__tooltip-details">
        {tooltip.community && (
          <div className="graph-canvas__tooltip-row">
            <span
              className="graph-canvas__tooltip-dot"
              style={{ backgroundColor: tooltip.community }}
            />
            <span>Community</span>
          </div>
        )}
        {tooltip.tagCount != null && (
          <div className="graph-canvas__tooltip-row">
            Used in {tooltip.tagCount} notes
          </div>
        )}
        {tooltip.imageSize && (
          <div className="graph-canvas__tooltip-row">
            {tooltip.imageSize}
          </div>
        )}
        {relTime && (
          <div className="graph-canvas__tooltip-row">
            Modified {relTime}
          </div>
        )}
        {tooltip.depth != null && tooltip.depth < 99 && tooltip.depth > 0 && (
          <div className="graph-canvas__tooltip-row">
            Depth {tooltip.depth}
          </div>
        )}
      </div>
    </div>
  );
}

export default GraphTooltip;
