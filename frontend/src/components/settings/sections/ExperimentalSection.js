/**
 * Experimental settings section - feature flags
 */
import React from 'react';
import { FlaskConical } from 'lucide-react';
import { FEATURE_FLAGS } from '../constants';

function ExperimentalSection({ featureFlags, onToggleFlag }) {
  return (
    <div className="settings-section">
      <div className="settings-section-header">
        <FlaskConical size={20} />
        <h3>Experimental Features</h3>
      </div>
      <p className="settings-section-description">
        Try new features before they become default. Changes apply after page refresh.
      </p>
      {FEATURE_FLAGS.map(flag => (
        <div key={flag.key} className="settings-item settings-item-toggle">
          <div className="settings-item-info">
            <label>{flag.label}</label>
            <p>{flag.description}</p>
          </div>
          <button
            className={`toggle-switch ${featureFlags[flag.key] ? 'active' : ''}`}
            onClick={() => onToggleFlag(flag.key)}
            role="switch"
            aria-checked={featureFlags[flag.key]}
            aria-label={`Toggle ${flag.label}`}
          >
            <span className="toggle-slider" />
          </button>
        </div>
      ))}
    </div>
  );
}

export default ExperimentalSection;
