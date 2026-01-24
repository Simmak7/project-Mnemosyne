/**
 * Auth Feature - Public Exports
 *
 * Main entry point for the authentication feature.
 */

// Components
export { default as Login } from './components/Login';
export { default as EmailVerification } from './components/EmailVerification';

// Hooks (to be added)
// export { useAuth } from './hooks/useAuth';

// Constants
export const AUTH_ENDPOINTS = {
  LOGIN: 'http://localhost:8000/login',
  REGISTER: 'http://localhost:8000/register',
  ME: 'http://localhost:8000/me',
};
