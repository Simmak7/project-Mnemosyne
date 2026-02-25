/**
 * DashboardHeader - Greeting, date, health pulse, and customize toolbar
 */
import React from 'react';
import { Settings, LayoutGrid, Check } from 'lucide-react';
import { useGreeting } from '../hooks/useGreeting';
import './DashboardHeader.css';

function DashboardHeader({ health, isCustomizing, onEnterCustomize, onExitCustomize, onManageWidgets }) {
  const greeting = useGreeting();
  const displayName = localStorage.getItem('displayName') || localStorage.getItem('username') || 'User';

  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const healthOk = health?.status === 'healthy' || health?.status === 'ok';
  const healthDegraded = health?.status === 'degraded';
  const pulseClass = healthOk ? 'pulse-green' : healthDegraded ? 'pulse-yellow' : 'pulse-red';
  const pulseLabel = healthOk ? 'All systems OK' : healthDegraded ? 'Degraded' : 'Offline';

  return (
    <div className="dashboard-header">
      <div className="dashboard-header__left">
        <h1 className="dashboard-header__greeting">
          {greeting}, {displayName}
        </h1>
        <p className="dashboard-header__subtitle">
          {isCustomizing ? 'Drag widgets to rearrange, resize from corners' : 'Your knowledge base at a glance'}
        </p>
      </div>
      <div className="dashboard-header__right">
        {isCustomizing ? (
          <div className="dashboard-customize-toolbar">
            <button className="dashboard-toolbar-btn dashboard-toolbar-btn--secondary" onClick={onManageWidgets}>
              <LayoutGrid size={14} />
              <span>Manage Widgets</span>
            </button>
            <button className="dashboard-toolbar-btn dashboard-toolbar-btn--primary" onClick={onExitCustomize}>
              <Check size={14} />
              <span>Done</span>
            </button>
          </div>
        ) : (
          <>
            <span className="dashboard-header__date">{dateStr}</span>
            <span className={`dashboard-header__pulse ${pulseClass}`} title={pulseLabel}>
              <span className="pulse-dot" />
              <span className="pulse-label">{pulseLabel}</span>
            </span>
            <button
              className="dashboard-customize-btn"
              onClick={onEnterCustomize}
              title="Customize dashboard"
              aria-label="Customize dashboard"
            >
              <Settings size={16} />
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default DashboardHeader;
