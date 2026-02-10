/**
 * Password strength indicator with visual bar and label
 */
import React, { useState, useEffect } from 'react';

const STRENGTH_COLORS = {
  weak: '#ef4444',
  fair: '#f59e0b',
  good: '#10b981',
  strong: '#3b82f6',
  excellent: '#8b5cf6',
};

function PasswordStrengthIndicator({ password }) {
  const [strength, setStrength] = useState({ score: 0, strength: 'weak', feedback: [] });

  useEffect(() => {
    if (!password) {
      setStrength({ score: 0, strength: 'weak', feedback: [] });
      return;
    }

    const checkStrength = async () => {
      try {
        const response = await fetch('http://localhost:8000/check-password-strength', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ password })
        });
        if (response.ok) {
          const data = await response.json();
          setStrength(data);
        }
      } catch (error) {
        console.error('Error checking password strength:', error);
      }
    };

    const debounce = setTimeout(checkStrength, 300);
    return () => clearTimeout(debounce);
  }, [password]);

  const color = STRENGTH_COLORS[strength.strength] || '#6b7280';

  return (
    <div className="password-strength">
      <div className="password-strength-bar">
        <div
          className="password-strength-fill"
          style={{ width: `${strength.score}%`, backgroundColor: color }}
        />
      </div>
      <span className="password-strength-label" style={{ color }}>
        {strength.strength.charAt(0).toUpperCase() + strength.strength.slice(1)}
      </span>
    </div>
  );
}

export default PasswordStrengthIndicator;
