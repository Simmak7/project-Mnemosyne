/**
 * AIStatusIndicator - Shows Ollama/AI service health status.
 *
 * Displays a colored dot (green/amber/red/gray) with a tooltip/popover
 * showing detailed component status. Polls GET /health every 30 seconds.
 *
 * States:
 * - Green  + "AI Ready"    : Ollama connected, all healthy
 * - Amber  + "AI Degraded" : Ollama timeout or partial failure
 * - Red    + "AI Offline"  : Ollama disconnected
 * - Gray   + "Checking..." : Initial load / polling
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Activity, Wifi, WifiOff, AlertTriangle, Loader2 } from 'lucide-react';
import { API_URL } from '../../utils/api';
import './AIStatusIndicator.css';

const POLL_INTERVAL = 30000; // 30 seconds

function deriveStatus(data) {
  if (!data) return { level: 'checking', label: 'Checking...', icon: Loader2 };

  const ollama = data.components?.ollama;
  const overall = data.status;

  if (overall === 'unhealthy') {
    return { level: 'offline', label: 'System Offline', icon: WifiOff };
  }
  if (ollama === 'disconnected') {
    return { level: 'offline', label: 'AI Offline', icon: WifiOff };
  }
  if (ollama === 'timeout' || overall === 'degraded') {
    return { level: 'degraded', label: 'AI Degraded', icon: AlertTriangle };
  }
  if (ollama === 'connected' && (overall === 'healthy' || overall === 'degraded')) {
    // If overall is degraded but ollama is connected, AI itself is fine
    if (overall === 'healthy') {
      return { level: 'healthy', label: 'AI Ready', icon: Wifi };
    }
    return { level: 'degraded', label: 'AI Ready (System Degraded)', icon: Activity };
  }

  return { level: 'healthy', label: 'AI Ready', icon: Wifi };
}

function AIStatusIndicator() {
  const [healthData, setHealthData] = useState(null);
  const [showPopover, setShowPopover] = useState(false);
  const [error, setError] = useState(false);
  const popoverRef = useRef(null);
  const buttonRef = useRef(null);

  const fetchHealth = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/health`, {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setHealthData(data);
        setError(false);
      } else {
        setError(true);
        setHealthData(null);
      }
    } catch {
      setError(true);
      setHealthData(null);
    }
  }, []);

  // Initial fetch and polling
  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  // Close popover on outside click
  useEffect(() => {
    if (!showPopover) return;
    const handleClick = (e) => {
      if (
        popoverRef.current && !popoverRef.current.contains(e.target) &&
        buttonRef.current && !buttonRef.current.contains(e.target)
      ) {
        setShowPopover(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [showPopover]);

  const status = error
    ? { level: 'offline', label: 'AI Offline', icon: WifiOff }
    : deriveStatus(healthData);

  const StatusIcon = status.icon;

  return (
    <div className="ai-status-wrapper">
      <button
        ref={buttonRef}
        className="ai-status-btn"
        onClick={() => setShowPopover(!showPopover)}
        aria-label={`AI Status: ${status.label}`}
        aria-expanded={showPopover}
        title={status.label}
      >
        <span className={`ai-status-dot ai-status-${status.level}`} />
        <span className="ai-status-label">{status.label}</span>
      </button>

      {showPopover && (
        <div ref={popoverRef} className="ai-status-popover" role="dialog">
          <div className="ai-status-popover-header">
            <StatusIcon size={16} />
            <span>{status.label}</span>
          </div>

          {healthData?.components && (
            <div className="ai-status-components">
              {Object.entries(healthData.components).map(([name, value]) => (
                <div key={name} className="ai-status-row">
                  <span className="ai-status-component-name">{name}</span>
                  <span className={`ai-status-component-value ai-cv-${value}`}>
                    {value}
                  </span>
                </div>
              ))}
            </div>
          )}

          {healthData?.version && (
            <div className="ai-status-version">
              v{healthData.version}
              {healthData.build ? ` (build ${healthData.build})` : ''}
            </div>
          )}

          {error && (
            <p className="ai-status-error-msg">
              Cannot reach the backend server. Check that the service is running.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default React.memo(AIStatusIndicator);
