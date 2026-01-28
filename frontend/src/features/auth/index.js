/**
 * Auth Feature - Public Exports
 *
 * Main entry point for the authentication feature.
 */

import { API_URL } from '../../utils/api';

// Components
export { default as Login } from './components/Login';
export { default as EmailVerification } from './components/EmailVerification';

// Hooks (to be added)
// export { useAuth } from './hooks/useAuth';

// API utility re-export for convenience
export { API_URL, api } from '../../utils/api';

// Constants - use API_URL from environment
export const AUTH_ENDPOINTS = {
  LOGIN: `${API_URL}/login`,
  REGISTER: `${API_URL}/register`,
  ME: `${API_URL}/me`,
  LOGOUT: `${API_URL}/logout`,
};
