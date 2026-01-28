import React, { useState } from 'react';
import { API_URL } from '../../../utils/api';
import './Login.css';

/**
 * Login/Register component for user authentication.
 * Supports two-factor authentication (2FA) flow.
 *
 * Authentication is handled via httpOnly cookies for security.
 * The token is also stored in localStorage for backward compatibility
 * with components that check auth status on page load.
 *
 * @param {Object} props
 * @param {Function} props.onLoginSuccess - Callback when login succeeds (token, username)
 */
function Login({ onLoginSuccess }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');

  // 2FA state
  const [requires2FA, setRequires2FA] = useState(false);
  const [tempToken, setTempToken] = useState('');
  const [twoFactorCode, setTwoFactorCode] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      if (isRegistering) {
        // Register
        const registerResponse = await fetch(`${API_URL}/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include', // Include cookies for CSRF
          body: JSON.stringify({ username, email, password }),
        });

        if (registerResponse.ok) {
          setMessage('Registration successful! Please login.');
          setMessageType('success');
          setIsRegistering(false);
          setPassword('');
        } else {
          const errorData = await registerResponse.json();
          setMessage(`Registration failed: ${errorData.error || errorData.detail}`);
          setMessageType('error');
        }
      } else if (requires2FA) {
        // Complete 2FA login
        const response = await fetch(`${API_URL}/login/2fa`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include', // Include cookies for CSRF and auth
          body: JSON.stringify({ temp_token: tempToken, code: twoFactorCode }),
        });

        if (response.ok) {
          const data = await response.json();
          // Store token in localStorage for backward compatibility
          // Primary auth is now via httpOnly cookie set by server
          localStorage.setItem('token', data.access_token);
          localStorage.setItem('username', username);
          setMessage('Login successful!');
          setMessageType('success');
          onLoginSuccess(data.access_token, username);
        } else {
          const errorData = await response.json();
          setMessage(`2FA verification failed: ${errorData.error || errorData.detail || 'Invalid code'}`);
          setMessageType('error');
        }
      } else {
        // Initial login
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const loginResponse = await fetch(`${API_URL}/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          credentials: 'include', // Include cookies for CSRF and auth
          body: formData,
        });

        if (loginResponse.ok) {
          const data = await loginResponse.json();

          // Check if 2FA is required
          if (data.requires_2fa) {
            setRequires2FA(true);
            setTempToken(data.temp_token);
            setMessage('Enter your authenticator code to continue');
            setMessageType('info');
          } else {
            // Store token in localStorage for backward compatibility
            // Primary auth is now via httpOnly cookie set by server
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('username', username);
            setMessage('Login successful!');
            setMessageType('success');
            onLoginSuccess(data.access_token, username);
          }
        } else {
          const errorData = await loginResponse.json();
          setMessage(`Login failed: ${errorData.error || errorData.detail || 'Invalid credentials'}`);
          setMessageType('error');
        }
      }
    } catch (error) {
      setMessage(`Error: ${error.message}`);
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>Mnemosyne</h1>
        <h2>{requires2FA ? 'Two-Factor Authentication' : (isRegistering ? 'Create Account' : 'Login')}</h2>

        {message && (
          <div
            className={`message ${messageType}`}
            role="alert"
            aria-live="polite"
            id="login-message"
          >
            {message}
          </div>
        )}

        <form onSubmit={handleSubmit} aria-describedby={message ? 'login-message' : undefined}>
          <fieldset disabled={loading}>
            <legend className="sr-only">{requires2FA ? '2FA verification' : (isRegistering ? 'Registration' : 'Login')} form</legend>

            {requires2FA ? (
              /* 2FA Code Input */
              <div className="form-group">
                <label htmlFor="twoFactorCode">Enter your 6-digit code:</label>
                <input
                  id="twoFactorCode"
                  type="text"
                  value={twoFactorCode}
                  onChange={(e) => setTwoFactorCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  required
                  disabled={loading}
                  placeholder="000000"
                  maxLength={6}
                  autoComplete="one-time-code"
                  aria-required="true"
                  autoFocus
                  style={{ fontSize: '1.5rem', textAlign: 'center', letterSpacing: '0.5rem' }}
                />
              </div>
            ) : (
              /* Normal Login/Register Form */
              <>
                <div className="form-group">
                  <label htmlFor="username">Username:</label>
                  <input
                    id="username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    disabled={loading}
                    autoComplete="username"
                    aria-required="true"
                  />
                </div>

                {isRegistering && (
                  <div className="form-group">
                    <label htmlFor="email">Email:</label>
                    <input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      disabled={loading}
                      autoComplete="email"
                      aria-required="true"
                    />
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="password">Password:</label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    disabled={loading}
                    autoComplete={isRegistering ? 'new-password' : 'current-password'}
                    aria-required="true"
                  />
                </div>
              </>
            )}

            <button type="submit" disabled={loading || (requires2FA && twoFactorCode.length !== 6)} className="submit-button" aria-busy={loading}>
              {loading ? 'Please wait...' : (requires2FA ? 'Verify' : (isRegistering ? 'Register' : 'Login'))}
            </button>
          </fieldset>
        </form>

        <div className="toggle-mode">
          {requires2FA ? (
            <button
              type="button"
              onClick={() => {
                setRequires2FA(false);
                setTempToken('');
                setTwoFactorCode('');
                setMessage('');
              }}
              disabled={loading}
              className="link-button"
            >
              Back to login
            </button>
          ) : (
            <button
              type="button"
              onClick={() => {
                setIsRegistering(!isRegistering);
                setMessage('');
                setPassword('');
              }}
              disabled={loading}
              className="link-button"
            >
              {isRegistering ? 'Already have an account? Login' : 'Need an account? Register'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default Login;
