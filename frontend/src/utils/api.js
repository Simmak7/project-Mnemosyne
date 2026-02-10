/**
 * API Configuration and HTTP Client Utilities
 *
 * Centralizes API URL configuration and provides a secure fetch wrapper
 * that handles authentication via httpOnly cookies with CSRF protection.
 *
 * Usage:
 *   import { api, API_URL } from '../utils/api';
 *
 *   // Simple GET request
 *   const data = await api.get('/notes/');
 *
 *   // POST with JSON body
 *   const result = await api.post('/notes/', { title: 'My Note', content: '...' });
 *
 *   // Form data (for login)
 *   const token = await api.postForm('/login', { username, password });
 */

// API base URL from environment variable, fallback to localhost for development
export const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// CSRF token storage (refreshed on each request that returns a new token)
let csrfToken = null;

// Track if CSRF has been initialized
let csrfInitialized = false;
let csrfInitPromise = null;

// Token refresh state (prevents multiple concurrent refresh attempts)
let refreshPromise = null;
let isRefreshing = false;

/**
 * Get the current CSRF token from memory
 */
function getCsrfToken() {
  return csrfToken;
}

/**
 * Update CSRF token from response header
 */
function updateCsrfToken(response) {
  const newToken = response.headers.get('X-CSRF-Token');
  if (newToken) {
    csrfToken = newToken;
    csrfInitialized = true;
  }
}

/**
 * Build full URL from path
 */
