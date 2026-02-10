/**
 * Centralized Authentication Event System
 *
 * Provides utilities for:
 * - Listening to auth events (logout, session expiration)
 * - Proactive token expiration checking
 * - Session management helpers
 */

import { api } from './api';

// Token validation interval (5 minutes)
const TOKEN_CHECK_INTERVAL = 5 * 60 * 1000;

// Refresh token when it expires within this window (5 minutes)
const REFRESH_THRESHOLD = 5 * 60 * 1000;

let tokenCheckInterval = null;

/**
 * Decode a JWT token without verifying the signature.
 * Used to check expiration time on the client side.
 *
 * @param {string} token - JWT token
 * @returns {object|null} Decoded payload or null if invalid
 */
export function decodeToken(token) {
  if (!token) return null;

  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;

    const payload = JSON.parse(atob(parts[1]));
    return payload;
  } catch (error) {
    console.warn('Failed to decode token:', error);
    return null;
  }
}

/**
 * Check if a token is expired or expiring soon.
 *
 * @param {string} token - JWT token
 * @param {number} thresholdMs - Time threshold in ms (refresh if expiring within this window)
 * @returns {{ expired: boolean, expiringSoon: boolean, expiresAt: Date|null }}
 */
export function checkTokenExpiration(token, thresholdMs = REFRESH_THRESHOLD) {
  const payload = decodeToken(token);

  if (!payload || !payload.exp) {
    return { expired: true, expiringSoon: true, expiresAt: null };
  }

  const expiresAt = new Date(payload.exp * 1000);
  const now = Date.now();
  const timeUntilExpiry = expiresAt.getTime() - now;

  return {
    expired: timeUntilExpiry <= 0,
    expiringSoon: timeUntilExpiry <= thresholdMs,
    expiresAt,
    timeUntilExpiry: Math.max(0, timeUntilExpiry),
  };
}

/**
 * Setup auth event listeners.
 *
 * @param {function} onLogout - Callback when logout event is triggered
 * @returns {function} Cleanup function to remove listeners
 */
export function setupAuthListeners(onLogout) {
  const handleLogout = (event) => {
    const reason = event.detail?.reason || 'unknown';
    console.log('Auth logout event received:', reason);
    onLogout(reason);
  };

  window.addEventListener('auth:logout', handleLogout);

  return () => {
    window.removeEventListener('auth:logout', handleLogout);
  };
}

/**
 * Start periodic token validation.
 * Proactively refreshes the token before it expires.
 *
 * @param {function} onSessionExpiring - Optional callback when session is about to expire
 * @returns {function} Cleanup function to stop validation
 */
export function startTokenValidation(onSessionExpiring = null) {
  // Clear any existing interval
  if (tokenCheckInterval) {
    clearInterval(tokenCheckInterval);
  }

  const checkToken = async () => {
    const token = localStorage.getItem('token');
    if (!token) return;

    const { expired, expiringSoon, timeUntilExpiry } = checkTokenExpiration(token);

    if (expired) {
      // Token already expired - attempt refresh
      console.log('Token expired, attempting refresh...');
      const refreshed = await api.refreshToken();
      if (!refreshed) {
        // Refresh failed - trigger logout
        window.dispatchEvent(new CustomEvent('auth:logout', {
          detail: { reason: 'token_expired' }
        }));
      }
      return;
    }

    if (expiringSoon) {
      // Token expiring soon - proactively refresh
      console.log('Token expiring soon, proactively refreshing...');

      // Notify if callback provided
      if (onSessionExpiring) {
        onSessionExpiring(timeUntilExpiry);
      }

      await api.refreshToken();
    }
  };

  // Check immediately on start
  checkToken();

  // Then check periodically
  tokenCheckInterval = setInterval(checkToken, TOKEN_CHECK_INTERVAL);

  return () => {
    if (tokenCheckInterval) {
      clearInterval(tokenCheckInterval);
      tokenCheckInterval = null;
    }
  };
}

/**
 * Stop periodic token validation.
 */
export function stopTokenValidation() {
  if (tokenCheckInterval) {
    clearInterval(tokenCheckInterval);
    tokenCheckInterval = null;
  }
}

/**
 * Get session info from the current token.
 *
 * @returns {object|null} Session info or null if not authenticated
 */
export function getSessionInfo() {
  const token = localStorage.getItem('token');
  if (!token) return null;

  const payload = decodeToken(token);
  if (!payload) return null;

  const { expired, expiringSoon, expiresAt, timeUntilExpiry } = checkTokenExpiration(token);

  return {
    username: payload.sub,
    issuedAt: payload.iat ? new Date(payload.iat * 1000) : null,
    expiresAt,
    expired,
    expiringSoon,
    timeUntilExpiry,
  };
}

export default {
  decodeToken,
  checkTokenExpiration,
  setupAuthListeners,
  startTokenValidation,
  stopTokenValidation,
  getSessionInfo,
};
