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

/**
 * Get the current CSRF token from cookie or memory
 */
function getCsrfToken() {
  // First check memory
  if (csrfToken) return csrfToken;

  // Then check cookie (for page reloads)
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  if (match) {
    csrfToken = match[1];
    return csrfToken;
  }

  return null;
}

/**
 * Update CSRF token from response header
 */
function updateCsrfToken(response) {
  const newToken = response.headers.get('X-CSRF-Token');
  if (newToken) {
    csrfToken = newToken;
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
 * Base fetch wrapper with authentication and error handling
 */
async function fetchWithAuth(path, options = {}) {
  const url = buildUrl(path);

  // Default headers
  const headers = {
    ...options.headers,
  };

  // Add CSRF token for state-changing requests
  const method = (options.method || 'GET').toUpperCase();
  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
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
