/**
 * FileCard - Individual file in the queue with status
 */

import React, { useState } from 'react';
import {
  Image,
  FileText,
  X,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Loader2,
  MessageSquare,
  ChevronDown,
  ChevronRight,
  ArrowRight
} from 'lucide-react';
import { formatFileSize, getFileTypeInfo } from '../utils/fileValidation';
import { FILE_STATES } from '../hooks/useUploadQueue';
import { UPLOAD_FLAGS } from '../utils/featureFlags';

import './FileCard.css';

/**
 * Get status icon and color
 * @param {string} status - File status
 * @param {boolean} isSlow - Whether AI is taking longer than expected
 */
function getStatusDisplay(status, isSlow = false) {
  switch (status) {
    case FILE_STATES.PENDING:
      return { icon: null, color: 'secondary', label: 'Ready' };
    case FILE_STATES.UPLOADING:
      return { icon: Loader2, color: 'ai', label: 'Uploading...' };
    case FILE_STATES.PROCESSING:
      return {
        icon: Loader2,
        color: isSlow ? 'warning' : 'ai',
        label: isSlow ? 'Analyzing (slow)...' : 'Analyzing...'
      };
    case FILE_STATES.COMPLETED:
      return { icon: CheckCircle, color: 'success', label: 'Done' };
    case 'needs_review':
      return { icon: AlertCircle, color: 'warning', label: 'Needs Review' };
    case FILE_STATES.FAILED:
      return { icon: AlertCircle, color: 'error', label: 'Failed' };
    default:
      return { icon: null, color: 'secondary', label: status };
  }
}

/**
 * Get file type icon
 */
function getFileIcon(type) {
  if (type === 'application/pdf') return FileText;
  if (type.startsWith('image/')) return Image;
  return FileText;
}

/**
 * FileCard Component
 * @param {object} props
 * @param {object} props.file - File object from queue
 * @param {function} props.onRemove - Remove callback
 * @param {function} props.onRetry - Retry callback (for failed files)
 * @param {function} props.onSetCustomPrompt - Set per-file custom prompt
 */
function FileCard({ file, onRemove, onRetry, onSetCustomPrompt, onNavigateToDocument, onNavigateToImage }) {
  const { name, size, type, status, progress, error, isSlow, customPrompt, useCustomPrompt } = file;
  const statusDisplay = getStatusDisplay(status, isSlow);
  const FileIcon = getFileIcon(type);
  const StatusIcon = statusDisplay.icon;

  const [showPromptInput, setShowPromptInput] = useState(false);
  const [promptValue, setPromptValue] = useState(customPrompt || '');

  const isActive = status === FILE_STATES.UPLOADING || status === FILE_STATES.PROCESSING;
  const isFailed = status === FILE_STATES.FAILED;
  const isCompleted = status === FILE_STATES.COMPLETED;
  const isPending = status === FILE_STATES.PENDING;
  const canEditPrompt = isPending && UPLOAD_FLAGS.PER_FILE_CONFIG;
  const canNavigateToDoc = isCompleted && file.isDocument && file.documentId && onNavigateToDocument;
  const canNavigateToImage = isCompleted && !file.isDocument && file.imageId && onNavigateToImage;
  const canNavigate = canNavigateToDoc || canNavigateToImage;

  const handlePromptSave = () => {
    if (onSetCustomPrompt) {
      const trimmed = promptValue.trim();
      onSetCustomPrompt(file.id, trimmed, trimmed.length > 0);
    }
    setShowPromptInput(false);
  };

  const handlePromptClear = () => {
    setPromptValue('');
    if (onSetCustomPrompt) {
      onSetCustomPrompt(file.id, '', false);
    }
    setShowPromptInput(false);
  };

  const handleCardClick = () => {
    if (canNavigateToDoc) onNavigateToDocument(file.documentId);
    else if (canNavigateToImage) onNavigateToImage(file.imageId);
  };

  return (
    <div
      className={`file-card ng-glass-interactive status-${statusDisplay.color}${canNavigate ? ' file-card-clickable' : ''}`}
      onClick={handleCardClick}
      title={canNavigateToDoc ? 'Open in Documents' : canNavigateToImage ? 'Open in Gallery' : undefined}
    >
      {/* File icon */}
      <div className="file-card-icon">
        <FileIcon size={24} />
      </div>

      {/* File info */}
      <div className="file-card-info">
        <div className="file-card-name" title={name}>
          {name}
        </div>
        <div className="file-card-meta">
          <span className="file-card-size">{formatFileSize(size)}</span>
          <span className="file-card-status">
            {StatusIcon && (
              <StatusIcon
                size={14}
                className={isActive ? 'spinning' : ''}
              />
            )}
            {statusDisplay.label}
          </span>
          {/* Navigate hint for completed documents */}
          {canNavigateToDoc && (
            <span className="file-card-navigate-hint">
              Open in Documents <ArrowRight size={12} />
            </span>
          )}
          {/* Navigate hint for completed images */}
          {canNavigateToImage && (
            <span className="file-card-navigate-hint file-card-navigate-hint-image">
              Open in Gallery <ArrowRight size={12} />
            </span>
          )}
          {/* Per-file prompt indicator */}
          {useCustomPrompt && customPrompt && (
            <span className="file-card-custom-prompt-badge" title={customPrompt}>
              <MessageSquare size={12} />
              Custom
            </span>
          )}
        </div>

        {/* Error message */}
        {isFailed && error && (
          <div className="file-card-error">
            {error}
          </div>
        )}

        {/* Per-file prompt toggle and input */}
        {canEditPrompt && (
          <div className="file-card-prompt-section">
            <button
              className={`file-card-prompt-toggle ${useCustomPrompt ? 'has-custom' : ''}`}
              onClick={() => setShowPromptInput(!showPromptInput)}
            >
              {showPromptInput ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              <MessageSquare size={14} />
              <span>
                {useCustomPrompt
                  ? 'Custom instructions (overrides global)'
                  : 'Override global instructions'}
              </span>
            </button>

            {showPromptInput && (
              <div className="file-card-prompt-input-container">
                <textarea
                  className="file-card-prompt-input"
                  value={promptValue}
                  onChange={(e) => setPromptValue(e.target.value)}
                  placeholder="Instructions for this file only (replaces global instructions)..."
                  rows={2}
                  autoFocus
                />
                <div className="file-card-prompt-actions">
                  <button
                    className="file-card-prompt-btn file-card-prompt-save"
                    onClick={handlePromptSave}
                    disabled={!promptValue.trim() && !useCustomPrompt}
                  >
                    {useCustomPrompt ? 'Update' : 'Apply'}
                  </button>
                  {useCustomPrompt && (
                    <button
                      className="file-card-prompt-btn file-card-prompt-clear"
                      onClick={handlePromptClear}
                    >
                      Use global
                    </button>
                  )}
                  <button
                    className="file-card-prompt-btn file-card-prompt-cancel"
                    onClick={() => {
                      setShowPromptInput(false);
                      setPromptValue(customPrompt || '');
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Progress bar */}
      {isActive && (
        <div className="file-card-progress">
          <div
            className="file-card-progress-bar"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {/* Actions */}
      <div className="file-card-actions">
        {isFailed && (
          <button
            className="file-card-action file-card-retry"
            onClick={onRetry}
            title="Retry"
          >
            <RefreshCw size={16} />
          </button>
        )}
        {!isActive && (
          <button
            className="file-card-action file-card-remove"
            onClick={onRemove}
            title="Remove"
          >
            <X size={16} />
          </button>
        )}
      </div>
    </div>
  );
}

export default FileCard;
