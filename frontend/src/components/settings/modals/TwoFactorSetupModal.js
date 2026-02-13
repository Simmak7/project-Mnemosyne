/**
 * Modal for setting up two-factor authentication
 */
import React, { useState, useEffect } from 'react';
import { X, Shield, AlertTriangle, Check, Copy } from 'lucide-react';
import { api } from '../../../utils/api';

function TwoFactorSetupModal({ isOpen, onClose, onComplete }) {
  const [step, setStep] = useState(1);
  const [setupData, setSetupData] = useState(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [copiedCode, setCopiedCode] = useState(false);

  useEffect(() => {
    if (isOpen && step === 1) {
      initSetup();
    }
  }, [isOpen]);

  const initSetup = async () => {
    setLoading(true);
    try {
      const response = await api.fetch('/2fa/setup', { method: 'POST' });
      if (response.ok) {
        const data = await response.json();
        setSetupData(data);
      } else {
        const data = await response.json();
        setMessage({ type: 'error', text: data.error || data.detail || 'Failed to setup 2FA' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error' });
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const response = await api.fetch('/2fa/enable', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: verificationCode })
      });

      if (response.ok) {
        setStep(3);
      } else {
        const data = await response.json();
        setMessage({ type: 'error', text: data.error || data.detail || 'Invalid code' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error' });
    } finally {
      setLoading(false);
    }
  };

  const copyBackupCodes = () => {
    if (setupData?.backup_codes) {
      navigator.clipboard.writeText(setupData.backup_codes.join('\n'));
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    }
  };

  const handleClose = () => {
    if (step === 3) {
      onComplete?.();
    }
    onClose();
    setStep(1);
    setSetupData(null);
    setVerificationCode('');
    setMessage({ type: '', text: '' });
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content modal-2fa" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3><Shield size={20} /> {step === 3 ? 'Backup Codes' : 'Setup Two-Factor Authentication'}</h3>
          <button className="modal-close" onClick={handleClose}><X size={20} /></button>
        </div>

        {loading && !setupData ? (
          <div className="modal-loading">Setting up 2FA...</div>
        ) : step === 1 && setupData ? (
          <div className="two-factor-setup">
            <p>Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)</p>
            <div className="qr-code-container">
              <img src={setupData.qr_code} alt="2FA QR Code" />
            </div>
            <p className="manual-entry">
              Or enter this code manually: <code>{setupData.secret}</code>
            </p>
            <button className="btn-primary" onClick={() => setStep(2)}>
              I've scanned the code
            </button>
          </div>
        ) : step === 2 ? (
          <form onSubmit={handleVerify} className="two-factor-verify">
            <p>Enter the 6-digit code from your authenticator app to verify setup:</p>
            <input
              type="text"
              value={verificationCode}
              onChange={e => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              maxLength={6}
              className="verification-input"
              autoFocus
            />
            {message.text && (
              <div className={`message ${message.type}`}>
                <AlertTriangle size={16} /> {message.text}
              </div>
            )}
            <div className="modal-actions">
              <button type="button" className="btn-secondary" onClick={() => setStep(1)}>Back</button>
              <button type="submit" className="btn-primary" disabled={loading || verificationCode.length !== 6}>
                {loading ? 'Verifying...' : 'Verify & Enable'}
              </button>
            </div>
          </form>
        ) : step === 3 && setupData ? (
          <div className="backup-codes">
            <div className="backup-codes-warning">
              <AlertTriangle size={20} />
              <p>Save these backup codes in a secure place. You can use them to access your account if you lose your authenticator device.</p>
            </div>
            <div className="backup-codes-list">
              {setupData.backup_codes.map((code, i) => (
                <code key={i}>{code}</code>
              ))}
            </div>
            <button className="btn-secondary" onClick={copyBackupCodes}>
              {copiedCode ? <><Check size={16} /> Copied!</> : <><Copy size={16} /> Copy Codes</>}
            </button>
            <button className="btn-primary" onClick={handleClose}>
              I've saved my backup codes
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default TwoFactorSetupModal;
