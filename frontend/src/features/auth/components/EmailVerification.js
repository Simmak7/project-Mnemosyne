import React, { useState, useEffect } from 'react';
import { Check, AlertTriangle, Loader, Mail } from 'lucide-react';
import './EmailVerification.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Email verification page component.
 * Handles email change verification via token from URL.
 *
 * @param {Object} props
 * @param {Function} props.onComplete - Callback when verification is complete
 */
function EmailVerification({ onComplete }) {
  const [status, setStatus] = useState('verifying'); // verifying, success, error
  const [message, setMessage] = useState('');

  useEffect(() => {
    const verifyEmail = async () => {
      const params = new URLSearchParams(window.location.search);
      const token = params.get('token');

      if (!token) {
        setStatus('error');
        setMessage('No verification token found. Please check your email link.');
        return;
      }

      try {
        const response = await fetch(`${API_BASE}/email/change/verify`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ token }),
        });

        if (response.ok) {
          setStatus('success');
          setMessage('Your email address has been updated successfully!');
          // Clear the URL params
          window.history.replaceState({}, document.title, window.location.pathname);
        } else {
          const data = await response.json();
          setStatus('error');
          setMessage(data.error || data.detail || 'Verification failed. The link may have expired.');
        }
      } catch (error) {
        setStatus('error');
        setMessage('Network error. Please try again.');
      }
    };

    verifyEmail();
  }, []);

  const handleContinue = () => {
    // Clear URL and go to main app
    window.history.replaceState({}, document.title, '/');
    if (onComplete) {
      onComplete();
    } else {
      window.location.href = '/';
    }
  };

  return (
    <div className="email-verification-container">
      <div className="email-verification-card">
        <div className="email-verification-icon">
          {status === 'verifying' && <Loader className="spinning" size={48} />}
          {status === 'success' && <Check size={48} className="success-icon" />}
          {status === 'error' && <AlertTriangle size={48} className="error-icon" />}
        </div>

        <h1>
          {status === 'verifying' && 'Verifying Email...'}
          {status === 'success' && 'Email Verified!'}
          {status === 'error' && 'Verification Failed'}
        </h1>

        <p className={`message ${status}`}>{message || 'Please wait while we verify your email address...'}</p>

        {status !== 'verifying' && (
          <button className="continue-button" onClick={handleContinue}>
            {status === 'success' ? 'Continue to App' : 'Back to Login'}
          </button>
        )}
      </div>
    </div>
  );
}

export default EmailVerification;
