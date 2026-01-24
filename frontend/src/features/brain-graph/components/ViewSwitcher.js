/**
 * ViewSwitcher - Tab navigation between graph views
 *
 * Provides view tabs (Explore, Map, Media, PathFinder) and
 * layout controls (zoom, fit, pause).
 */

import React from 'react';
import { ZoomIn, ZoomOut, Maximize2, Pause, Play, RotateCcw } from 'lucide-react';
import './ViewSwitcher.css';

export function ViewSwitcher({
  views,
  currentView,
  onViewChange,
  layout,
}) {
  return (
    <div className="view-switcher">
      {/* View Tabs */}
      <div className="view-switcher__tabs">
        {views.map((view) => {
          const Icon = view.icon;
          const isActive = currentView === view.id;

          return (
            <button
              key={view.id}
              className={`view-switcher__tab ${isActive ? 'is-active' : ''}`}
              onClick={() => onViewChange(view.id)}
              title={`${view.label} (${views.indexOf(view) + 1})`}
            >
              <Icon className="view-switcher__tab-icon" size={16} />
              <span className="view-switcher__tab-label">{view.label}</span>
            </button>
          );
        })}
      </div>

      {/* Layout Controls */}
      <div className="view-switcher__controls">
        {/* Zoom Controls */}
        <div className="view-switcher__control-group">
          <button
            className="view-switcher__control"
            onClick={layout.zoomOut}
            title="Zoom Out (-)"
          >
            <ZoomOut size={16} />
          </button>

          <span className="view-switcher__zoom-level">
            {Math.round(layout.zoom * 100)}%
          </span>

          <button
            className="view-switcher__control"
            onClick={layout.zoomIn}
            title="Zoom In (+)"
          >
            <ZoomIn size={16} />
          </button>
        </div>

        {/* Fit & Reset */}
        <div className="view-switcher__control-group">
          <button
            className="view-switcher__control"
            onClick={() => layout.fitToView()}
            title="Fit to View"
          >
            <Maximize2 size={16} />
          </button>

          <button
            className="view-switcher__control"
            onClick={layout.resetZoom}
            title="Reset View (0)"
          >
            <RotateCcw size={16} />
          </button>
        </div>

        {/* Simulation Control */}
        <div className="view-switcher__control-group">
          <button
            className={`view-switcher__control ${layout.isPaused ? 'is-paused' : ''}`}
            onClick={layout.togglePause}
            title={layout.isPaused ? 'Resume (Space)' : 'Pause (Space)'}
          >
            {layout.isPaused ? <Play size={16} /> : <Pause size={16} />}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ViewSwitcher;
