import React, { useState, useEffect } from 'react';
import {
  X, User, Bell, Palette, Lock, Database, FlaskConical,
  Eye, EyeOff, Shield, Key, AlertTriangle, Check, Copy, Mail, Edit3
} from 'lucide-react';
import './Settings.css';

// Feature flags with defaults
const FEATURE_FLAGS = [
  { key: 'ENABLE_NEW_BRAIN_GRAPH', label: 'Neural Glass Brain Graph', description: 'New graph visualization with exploration views', default: false },
  { key: 'ENABLE_NEW_GALLERY', label: 'Immich-style Gallery', description: 'Grid layout with blurhash placeholders', default: true },
  { key: 'ENABLE_NEW_NOTES', label: '3-Pane Notes Layout', description: 'Collections, list, and editor panels', default: true },
  { key: 'ENABLE_NEW_AI_CHAT', label: 'AI Chat Layout', description: 'Enhanced chat with history panel', default: true },
  { key: 'ENABLE_NEW_UPLOAD', label: 'Neural Studio Upload', description: '2-pane upload experience', default: true },
  { key: 'ENABLE_WORKSPACE', label: 'Workspace Mode', description: 'Full workspace layout', default: true },
];

// Password strength indicator component
function PasswordStrengthIndicator({ password }) {
  const [strength, setStrength] = useState({ score: 0, strength: 'weak', feedback: [] });

  useEffect(() => {
    if (!password) {
      setStrength({ score: 0, strength: 'weak', feedback: [] });
      return;
    }

    // Check password strength via API
    const checkStrength = async () => {
      try {
        const response = await fetch('http://localhost:8000/check-password-strength', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ password })
        });
        if (response.ok) {
          const data = await response.json();
          setStrength(data);
        }
      } catch (error) {
        console.error('Error checking password strength:', error);
      }
    };

    const debounce = setTimeout(checkStrength, 300);
    return () => clearTimeout(debounce);
  }, [password]);

  const getStrengthColor = () => {
    switch (strength.strength) {
      case 'weak': return '#ef4444';
      case 'fair': return '#f59e0b';
      case 'good': return '#10b981';
      case 'strong': return '#3b82f6';
      case 'excellent': return '#8b5cf6';
      default: return '#6b7280';
    }
  };

  return (
    <div className="password-strength">
      <div className="password-strength-bar">
        <div
          className="password-strength-fill"
          style={{
            width: `${strength.score}%`,
            backgroundColor: getStrengthColor()
          }}
        />
      </div>
      <span className="password-strength-label" style={{ color: getStrengthColor() }}>
        {strength.strength.charAt(0).toUpperCase() + strength.strength.slice(1)}
      </span>
    </div>
  );
}

