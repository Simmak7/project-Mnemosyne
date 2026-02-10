/**
 * Data settings section - export functionality
 */
import React from 'react';
import { Database } from 'lucide-react';

function DataSection() {
  return (
    <div className="settings-section">
      <div className="settings-section-header">
        <Database size={20} />
        <h3>Data</h3>
      </div>
      <div className="settings-item">
        <div className="settings-item-info">
          <label>Export data</label>
          <p className="settings-placeholder">Coming soon...</p>
        </div>
      </div>
    </div>
  );
}

export default DataSection;
