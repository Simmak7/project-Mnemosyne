/**
 * ModelCard - Displays a single model with status, download/remove actions
 */
import React from 'react';
import { Download, Trash2, X, Loader, RefreshCw } from 'lucide-react';

function ModelCard({ model, progress, onPull, onDelete, onCancelPull, updateInfo, onUpdate }) {
  const isDownloading = progress && !['success', 'error'].includes(progress.status);
  const hasError = progress?.status === 'error';
  const isInstalled = model.is_available;
  const hasUpdate = updateInfo?.update_available;

  const categoryColors = {
    fast: 'var(--color-success, #10b981)',
    balanced: 'var(--accent-color, #3b82f6)',
    powerful: 'var(--color-warning, #f59e0b)',
    vision: 'var(--color-info, #8b5cf6)',
  };

  return (
    <div className={`model-card ng-glass-surface ${isInstalled ? 'installed' : ''}`}>
      <div className="model-card-header">
        <div className="model-card-title">
          <span className="model-card-name">{model.name}</span>
          <span
            className="model-card-category"
            style={{ color: categoryColors[model.category] || 'var(--text-secondary)' }}
          >
            {model.category}
          </span>
        </div>
        <span className="model-card-params">{model.parameters}</span>
      </div>

      <p className="model-card-description">{model.description}</p>

      {model.size_gb > 0 && (
        <div className="model-card-size">{model.size_gb} GB</div>
      )}

      {/* Download progress bar */}
      {isDownloading && (
        <div className="model-card-progress">
          <div className="model-progress-bar">
            <div
              className="model-progress-fill"
              style={{ width: `${progress.percent || 0}%` }}
            />
          </div>
          <div className="model-progress-info">
            <span className="model-progress-status">{progress.status}</span>
            <span className="model-progress-percent">{Math.round(progress.percent || 0)}%</span>
          </div>
        </div>
      )}

      {hasError && (
        <div className="model-card-error">{progress.error}</div>
      )}

      {/* Actions */}
      <div className="model-card-actions">
        {isDownloading ? (
          <button
            className="model-btn model-btn-cancel"
            onClick={() => onCancelPull(model.id)}
            title="Cancel download"
          >
            <X size={14} /> Cancel
          </button>
        ) : isInstalled ? (
          <>
            {hasUpdate && (
              <button
                className="model-btn model-btn-update"
                onClick={() => onUpdate(model.id)}
                title="Update to latest version"
              >
                <RefreshCw size={14} /> Update
              </button>
            )}
            <button
              className="model-btn model-btn-remove"
              onClick={() => {
                if (window.confirm(`Remove ${model.name}? You can re-download it later.`)) {
                  onDelete(model.id);
                }
              }}
              title="Remove model"
            >
              <Trash2 size={14} /> Remove
            </button>
          </>
        ) : model.provider === 'ollama' ? (
          <button
            className="model-btn model-btn-download"
            onClick={() => onPull(model.id)}
            title="Download model"
          >
            <Download size={14} /> Download
          </button>
        ) : (
          <span className="model-card-cloud-badge">Cloud</span>
        )}

        {isInstalled && !isDownloading && (
          hasUpdate ? (
            <span className="model-card-update-badge">Update Available</span>
          ) : (
            <span className="model-card-installed-badge">Installed</span>
          )
        )}
      </div>
    </div>
  );
}

export default ModelCard;
