/**
 * Data settings section - GDPR data export functionality
 *
 * Self-contained component that manages export jobs:
 * POST /settings/export-data, GET status polling, blob download.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Database, Download, Loader2, CheckCircle,
  AlertCircle, FileArchive, RefreshCw
} from 'lucide-react';
import { api } from '../../../utils/api';

const STATUS_TEXT = {
  0: 'Preparing export...',
  10: 'Exporting notes...',
  40: 'Exporting images...',
  70: 'Exporting tags & activity...',
  90: 'Creating archive...',
};

function getStatusText(progress) {
  const thresholds = [90, 70, 40, 10, 0];
  for (const t of thresholds) {
    if (progress >= t) return STATUS_TEXT[t];
  }
  return 'Preparing export...';
}

function formatBytes(bytes) {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

function DataSection() {
  const [options, setOptions] = useState({
    include_notes: true,
    include_images: true,
    include_tags: true,
    include_activity: false,
  });
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const pollRef = useRef(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const startPolling = useCallback((jobId) => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const status = await api.get(`/settings/export-data/${jobId}`);
        setJob(status);
        if (!['pending', 'processing'].includes(status.status)) {
          stopPolling();
          if (status.status === 'failed') {
            setError(status.error_message || 'Export failed');
          }
        }
      } catch {
        stopPolling();
        setError('Failed to check export status');
      }
    }, 2000);
  }, [stopPolling]);

  useEffect(() => {
    (async () => {
      try {
        const data = await api.get('/settings/export-data/history?limit=1');
        if (data.jobs?.length > 0) {
          const latest = data.jobs[0];
          if (['pending', 'processing'].includes(latest.status)) {
            setJob(latest);
            startPolling(latest.job_id);
          } else if (latest.status === 'completed') {
            setJob(latest);
          }
        }
      } catch { /* history not critical */ }
    })();
    return stopPolling;
  }, [startPolling, stopPolling]);

  async function handleExport() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.post('/settings/export-data', options);
      setJob(data);
      startPolling(data.job_id);
    } catch (err) {
      setError(err.message || 'Failed to start export');
    } finally {
      setLoading(false);
    }
  }

  async function handleDownload() {
    if (!job?.download_url) return;
    try {
      const response = await api.fetch(job.download_url);
      if (!response.ok) throw new Error('Download failed');
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `mnemosyne_export_${job.job_id.slice(0, 8)}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      setError('Failed to download export');
    }
  }

  const isActive = job && ['pending', 'processing'].includes(job.status);
  const isCompleted = job?.status === 'completed';
  const isFailed = job?.status === 'failed';
  const isExpired = job?.status === 'expired';
  const showForm = !job || isFailed || isExpired;

  return (
    <div className="settings-section">
      <div className="settings-section-header">
        <Database size={20} />
        <h3>Data</h3>
      </div>

      {error && (
        <div className="message error">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {showForm && (
        <div className="settings-item">
          <div className="settings-item-info">
            <label>Export your data</label>
            <p>Download a ZIP archive of your data (GDPR compliant). Select what to include:</p>
          </div>
          <div className="export-options">
            {[
              { key: 'include_notes', label: 'Notes' },
              { key: 'include_images', label: 'Images' },
              { key: 'include_tags', label: 'Tags' },
              { key: 'include_activity', label: 'Activity log' },
            ].map(({ key, label }) => (
              <label key={key} className="export-option">
                <input
                  type="checkbox"
                  checked={options[key]}
                  onChange={(e) => setOptions(prev => ({ ...prev, [key]: e.target.checked }))}
                />
                <span>{label}</span>
              </label>
            ))}
          </div>
          <button
            className="btn-primary"
            onClick={handleExport}
            disabled={loading || !Object.values(options).some(Boolean)}
            style={{ marginTop: 12, width: '100%' }}
          >
            {loading ? <><Loader2 size={16} className="spin" /> Starting export...</>
              : <><FileArchive size={16} /> Export My Data</>}
          </button>
        </div>
      )}

      {isActive && (
        <div className="settings-item">
          <div className="settings-item-info">
            <label>Export in progress</label>
          </div>
          <div className="export-progress">
            <div className="export-progress-bar">
              <div className="export-progress-fill" style={{ width: `${job.progress || 0}%` }} />
            </div>
            <p className="export-progress-text">
              <Loader2 size={14} className="spin" />
              {getStatusText(job.progress || 0)} ({job.progress || 0}%)
            </p>
          </div>
        </div>
      )}

      {isCompleted && (
        <div className="settings-item export-completed">
          <div className="settings-item-info">
            <label><CheckCircle size={16} style={{ color: '#10b981' }} /> Export ready</label>
            {job.file_size && <p>Archive size: {formatBytes(job.file_size)}</p>}
            {job.expires_at && (
              <p className="export-expiry">
                Available until {new Date(job.expires_at).toLocaleString()}
              </p>
            )}
          </div>
          <div className="export-actions">
            <button className="btn-primary" onClick={handleDownload}>
              <Download size={16} /> Download ZIP
            </button>
            <button className="btn-secondary" onClick={() => { setJob(null); setError(null); }}>
              <RefreshCw size={14} /> New Export
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default DataSection;