// Change Password Modal
function ChangePasswordModal({ isOpen, onClose }) {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    if (newPassword !== confirmPassword) {
      setMessage({ type: 'error', text: 'New passwords do not match' });
      setLoading(false);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          confirm_password: confirmPassword
        })
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Password changed successfully!' });
        setTimeout(() => {
          onClose();
          setCurrentPassword('');
          setNewPassword('');
          setConfirmPassword('');
        }, 1500);
      } else {
        const data = await response.json();
        setMessage({ type: 'error', text: data.error || data.detail || 'Failed to change password' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3><Key size={20} /> Change Password</h3>
          <button className="modal-close" onClick={onClose}><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Current Password</label>
            <div className="password-input-wrapper">
              <input
                type={showCurrent ? 'text' : 'password'}
                value={currentPassword}
                onChange={e => setCurrentPassword(e.target.value)}
                required
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowCurrent(!showCurrent)}
              >
                {showCurrent ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
          <div className="form-group">
            <label>New Password</label>
            <div className="password-input-wrapper">
              <input
                type={showNew ? 'text' : 'password'}
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                required
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowNew(!showNew)}
              >
                {showNew ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            <PasswordStrengthIndicator password={newPassword} />
          </div>
          <div className="form-group">
            <label>Confirm New Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              required
            />
            {confirmPassword && newPassword !== confirmPassword && (
              <span className="error-hint">Passwords do not match</span>
            )}
          </div>
          {message.text && (
            <div className={`message ${message.type}`}>
              {message.type === 'success' ? <Check size={16} /> : <AlertTriangle size={16} />}
              {message.text}
            </div>
          )}
          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Changing...' : 'Change Password'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Two-Factor Setup Modal
function TwoFactorSetupModal({ isOpen, onClose, onComplete }) {
  const [step, setStep] = useState(1);
  const [setupData, setSetupData] = useState(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [copiedCode, setCopiedCode] = useState(false);

  useEffect(() => {
    if (isOpen && step === 1) {
      initSetup();
    }
  }, [isOpen]);

  const initSetup = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/2fa/setup', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setSetupData(data);
      } else {
        const data = await response.json();
        setMessage({ type: 'error', text: data.error || data.detail || 'Failed to setup 2FA' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error' });
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/2fa/enable', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ code: verificationCode })
      });

      if (response.ok) {
        setStep(3); // Show backup codes
      } else {
        const data = await response.json();
        setMessage({ type: 'error', text: data.error || data.detail || 'Invalid code' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error' });
    } finally {
      setLoading(false);
    }
  };

  const copyBackupCodes = () => {
    if (setupData?.backup_codes) {
      navigator.clipboard.writeText(setupData.backup_codes.join('\n'));
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    }
  };

  const handleClose = () => {
    if (step === 3) {
      onComplete?.();
    }
    onClose();
    setStep(1);
    setSetupData(null);
    setVerificationCode('');
    setMessage({ type: '', text: '' });
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content modal-2fa" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3><Shield size={20} /> {step === 3 ? 'Backup Codes' : 'Setup Two-Factor Authentication'}</h3>
          <button className="modal-close" onClick={handleClose}><X size={20} /></button>
        </div>

        {loading && !setupData ? (
          <div className="modal-loading">Setting up 2FA...</div>
        ) : step === 1 && setupData ? (
          <div className="two-factor-setup">
            <p>Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)</p>
            <div className="qr-code-container">
              <img src={setupData.qr_code} alt="2FA QR Code" />
            </div>
            <p className="manual-entry">
              Or enter this code manually: <code>{setupData.secret}</code>
            </p>
            <button className="btn-primary" onClick={() => setStep(2)}>
              I've scanned the code
            </button>
          </div>
        ) : step === 2 ? (
          <form onSubmit={handleVerify} className="two-factor-verify">
            <p>Enter the 6-digit code from your authenticator app to verify setup:</p>
            <input
              type="text"
              value={verificationCode}
              onChange={e => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              maxLength={6}
              className="verification-input"
              autoFocus
            />
            {message.text && (
              <div className={`message ${message.type}`}>
                <AlertTriangle size={16} /> {message.text}
              </div>
            )}
            <div className="modal-actions">
              <button type="button" className="btn-secondary" onClick={() => setStep(1)}>Back</button>
              <button type="submit" className="btn-primary" disabled={loading || verificationCode.length !== 6}>
                {loading ? 'Verifying...' : 'Verify & Enable'}
              </button>
            </div>
          </form>
        ) : step === 3 && setupData ? (
          <div className="backup-codes">
            <div className="backup-codes-warning">
              <AlertTriangle size={20} />
              <p>Save these backup codes in a secure place. You can use them to access your account if you lose your authenticator device.</p>
            </div>
            <div className="backup-codes-list">
              {setupData.backup_codes.map((code, i) => (
                <code key={i}>{code}</code>
              ))}
            </div>
            <button className="btn-secondary" onClick={copyBackupCodes}>
              {copiedCode ? <><Check size={16} /> Copied!</> : <><Copy size={16} /> Copy Codes</>}
            </button>
            <button className="btn-primary" onClick={handleClose}>
              I've saved my backup codes
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}

// Email Change Modal
function EmailChangeModal({ isOpen, onClose, currentEmail, onSuccess }) {
  const [newEmail, setNewEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/email/change', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ new_email: newEmail, password })
      });

      if (response.ok) {
        setMessage({
          type: 'success',
          text: 'Verification email sent! Check your new email address to confirm the change.'
        });
        setTimeout(() => {
          onClose();
          setNewEmail('');
          setPassword('');
        }, 3000);
      } else {
        const data = await response.json();
        setMessage({ type: 'error', text: data.error || data.detail || 'Failed to request email change' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3><Mail size={20} /> Change Email Address</h3>
          <button className="modal-close" onClick={onClose}><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Current Email</label>
            <input type="email" value={currentEmail || 'Not set'} disabled />
          </div>
          <div className="form-group">
            <label>New Email Address</label>
            <input
              type="email"
              value={newEmail}
              onChange={e => setNewEmail(e.target.value)}
              required
              placeholder="Enter new email address"
            />
          </div>
          <div className="form-group">
            <label>Confirm with Password</label>
            <div className="password-input-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                placeholder="Enter your current password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
          {message.text && (
            <div className={`message ${message.type}`}>
              {message.type === 'success' ? <Check size={16} /> : <AlertTriangle size={16} />}
              {message.text}
            </div>
          )}
          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Sending...' : 'Send Verification Email'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Settings({ isOpen, onClose, username, userEmail }) {
  const [featureFlags, setFeatureFlags] = useState(() => {
    const flags = {};
    FEATURE_FLAGS.forEach(flag => {
      const stored = localStorage.getItem(flag.key);
      flags[flag.key] = stored === null ? flag.default : stored === 'true';
    });
    return flags;
  });

  const [showChangePassword, setShowChangePassword] = useState(false);
  const [showTwoFactorSetup, setShowTwoFactorSetup] = useState(false);
  const [showEmailChange, setShowEmailChange] = useState(false);
  const [twoFactorStatus, setTwoFactorStatus] = useState({ is_enabled: false, has_backup_codes: false });

  // Profile state
  const [profile, setProfile] = useState(null);
  const [editingDisplayName, setEditingDisplayName] = useState(false);
  const [displayNameInput, setDisplayNameInput] = useState('');

  // New state for preferences, notifications, sessions
  const [preferences, setPreferences] = useState(null);
  const [prefOptions, setPrefOptions] = useState(null);
  const [notifications, setNotifications] = useState(null);
  const [notifOptions, setNotifOptions] = useState(null);
  const [sessions, setSessions] = useState([]);

  // Fetch all data when settings opens
  useEffect(() => {
    if (isOpen) {
      fetchProfile();
      fetch2FAStatus();
      fetchPreferences();
      fetchNotifications();
      fetchSessions();
    }
  }, [isOpen]);

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/profile', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setProfile(data);
        setDisplayNameInput(data.display_name || '');
        // Save display_name to localStorage for use elsewhere in the app
        if (data.display_name) {
          localStorage.setItem('displayName', data.display_name);
        } else {
          localStorage.removeItem('displayName');
        }
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
    }
  };

  const updateDisplayName = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ display_name: displayNameInput || null })
      });
      if (response.ok) {
        const data = await response.json();
        setProfile(data);
        setEditingDisplayName(false);
        // Update localStorage
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

  const startEditingDisplayName = () => {
    setDisplayNameInput(profile?.display_name || '');
    setEditingDisplayName(true);
  };

  const cancelEditingDisplayName = () => {
    setDisplayNameInput(profile?.display_name || '');
    setEditingDisplayName(false);
  };

  const fetch2FAStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/2fa/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setTwoFactorStatus(data);
      }
    } catch (error) {
      console.error('Error fetching 2FA status:', error);
    }
  };

  const fetchPreferences = async () => {
    try {
      const token = localStorage.getItem('token');
      const [prefsRes, optionsRes] = await Promise.all([
        fetch('http://localhost:8000/settings/preferences', {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch('http://localhost:8000/settings/options', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);
      if (prefsRes.ok) {
        const prefs = await prefsRes.json();
        setPreferences(prefs);
        // Apply preferences to UI immediately
        applyAllPreferences(prefs);
      }
      if (optionsRes.ok) setPrefOptions(await optionsRes.json());
    } catch (error) {
      console.error('Error fetching preferences:', error);
    }
  };

  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem('token');
      const [notifsRes, optionsRes] = await Promise.all([
        fetch('http://localhost:8000/settings/notifications', {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch('http://localhost:8000/settings/notifications/options', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);
      if (notifsRes.ok) setNotifications(await notifsRes.json());
      if (optionsRes.ok) setNotifOptions(await optionsRes.json());
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const fetchSessions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/sessions', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setSessions(data.sessions || []);
      }
    } catch (error) {
      console.error('Error fetching sessions:', error);
    }
  };

  const updatePreference = async (key, value) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/settings/preferences', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ [key]: value })
      });
      if (response.ok) {
        const data = await response.json();
        setPreferences(data);
        // Apply preferences immediately
        applyPreference(key, value);
      }
    } catch (error) {
      console.error('Error updating preference:', error);
    }
  };

  // Apply a preference to the UI immediately
  const applyPreference = (key, value) => {
    const root = document.documentElement;

    if (key === 'theme') {
      // Update localStorage for App.js dark mode state
      localStorage.setItem('darkMode', JSON.stringify(value === 'dark'));
      // Apply theme immediately
      root.setAttribute('data-theme', value);
    }

    if (key === 'accent_color') {
      // Apply accent color CSS variables
      const accentColors = {
        blue: { primary: '#3B82F6', hover: '#2563EB', light: '#DBEAFE' },
        purple: { primary: '#8B5CF6', hover: '#7C3AED', light: '#EDE9FE' },
        green: { primary: '#10B981', hover: '#059669', light: '#D1FAE5' },
        orange: { primary: '#F59E0B', hover: '#D97706', light: '#FEF3C7' },
        pink: { primary: '#EC4899', hover: '#DB2777', light: '#FCE7F3' },
      };
      const colors = accentColors[value] || accentColors.blue;
      root.style.setProperty('--accent-color', colors.primary);
      root.style.setProperty('--accent-hover', colors.hover);
      root.style.setProperty('--accent-light', colors.light);
      localStorage.setItem('accentColor', value);
    }

    if (key === 'ui_density') {
      // Apply UI density CSS variables
      const densityValues = {
        compact: { spacing: '8px', padding: '12px', fontSize: '13px' },
        comfortable: { spacing: '16px', padding: '16px', fontSize: '14px' },
        spacious: { spacing: '24px', padding: '20px', fontSize: '15px' },
      };
      const density = densityValues[value] || densityValues.comfortable;
      root.style.setProperty('--density-spacing', density.spacing);
      root.style.setProperty('--density-padding', density.padding);
      root.style.setProperty('--density-font-size', density.fontSize);
      root.setAttribute('data-density', value);
      localStorage.setItem('uiDensity', value);
    }
  };

  // Apply all preferences on load
  const applyAllPreferences = (prefs) => {
    if (prefs.theme) applyPreference('theme', prefs.theme);
    if (prefs.accent_color) applyPreference('accent_color', prefs.accent_color);
    if (prefs.ui_density) applyPreference('ui_density', prefs.ui_density);
  };

  const updateNotification = async (key, value) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/settings/notifications', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ [key]: value })
      });
      if (response.ok) {
        const data = await response.json();
        setNotifications(data);
      }
    } catch (error) {
      console.error('Error updating notification:', error);
    }
  };

  const revokeSession = async (sessionId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        fetchSessions();
      } else {
        const data = await response.json();
        alert(data.error || data.detail || 'Failed to revoke session');
      }
    } catch (error) {
      console.error('Error revoking session:', error);
    }
  };

  const revokeAllSessions = async () => {
    if (!window.confirm('Revoke all other sessions? You will stay logged in on this device.')) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/sessions/revoke-all', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        alert(`Revoked ${data.revoked_count} session(s)`);
        fetchSessions();
      }
    } catch (error) {
      console.error('Error revoking sessions:', error);
    }
  };

  // Save feature flags to localStorage when they change
  useEffect(() => {
    Object.entries(featureFlags).forEach(([key, value]) => {
      localStorage.setItem(key, value.toString());
    });
  }, [featureFlags]);

  const toggleFeatureFlag = (key) => {
    setFeatureFlags(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleDisable2FA = async () => {
    const code = prompt('Enter your 2FA code to disable:');
    const password = prompt('Enter your password to confirm:');

    if (!code || !password) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/2fa/disable', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ code, password })
      });

      if (response.ok) {
        alert('Two-factor authentication disabled');
        fetch2FAStatus();
      } else {
        const data = await response.json();
        alert(data.error || data.detail || 'Failed to disable 2FA');
      }
    } catch (error) {
      alert('Network error');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="settings-overlay" onClick={onClose} role="presentation">
      <div
        className="settings-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-title"
      >
        <div className="settings-header">
          <h2 id="settings-title">Settings</h2>
          <button className="settings-close-btn" onClick={onClose} aria-label="Close settings">
            <X size={24} />
          </button>
        </div>

        <div className="settings-content">
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
              <button
                className="btn-secondary btn-small"
                onClick={() => setShowEmailChange(true)}
              >
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
                      <button className="btn-small btn-secondary" onClick={cancelEditingDisplayName}>
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <p>{profile?.display_name || 'Not set'}</p>
                )}
              </div>
              {!editingDisplayName && (
                <button
                  className="btn-secondary btn-small"
                  onClick={startEditingDisplayName}
                >
                  <Edit3 size={14} /> Edit
                </button>
              )}
            </div>
          </div>

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
              <button
                className="btn-secondary"
                onClick={() => setShowChangePassword(true)}
              >
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
                <button
                  className="btn-danger"
                  onClick={handleDisable2FA}
                >
                  Disable 2FA
                </button>
              ) : (
                <button
                  className="btn-primary"
                  onClick={() => setShowTwoFactorSetup(true)}
                >
                  Enable 2FA
                </button>
              )}
            </div>
          </div>

          <div className="settings-section">
            <div className="settings-section-header">
              <Palette size={20} />
              <h3>Appearance</h3>
            </div>
            {preferences && prefOptions ? (
              <div className="settings-appearance-grid">
                <div className="settings-appearance-item">
                  <label>Theme</label>
                  <select
                    value={preferences.theme}
                    onChange={(e) => updatePreference('theme', e.target.value)}
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
                    onChange={(e) => updatePreference('accent_color', e.target.value)}
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
                    onChange={(e) => updatePreference('ui_density', e.target.value)}
                    className="settings-select"
                  >
                    {prefOptions.ui_density.map(d => (
                      <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                    ))}
                  </select>
                </div>
              </div>
            ) : (
              <div className="settings-item">
                <div className="settings-item-info">
                  <p className="settings-placeholder">Loading preferences...</p>
                </div>
              </div>
            )}
          </div>

          <div className="settings-section">
            <div className="settings-section-header">
              <Bell size={20} />
              <h3>Notifications</h3>
            </div>
            {notifications && notifOptions ? (
              <>
                {notifOptions.email_types.map(opt => (
                  <div key={opt.key} className="settings-item settings-item-toggle">
                    <div className="settings-item-info">
                      <label>{opt.label}</label>
                      <p>{opt.description}</p>
                    </div>
                    <button
                      className={`toggle-switch ${notifications[opt.key] ? 'active' : ''}`}
                      onClick={() => updateNotification(opt.key, !notifications[opt.key])}
                      role="switch"
                      aria-checked={notifications[opt.key]}
                    >
                      <span className="toggle-slider" />
                    </button>
                  </div>
                ))}
              </>
            ) : (
              <div className="settings-item">
                <div className="settings-item-info">
                  <p className="settings-placeholder">Loading notifications...</p>
                </div>
              </div>
            )}
          </div>

          <div className="settings-section">
            <div className="settings-section-header">
              <Shield size={20} />
              <h3>Active Sessions</h3>
            </div>
            {sessions.length > 0 ? (
              <>
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
                        onClick={() => revokeSession(session.id)}
                      >
                        Revoke
                      </button>
                    )}
                  </div>
                ))}
                {sessions.length > 1 && (
                  <div className="settings-item">
                    <button className="btn-secondary" onClick={revokeAllSessions}>
                      Revoke All Other Sessions
                    </button>
                  </div>
                )}
              </>
            ) : (
              <div className="settings-item">
                <div className="settings-item-info">
                  <p className="settings-placeholder">Loading sessions...</p>
                </div>
              </div>
            )}
          </div>

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
                  onClick={() => toggleFeatureFlag(flag.key)}
                  role="switch"
                  aria-checked={featureFlags[flag.key]}
                  aria-label={`Toggle ${flag.label}`}
                >
                  <span className="toggle-slider" />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="settings-footer">
          <p className="settings-version">Mnemosyne v1.0.0</p>
        </div>
      </div>

      <ChangePasswordModal
        isOpen={showChangePassword}
        onClose={() => setShowChangePassword(false)}
      />

      <TwoFactorSetupModal
        isOpen={showTwoFactorSetup}
        onClose={() => setShowTwoFactorSetup(false)}
        onComplete={fetch2FAStatus}
      />

      <EmailChangeModal
        isOpen={showEmailChange}
        onClose={() => setShowEmailChange(false)}
        currentEmail={profile?.email || userEmail}
        onSuccess={fetchProfile}
      />
    </div>
  );
}

export default Settings;
