/**
 * Security settings section - password, 2FA
 */
import React from 'react';
import { Lock } from 'lucide-react';
import { api } from '../../../utils/api';

function SecuritySection({
  twoFactorStatus,
  onChangePasswordClick,
  onTwoFactorSetupClick,
  onDisable2FA
}) {
  const handleDisable2FA = async () => {
    const code = prompt('Enter your 2FA code to disable:');
    const password = prompt('Enter your password to confirm:');

    if (!code || !password) return;

    try {
      const response = await api.fetch('/2fa/disable', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, password })
      });

      if (response.ok) {
        alert('Two-factor authentication disabled');
        onDisable2FA();
      } else {
        const data = await response.json();
        alert(data.error || data.detail || 'Failed to disable 2FA');
      }
    } catch (error) {
      alert('Network error');
    }
  };

  return (
    <div className="settings-section">
      <div className="settings-section-header">
        <Lock size={20} />
        <h3>Privacy & Security</h3>
      </div>
      <div className="settings-item settings-item-action">
        <div className="settings-item-info">
          <label>Password</label>
          <p>Change your account password</p>
        </div>
        <button className="btn-secondary" onClick={onChangePasswordClick}>
          Change Password
        </button>
      </div>
      <div className="settings-item settings-item-action">
        <div className="settings-item-info">
          <label>Two-Factor Authentication</label>
          <p>
            {twoFactorStatus.is_enabled
              ? 'Enabled - Your account is protected with 2FA'
              : 'Add an extra layer of security to your account'
            }
          </p>
        </div>
        {twoFactorStatus.is_enabled ? (
          <button className="btn-danger" onClick={handleDisable2FA}>
            Disable 2FA
          </button>
        ) : (
          <button className="btn-primary" onClick={onTwoFactorSetupClick}>
            Enable 2FA
          </button>
        )}
      </div>
    </div>
  );
}

export default SecuritySection;
