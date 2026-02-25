/**
 * KnowledgeGraphWidget - Graph stats with node type breakdown bars
 */
import React from 'react';
import { Brain } from 'lucide-react';
import WidgetShell from './WidgetShell';

const NODE_TYPE_COLORS = {
  note: '#fbbf24',
  tag: '#34d399',
  image: '#22d3ee',
  entity: '#818cf8',
};

function BreakdownBar({ label, count, total, color }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="widget-bar-row">
      <span className="widget-bar-dot" style={{ backgroundColor: color }} />
      <span className="widget-bar-label">{label}</span>
      <div className="widget-bar-track">
        <div className="widget-bar-fill" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="widget-bar-count">{count}</span>
    </div>
  );
}

function KnowledgeGraphWidget({ graphStats, isLoading, onTabChange }) {
  const nodeCounts = graphStats?.node_counts || {};
  const totalNodes = graphStats?.total_nodes || 0;
  const totalEdges = graphStats?.total_edges || 0;
  const communities = graphStats?.communities || 0;

  return (
    <WidgetShell
      icon={Brain}
      title="Knowledge Graph"
      action={() => onTabChange('graph')}
      actionLabel="View graph"
      isLoading={isLoading}
    >
      <div className="widget-stats-summary">
        <div className="widget-stat">
          <span className="widget-stat-value">{totalNodes.toLocaleString()}</span>
          <span className="widget-stat-label">Nodes</span>
        </div>
        <div className="widget-stat">
          <span className="widget-stat-value">{totalEdges.toLocaleString()}</span>
          <span className="widget-stat-label">Edges</span>
        </div>
        <div className="widget-stat">
          <span className="widget-stat-value">{communities}</span>
          <span className="widget-stat-label">Communities</span>
        </div>
      </div>
      <div className="widget-bars">
        {Object.entries(nodeCounts).map(([type, count]) => (
          <BreakdownBar
            key={type}
            label={type}
            count={count}
            total={totalNodes}
            color={NODE_TYPE_COLORS[type] || '#9ca3af'}
          />
        ))}
        {Object.keys(nodeCounts).length === 0 && (
          <p className="widget-empty">No graph data yet</p>
        )}
      </div>
    </WidgetShell>
  );
}

export default KnowledgeGraphWidget;
