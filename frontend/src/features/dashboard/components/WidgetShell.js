/**
 * WidgetShell - Reusable widget container with title and loading state
 */
import React from 'react';
import GlassPanel from '../../../components/layout/GlassPanel';

function WidgetShell({ icon: Icon, title, action, actionLabel, isLoading, children }) {
  return (
    <GlassPanel variant="default" padding="md" className="dashboard-widget">
      <div className="widget-header">
        <div className="widget-title-row">
          {Icon && <Icon size={16} className="widget-icon" />}
          <span className="widget-title">{title}</span>
        </div>
        {action && (
          <button className="widget-action" onClick={action}>
            {actionLabel || 'View all'}
          </button>
        )}
      </div>
      <div className="widget-body">
        {isLoading ? (
          <div className="widget-skeleton">
            <div className="widget-skeleton-line ng-shimmer" />
            <div className="widget-skeleton-line ng-shimmer" style={{ width: '75%' }} />
            <div className="widget-skeleton-line ng-shimmer" style={{ width: '60%' }} />
          </div>
        ) : children}
      </div>
    </GlassPanel>
  );
}

export default WidgetShell;
