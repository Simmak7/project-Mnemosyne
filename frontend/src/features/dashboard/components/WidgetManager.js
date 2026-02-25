/**
 * WidgetManager - Overlay panel to show/hide and manage widgets
 *
 * Single flat list of all widgets from WIDGET_REGISTRY.
 * Checkbox toggles visibility; reset restores defaults.
 */
import React from 'react';
import { X } from 'lucide-react';
import WIDGET_REGISTRY from '../utils/widgetRegistry';
import './WidgetManager.css';

function WidgetManager({ isWidgetVisible, toggleWidget, resetToDefaults, onClose }) {
  return (
    <>
      <div className="widget-manager-backdrop" onClick={onClose} />
      <div className="widget-manager-panel">
        <div className="widget-manager-header">
          <h2 className="widget-manager-title">Customize Dashboard</h2>
          <button className="widget-manager-close" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <div className="widget-manager-section">
          <h3 className="widget-manager-section-title">Widgets</h3>
          {WIDGET_REGISTRY.map(({ id, title: label, icon: Icon }) => (
            <label key={id} className="widget-manager-item">
              <input
                type="checkbox"
                className="widget-manager-checkbox"
                checked={isWidgetVisible(id)}
                onChange={() => toggleWidget(id)}
              />
              <Icon size={14} className="widget-manager-item-icon" />
              <span className="widget-manager-item-label">{label}</span>
            </label>
          ))}
        </div>

        <div className="widget-manager-footer">
          <button className="widget-manager-btn widget-manager-btn--reset" onClick={resetToDefaults}>
            Reset to Defaults
          </button>
          <button className="widget-manager-btn widget-manager-btn--done" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </>
  );
}

export default WidgetManager;
