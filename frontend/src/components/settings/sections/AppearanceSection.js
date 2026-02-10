/**
 * Appearance settings section - theme, accent color, UI density
 */
import React from 'react';
import { Palette } from 'lucide-react';
import { ACCENT_COLORS, DENSITY_VALUES } from '../constants';

function AppearanceSection({ preferences, prefOptions, onPreferenceUpdate }) {
  const applyPreference = (key, value) => {
    const root = document.documentElement;

    if (key === 'theme') {
      localStorage.setItem('darkMode', JSON.stringify(value === 'dark'));
      root.setAttribute('data-theme', value);
    }

    if (key === 'accent_color') {
      const colors = ACCENT_COLORS[value] || ACCENT_COLORS.blue;
      root.style.setProperty('--accent-color', colors.primary);
      root.style.setProperty('--accent-hover', colors.hover);
      root.style.setProperty('--accent-light', colors.light);
      localStorage.setItem('accentColor', value);
    }

    if (key === 'ui_density') {
      const density = DENSITY_VALUES[value] || DENSITY_VALUES.comfortable;
      root.style.setProperty('--density-spacing', density.spacing);
      root.style.setProperty('--density-padding', density.padding);
      root.style.setProperty('--density-font-size', density.fontSize);
      root.setAttribute('data-density', value);
      localStorage.setItem('uiDensity', value);
    }
  };

  const handleUpdate = async (key, value) => {
    applyPreference(key, value);
    onPreferenceUpdate(key, value);
  };

  if (!preferences || !prefOptions) {
    return (
      <div className="settings-section">
        <div className="settings-section-header">
          <Palette size={20} />
          <h3>Appearance</h3>
        </div>
        <div className="settings-item">
          <div className="settings-item-info">
            <p className="settings-placeholder">Loading preferences...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="settings-section">
      <div className="settings-section-header">
        <Palette size={20} />
        <h3>Appearance</h3>
      </div>
      <div className="settings-appearance-grid">
        <div className="settings-appearance-item">
          <label>Theme</label>
          <select
            value={preferences.theme}
            onChange={(e) => handleUpdate('theme', e.target.value)}
            className="settings-select"
          >
            {prefOptions.themes.map(t => (
              <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
            ))}
          </select>
        </div>
        <div className="settings-appearance-item">
          <label>Accent Color</label>
          <select
            value={preferences.accent_color}
            onChange={(e) => handleUpdate('accent_color', e.target.value)}
            className="settings-select"
          >
            {prefOptions.accent_colors.map(c => (
              <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
            ))}
          </select>
        </div>
        <div className="settings-appearance-item">
          <label>UI Density</label>
          <select
            value={preferences.ui_density}
            onChange={(e) => handleUpdate('ui_density', e.target.value)}
            className="settings-select"
          >
            {prefOptions.ui_density.map(d => (
              <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}

export default AppearanceSection;
