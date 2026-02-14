/**
 * Hook for fetching and managing settings data
 */
import { useState, useEffect, useCallback } from 'react';
import { api } from '../../../utils/api';
import { FEATURE_FLAGS, ACCENT_COLORS, DENSITY_VALUES } from '../constants';

export function useSettingsData(isOpen) {
  const [profile, setProfile] = useState(null);
  const [twoFactorStatus, setTwoFactorStatus] = useState({ is_enabled: false, has_backup_codes: false });
  const [preferences, setPreferences] = useState(null);
  const [prefOptions, setPrefOptions] = useState(null);
  const [notifications, setNotifications] = useState(null);
  const [notifOptions, setNotifOptions] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [availableModels, setAvailableModels] = useState([]);
  const [modelConfig, setModelConfig] = useState(null);

  const [featureFlags, setFeatureFlags] = useState(() => {
    const flags = {};
    FEATURE_FLAGS.forEach(flag => {
      const stored = localStorage.getItem(flag.key);
      flags[flag.key] = stored === null ? flag.default : stored === 'true';
    });
    return flags;
  });

  const fetchProfile = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/profile', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setProfile(data);
        if (data.display_name) {
          localStorage.setItem('displayName', data.display_name);
        } else {
          localStorage.removeItem('displayName');
        }
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
    }
  }, []);

  const fetch2FAStatus = useCallback(async () => {
    try {
      const response = await api.fetch('/2fa/status');
      if (response.ok) {
        setTwoFactorStatus(await response.json());
      }
    } catch (error) {
      console.error('Error fetching 2FA status:', error);
    }
  }, []);

  const fetchPreferences = useCallback(async () => {
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
        applyAllPreferences(prefs);
      }
      if (optionsRes.ok) setPrefOptions(await optionsRes.json());
    } catch (error) {
      console.error('Error fetching preferences:', error);
    }
  }, []);

  const fetchNotifications = useCallback(async () => {
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
  }, []);

  const fetchSessions = useCallback(async () => {
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
  }, []);

  const fetchModels = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/models', {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setAvailableModels(data.models || []);
        setModelConfig({
          current_rag_model: data.current_rag_model,
          current_brain_model: data.current_brain_model,
          current_vision_model: data.current_vision_model,
        });
      }
    } catch (error) {
      console.error('Error fetching models:', error);
    }
  }, []);

  // Fetch all data when settings opens
  useEffect(() => {
    if (isOpen) {
      fetchProfile();
      fetch2FAStatus();
      fetchPreferences();
      fetchNotifications();
      fetchSessions();
      fetchModels();
    }
  }, [isOpen, fetchProfile, fetch2FAStatus, fetchPreferences, fetchNotifications, fetchSessions, fetchModels]);

  // Save feature flags to localStorage
  useEffect(() => {
    Object.entries(featureFlags).forEach(([key, value]) => {
      localStorage.setItem(key, value.toString());
    });
  }, [featureFlags]);

  const toggleFeatureFlag = useCallback((key) => {
    setFeatureFlags(prev => ({ ...prev, [key]: !prev[key] }));
  }, []);

  const updatePreference = useCallback(async (key, value) => {
    // Optimistically update state so dropdowns reflect the change immediately
    setPreferences(prev => prev ? { ...prev, [key]: value } : prev);
    try {
      const response = await api.fetch('/settings/preferences', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [key]: value })
      });
      if (response.ok) {
        setPreferences(await response.json());
      }
    } catch (error) {
      console.error('Error updating preference:', error);
    }
  }, []);

  const updateNotification = useCallback(async (key, value) => {
    setNotifications(prev => prev ? { ...prev, [key]: value } : prev);
    try {
      const response = await api.fetch('/settings/notifications', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [key]: value })
      });
      if (response.ok) {
        setNotifications(await response.json());
      }
    } catch (error) {
      console.error('Error updating notification:', error);
    }
  }, []);

  const revokeSession = useCallback(async (sessionId) => {
    try {
      const response = await api.fetch(`/sessions/${sessionId}`, {
        method: 'DELETE',
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
  }, [fetchSessions]);

  const revokeAllSessions = useCallback(async () => {
    if (!window.confirm('Revoke all other sessions? You will stay logged in on this device.')) return;
    try {
      const response = await api.fetch('/sessions/revoke-all', {
        method: 'POST',
      });
      if (response.ok) {
        const data = await response.json();
        alert(`Revoked ${data.revoked_count} session(s)`);
        fetchSessions();
      }
    } catch (error) {
      console.error('Error revoking sessions:', error);
    }
  }, [fetchSessions]);

  return {
    // State
    profile,
    twoFactorStatus,
    preferences,
    prefOptions,
    notifications,
    notifOptions,
    sessions,
    availableModels,
    modelConfig,
    featureFlags,
    // Actions
    setProfile,
    fetchProfile,
    fetch2FAStatus,
    toggleFeatureFlag,
    updatePreference,
    updateNotification,
    revokeSession,
    revokeAllSessions,
  };
}

function applyAllPreferences(prefs) {
  const root = document.documentElement;

  if (prefs.theme) {
    localStorage.setItem('darkMode', JSON.stringify(prefs.theme === 'dark'));
    root.setAttribute('data-theme', prefs.theme);
  }

  if (prefs.accent_color) {
    const colors = ACCENT_COLORS[prefs.accent_color] || ACCENT_COLORS.blue;
    root.style.setProperty('--accent-color', colors.primary);
    root.style.setProperty('--accent-hover', colors.hover);
    root.style.setProperty('--accent-light', colors.light);
    localStorage.setItem('accentColor', prefs.accent_color);
  }

  if (prefs.ui_density) {
    const density = DENSITY_VALUES[prefs.ui_density] || DENSITY_VALUES.comfortable;
    root.style.setProperty('--density-spacing', density.spacing);
    root.style.setProperty('--density-padding', density.padding);
    root.style.setProperty('--density-font-size', density.fontSize);
    root.setAttribute('data-density', prefs.ui_density);
    localStorage.setItem('uiDensity', prefs.ui_density);
  }
}

export default useSettingsData;
