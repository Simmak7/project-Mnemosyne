/**
 * Notifications settings section - placeholder for future implementation
 */
import React from 'react';
import { Bell } from 'lucide-react';

function NotificationsSection() {
  return (
    <div className="settings-section">
      <div className="settings-section-header">
        <Bell size={20} />
        <h3>Notifications</h3>
      </div>
      <div className="settings-item">
        <div className="settings-item-info">
          <label>Email Notifications</label>
          <p>Security alerts, weekly digests, and product updates will be configurable here.</p>
        </div>
        <span className="settings-coming-soon-badge">Coming Soon</span>
      </div>
    </div>
  );
}

export default NotificationsSection;
