/**
 * Account settings section - username, email, display name
 */
import React, { useState } from 'react';
import { User, Edit3, Check } from 'lucide-react';
import { API_URL } from '../../../utils/api';

function AccountSection({ profile, username, userEmail, onEmailChangeClick, onProfileUpdate }) {
  const [editingDisplayName, setEditingDisplayName] = useState(false);
  const [displayNameInput, setDisplayNameInput] = useState(profile?.display_name || '');

  const updateDisplayName = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ display_name: displayNameInput || null })
      });
      if (response.ok) {
        const data = await response.json();
        onProfileUpdate(data);
        setEditingDisplayName(false);
        if (data.display_name) {
          localStorage.setItem('displayName', data.display_name);
        } else {
          localStorage.removeItem('displayName');
        }
      } else {
        const data = await response.json();
        alert(data.error || data.detail || 'Failed to update display name');
      }
    } catch (error) {
      console.error('Error updating display name:', error);
      alert('Network error. Please try again.');
    }
  };

  const startEditing = () => {
    setDisplayNameInput(profile?.display_name || '');
    setEditingDisplayName(true);
  };

  const cancelEditing = () => {
    setDisplayNameInput(profile?.display_name || '');
    setEditingDisplayName(false);
  };

  return (
    <div className="settings-section">
      <div className="settings-section-header">
        <User size={20} />
        <h3>Account</h3>
      </div>
      <div className="settings-item">
        <div className="settings-item-info">
          <label>Username</label>
          <p>{profile?.username || username}</p>
        </div>
        <span className="settings-readonly-hint">Cannot be changed</span>
      </div>
      <div className="settings-item settings-item-action">
        <div className="settings-item-info">
          <label>Email</label>
          <p>{profile?.email || userEmail || 'Not set'}</p>
        </div>
        <button className="btn-secondary btn-small" onClick={onEmailChangeClick}>
          <Edit3 size={14} /> Change
        </button>
      </div>
      <div className="settings-item settings-item-action">
        <div className="settings-item-info">
          <label>Display Name</label>
          {editingDisplayName ? (
            <div className="inline-edit">
              <input
                type="text"
                value={displayNameInput}
                onChange={e => setDisplayNameInput(e.target.value)}
                placeholder="Enter display name"
                maxLength={100}
                autoFocus
              />
              <div className="inline-edit-actions">
                <button className="btn-small btn-primary" onClick={updateDisplayName}>
                  <Check size={14} /> Save
                </button>
                <button className="btn-small btn-secondary" onClick={cancelEditing}>
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <p>{profile?.display_name || 'Not set'}</p>
          )}
        </div>
        {!editingDisplayName && (
          <button className="btn-secondary btn-small" onClick={startEditing}>
            <Edit3 size={14} /> Edit
          </button>
        )}
      </div>
    </div>
  );
}

export default AccountSection;
