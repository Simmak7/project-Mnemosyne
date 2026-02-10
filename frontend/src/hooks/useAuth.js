/**
 * useAuth - Authentication state and handlers
 */
import { useState, useEffect, useCallback } from 'react';
import { API_URL, api } from '../utils/api';
import { setupAuthListeners, startTokenValidation, stopTokenValidation } from '../utils/authEvents';

const ACCENT_COLORS = {
  blue: { primary: '#3B82F6', hover: '#2563EB', light: '#DBEAFE' },
  purple: { primary: '#8B5CF6', hover: '#7C3AED', light: '#EDE9FE' },
  green: { primary: '#10B981', hover: '#059669', light: '#D1FAE5' },
  orange: { primary: '#F59E0B', hover: '#D97706', light: '#FEF3C7' },
  pink: { primary: '#EC4899', hover: '#DB2777', light: '#FCE7F3' },
};

const DENSITY_VALUES = {
  compact: { spacing: '8px', padding: '12px', fontSize: '13px' },
  comfortable: { spacing: '16px', padding: '16px', fontSize: '14px' },
  spacious: { spacing: '24px', padding: '20px', fontSize: '15px' },
};

/**
 * Fetch user preferences from server and apply only MISSING values.
 * localStorage is authoritative (set by theme toggle / Settings UI).
 * Server prefs only fill gaps (e.g. after logout clears localStorage).
 */
async function loadAndApplyPreferences(token) {
  try {
    const res = await fetch(`${API_URL}/settings/preferences`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (!res.ok) return;
    const prefs = await res.json();
    const root = document.documentElement;

    // Only restore theme if localStorage was cleared (e.g. after logout)
    if (prefs.theme && localStorage.getItem('darkMode') === null) {
      localStorage.setItem('darkMode', JSON.stringify(prefs.theme === 'dark'));
      root.setAttribute('data-theme', prefs.theme);
    }

    if (prefs.accent_color && !localStorage.getItem('accentColor')) {
      const colors = ACCENT_COLORS[prefs.accent_color] || ACCENT_COLORS.blue;
      root.style.setProperty('--accent-color', colors.primary);
      root.style.setProperty('--accent-hover', colors.hover);
      root.style.setProperty('--accent-light', colors.light);
      localStorage.setItem('accentColor', prefs.accent_color);
    }

    if (prefs.ui_density && !localStorage.getItem('uiDensity')) {
      const d = DENSITY_VALUES[prefs.ui_density] || DENSITY_VALUES.comfortable;
      root.style.setProperty('--density-spacing', d.spacing);
      root.style.setProperty('--density-padding', d.padding);
      root.style.setProperty('--density-font-size', d.fontSize);
      root.setAttribute('data-density', prefs.ui_density);
      localStorage.setItem('uiDensity', prefs.ui_density);
    }
  } catch (e) {
    // Preferences fetch failed, not critical
  }
}

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('');

  // Check for existing token on app load and validate it
  useEffect(() => {
    const validateToken = async () => {
      const token = localStorage.getItem('token');
      const savedUsername = localStorage.getItem('username');

      if (token && savedUsername) {
        try {
          const response = await fetch(`${API_URL}/me`, {
            headers: { 'Authorization': `Bearer ${token}` },
            credentials: 'include',
          });

          if (response.ok) {
            setIsAuthenticated(true);
            setUsername(savedUsername);
            // Fetch profile and preferences in parallel
            const profilePromise = fetch(`${API_URL}/profile`, {
              headers: { 'Authorization': `Bearer ${token}` },
            }).then(r => r.ok ? r.json() : null).catch(() => null);

            const prefsPromise = loadAndApplyPreferences(token);

            const profile = await profilePromise;
            if (profile?.display_name) {
              localStorage.setItem('displayName', profile.display_name);
            }
            await prefsPromise;
          } else {
            if (process.env.NODE_ENV === 'development') {
              console.log('Token validation failed, clearing localStorage');
            }
            localStorage.removeItem('token');
            localStorage.removeItem('username');
          }
        } catch (error) {
          if (process.env.NODE_ENV === 'development') {
            console.error('Token validation failed:', error);
          }
          localStorage.removeItem('token');
          localStorage.removeItem('username');
        }
      }
    };

    validateToken();
  }, []);

  // Setup auth event listeners and periodic token validation when authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      stopTokenValidation();
      return;
    }

    const handleAuthLogout = (reason) => {
      console.log('Session ended:', reason);
      clearAuthState();
      setIsAuthenticated(false);
      setUsername('');
    };

    const cleanupListeners = setupAuthListeners(handleAuthLogout);
    const cleanupValidation = startTokenValidation();

    return () => {
      cleanupListeners();
      cleanupValidation();
    };
  }, [isAuthenticated]);

  const clearAuthState = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('displayName');
    localStorage.removeItem('accentColor');
    localStorage.removeItem('uiDensity');
    // Clear all persisted Mnemosyne state (notes selection, sort prefs, custom order)
    const mnemosyneKeys = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith('mnemosyne:')) mnemosyneKeys.push(key);
    }
    mnemosyneKeys.forEach(k => localStorage.removeItem(k));
    api.clearAuth();

    const root = document.documentElement;
    root.style.removeProperty('--accent-color');
    root.style.removeProperty('--accent-hover');
    root.style.removeProperty('--accent-light');
    root.style.removeProperty('--density-spacing');
    root.style.removeProperty('--density-padding');
    root.style.removeProperty('--density-font-size');
    root.removeAttribute('data-density');
  }, []);

  const handleLoginSuccess = useCallback(async (token, user) => {
    setIsAuthenticated(true);
    setUsername(user);
    // Load preferences and profile in parallel after login
    const profilePromise = fetch(`${API_URL}/profile`, {
      headers: { 'Authorization': `Bearer ${token}` },
    }).then(r => r.ok ? r.json() : null).catch(() => null);

    const prefsPromise = loadAndApplyPreferences(token);

    const profile = await profilePromise;
    if (profile?.display_name) {
      localStorage.setItem('displayName', profile.display_name);
    }
    await prefsPromise;
  }, []);

  const handleLogout = useCallback(async () => {
    try {
      await fetch(`${API_URL}/logout`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
    } catch (error) {
      console.warn('Logout API call failed:', error);
    }

    clearAuthState();
    setIsAuthenticated(false);
    setUsername('');
  }, [clearAuthState]);

  return {
    isAuthenticated,
    username,
    handleLoginSuccess,
    handleLogout,
  };
}

export default useAuth;
