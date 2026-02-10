/**
 * StatsBreakdown - Detailed graph statistics with type breakdown
 *
 * Shows node counts (notes/tags/images) and edge counts by type
 * as labeled horizontal bars with colored indicators.
 */

import React from 'react';
import './StatsBreakdown.css';

// Node type colors matching nodeRendering.js
const NODE_TYPE_COLORS = {
  note: '#fbbf24',
  tag: '#34d399',
  image: '#22d3ee',
  entity: '#818cf8',
};

// Edge type colors matching edgeRendering.js
const EDGE_TYPE_COLORS = {
  wikilink: '#f9fafb',
  tag: '#34d399',
  image: '#22d3ee',
  semantic: '#818cf8',
  mentions: '#a78bfa',
};

function BreakdownBar({ label, count, total, color }) {
  const pct = total > 0 ? (count / total) * 100 : 0;

  return (
    <div className="stats-breakdown__bar-row">
      <span className="stats-breakdown__bar-dot" style={{ backgroundColor: color }} />
      <span className="stats-breakdown__bar-label">{label}</span>
      <div className="stats-breakdown__bar-track">
        <div
          className="stats-breakdown__bar-fill"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="stats-breakdown__bar-count">{count}</span>
    </div>
  );
}

export function StatsBreakdown({ stats }) {
  if (!stats) return null;

  const nodeCounts = stats.node_counts || {};
  const edgeCounts = stats.edge_counts || {};
  const totalNodes = stats.total_nodes || 0;
  const totalEdges = stats.total_edges || 0;

  return (
    <div className="stats-breakdown">
      {/* Summary row */}
      <div className="stats-breakdown__summary">
        <div className="stats-breakdown__stat">
          <span className="stats-breakdown__stat-value">{totalNodes}</span>
          <span className="stats-breakdown__stat-label">Nodes</span>
        </div>
        <div className="stats-breakdown__stat">
          <span className="stats-breakdown__stat-value">{totalEdges}</span>
          <span className="stats-breakdown__stat-label">Edges</span>
        </div>
        <div className="stats-breakdown__stat">
          <span className="stats-breakdown__stat-value">{stats.communities || 0}</span>
          <span className="stats-breakdown__stat-label">Communities</span>
        </div>
      </div>

      {/* Node breakdown */}
      <div className="stats-breakdown__section">
        <div className="stats-breakdown__section-title">Nodes</div>
        {Object.entries(nodeCounts).map(([type, count]) => (
          <BreakdownBar
            key={type}
            label={type}
            count={count}
            total={totalNodes}
            color={NODE_TYPE_COLORS[type] || '#9ca3af'}
          />
        ))}
      </div>

      {/* Edge breakdown */}
      <div className="stats-breakdown__section">
        <div className="stats-breakdown__section-title">Edges</div>
        {Object.entries(edgeCounts).map(([type, count]) => (
          <BreakdownBar
            key={type}
            label={type}
            count={count}
            total={totalEdges}
            color={EDGE_TYPE_COLORS[type] || '#9ca3af'}
          />
        ))}
      </div>
    </div>
  );
}

export default StatsBreakdown;