function buildUrl(path) {
  // Handle both /path and path formats
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_URL}${cleanPath}`;
}

/**
 * Initialize CSRF token by making a GET request
 * This should be called before any state-changing requests
 */
async function initCsrf() {
  // If already initialized, return immediately
  if (csrfInitialized && csrfToken) {
    return csrfToken;
  }

  // If initialization is in progress, wait for it
  if (csrfInitPromise) {
    return csrfInitPromise;
  }

  // Start initialization
  csrfInitPromise = (async () => {
    try {
      // Make a simple GET request to get the CSRF token
      const response = await fetch(buildUrl('/health'), {
        method: 'GET',
        credentials: 'include',
      });
      updateCsrfToken(response);
      return csrfToken;
    } catch (error) {
      console.warn('Failed to initialize CSRF token:', error);
      return null;
    } finally {
      csrfInitPromise = null;
    }
  })();

  return csrfInitPromise;
}

/**
 * Ensure CSRF token is available before state-changing requests
 */
async function ensureCsrf() {
  if (!csrfToken) {
    await initCsrf();
  }
}

/**
 * Refresh the access token using the refresh token cookie.
 * Prevents multiple concurrent refresh attempts.
 *
 * @returns {Promise<boolean>} True if refresh succeeded, false otherwise
 */
async function refreshAccessToken() {
  // If already refreshing, wait for that attempt
  if (refreshPromise) {
    return refreshPromise;
  }

  // Start refresh attempt
  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      const response = await fetch(buildUrl('/auth/refresh'), {
        method: 'POST',
        credentials: 'include', // Include cookies (refresh token)
        headers: {
          'X-CSRF-Token': csrfToken || '',
        },
      });

      if (response.ok) {
        const data = await response.json();
        // Update stored access token if frontend stores it
        if (data.access_token) {
          localStorage.setItem('token', data.access_token);
        }
        // Update CSRF token from response
        updateCsrfToken(response);
        return true;
      }

      // Refresh failed - token might be expired or revoked
      return false;
    } catch (error) {
      console.warn('Token refresh failed:', error);
      return false;
    } finally {
      refreshPromise = null;
      isRefreshing = false;
    }
  })();

  return refreshPromise;
}

/**
 * Dispatch auth logout event for centralized handling
 */
function dispatchAuthLogout(reason = 'session_expired') {
  window.dispatchEvent(new CustomEvent('auth:logout', {
    detail: { reason, timestamp: Date.now() }
  }));
}

/**
 * Base fetch wrapper with authentication and error handling
 */
async function fetchWithAuth(path, options = {}, isRetry = false) {
  const url = buildUrl(path);

  // Default headers
  const headers = {
    ...options.headers,
  };

  // Add CSRF token for state-changing requests
  const method = (options.method || 'GET').toUpperCase();
  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
    // Ensure CSRF token is available
    await ensureCsrf();
    const token = getCsrfToken();
    if (token) {
      headers['X-CSRF-Token'] = token;
    }
  }

  // Include credentials (cookies) in requests
  const fetchOptions = {
    ...options,
    headers,
    credentials: 'include', // Send cookies with requests
  };

  try {
    const response = await fetch(url, fetchOptions);

    // Update CSRF token from response
    updateCsrfToken(response);

    // Handle 401 Unauthorized - attempt token refresh
    if (response.status === 401 && !isRetry && !isRefreshing) {
      // Don't retry refresh endpoint itself
      if (path.includes('/auth/refresh')) {
        dispatchAuthLogout('refresh_failed');
        return response;
      }

      // Attempt to refresh the token
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        // Retry the original request with new token
        return fetchWithAuth(path, options, true);
      }

      // Refresh failed - dispatch logout event
      dispatchAuthLogout('session_expired');
    }

    return response;
  } catch (error) {
    // Network error
    console.error(`API request failed: ${method} ${path}`, error);
    throw error;
  }
}

/**
 * API client with convenience methods
 */
export const api = {
  /**
   * Initialize CSRF token (call on app startup or before first POST)
   */
  initCsrf,

  /**
   * GET request
   */
  async get(path, options = {}) {
    const response = await fetchWithAuth(path, {
      method: 'GET',
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, error.detail || error.error || 'Request failed');
    }

    return response.json();
  },

  /**
   * POST request with JSON body
   */
  async post(path, data = {}, options = {}) {
    const response = await fetchWithAuth(path, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      body: JSON.stringify(data),
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, error.detail || error.error || 'Request failed');
    }

    return response.json();
  },

  /**
   * POST request with form data (for OAuth2 password flow)
   */
  async postForm(path, data = {}, options = {}) {
    const formData = new URLSearchParams();
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        formData.append(key, value);
      }
    });

    const response = await fetchWithAuth(path, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        ...options.headers,
      },
      body: formData,
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, error.detail || error.error || 'Request failed');
    }

    return response.json();
  },

  /**
   * PUT request with JSON body
   */
  async put(path, data = {}, options = {}) {
    const response = await fetchWithAuth(path, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      body: JSON.stringify(data),
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, error.detail || error.error || 'Request failed');
    }

    return response.json();
  },

  /**
   * PATCH request with JSON body
   */
  async patch(path, data = {}, options = {}) {
    const response = await fetchWithAuth(path, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      body: JSON.stringify(data),
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, error.detail || error.error || 'Request failed');
    }

    return response.json();
  },

  /**
   * DELETE request
   */
  async delete(path, options = {}) {
    const response = await fetchWithAuth(path, {
      method: 'DELETE',
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, error.detail || error.error || 'Request failed');
    }

    // DELETE might return empty body
    const text = await response.text();
    return text ? JSON.parse(text) : null;
  },

  /**
   * Raw fetch with auth (for custom handling like file uploads, streaming)
   */
  fetch: fetchWithAuth,

  /**
   * Build full URL (useful for image sources, etc.)
   */
  buildUrl,

  /**
   * Clear authentication state (call on logout)
   */
  clearAuth() {
    csrfToken = null;
    csrfInitialized = false;
    refreshPromise = null;
    isRefreshing = false;
  },

  /**
   * Manually trigger token refresh (call proactively before expiration)
   */
  refreshToken: refreshAccessToken,

  /**
   * Check if token refresh is currently in progress
   */
  isRefreshing() {
    return isRefreshing;
  },
};

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/**
 * Legacy support: Get auth header for components still using direct fetch
 * @deprecated Use api.* methods instead
 */
export function getAuthHeader() {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

/**
 * Legacy support: Build URL for components still using direct fetch
 * @deprecated Use api.buildUrl() instead
 */
export function buildApiUrl(path) {
  return buildUrl(path);
}

export default api;
