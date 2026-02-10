/**
 * Sessions settings section - active sessions management
 */
import React from 'react';
import { Shield } from 'lucide-react';

function SessionsSection({ sessions, onRevokeSession, onRevokeAllSessions }) {
  if (!sessions?.length) {
    return (
      <div className="settings-section">
        <div className="settings-section-header">
          <Shield size={20} />
          <h3>Active Sessions</h3>
        </div>
        <div className="settings-item">
          <div className="settings-item-info">
            <p className="settings-placeholder">Loading sessions...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="settings-section">
      <div className="settings-section-header">
        <Shield size={20} />
        <h3>Active Sessions</h3>
      </div>
      {sessions.map(session => (
        <div key={session.id} className="settings-item settings-item-action">
          <div className="settings-item-info">
            <label>
              {session.device_info || 'Unknown device'}
              {session.is_current && <span className="current-badge"> (current)</span>}
            </label>
            <p>
              IP: {session.ip_address || 'Unknown'} • Last active: {new Date(session.last_active).toLocaleString()}
            </p>
          </div>
          {!session.is_current && (
            <button
              className="btn-danger btn-small"
              onClick={() => onRevokeSession(session.id)}
            >
              Revoke
            </button>
          )}
        </div>
      ))}
      {sessions.length > 1 && (
        <div className="settings-item">
          <button className="btn-secondary" onClick={onRevokeAllSessions}>
            Revoke All Other Sessions
          </button>
        </div>
      )}
    </div>
  );
}

export default SessionsSection;
