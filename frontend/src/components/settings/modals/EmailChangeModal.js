/**
 * Modal for changing email address
 */
import React, { useState } from 'react';
import { X, Mail, Eye, EyeOff, Check, AlertTriangle } from 'lucide-react';
import { API_URL } from '../../../utils/api';

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
      const response = await fetch(`${API_URL}/email/change`, {
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

export default EmailChangeModal;
