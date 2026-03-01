import React from 'react';
import './MobilePanelTabs.css';

/**
 * MobilePanelTabs - Horizontal tab bar for mobile panel switching.
 * Hidden on desktop via CSS.
 *
 * @param {Array} panels - [{id, label, icon: LucideComponent}]
 * @param {string} activePanel - Currently active panel id
 * @param {function} onPanelChange - Callback with panel id
 */
function MobilePanelTabs({ panels, activePanel, onPanelChange }) {
  return (
    <div className="mobile-panel-tabs" role="tablist">
      {panels.map((panel) => {
        const Icon = panel.icon;
        const isActive = activePanel === panel.id;
        return (
          <button
            key={panel.id}
            role="tab"
            aria-selected={isActive}
            className={`mobile-panel-tab ${isActive ? 'active' : ''}`}
            onClick={() => onPanelChange(panel.id)}
          >
            {Icon && <Icon size={16} />}
            <span>{panel.label}</span>
          </button>
        );
      })}
    </div>
  );
}

export default MobilePanelTabs;
