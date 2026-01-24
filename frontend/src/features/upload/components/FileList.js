/**
 * FileList - Queue of uploaded files with status
 */

import React from 'react';
import { Trash2, CheckCircle, XCircle } from 'lucide-react';
import FileCard from './FileCard';

import './FileList.css';

/**
 * FileList Component
 * @param {object} props
 * @param {Array} props.files - Array of queued files
 * @param {function} props.onRemove - Remove file callback
 * @param {function} props.onRetry - Retry failed file callback
 * @param {function} props.onClearCompleted - Clear completed files
 * @param {function} props.onClearAll - Clear all files
 * @param {boolean} props.isProcessing - Whether queue is processing
 * @param {function} props.onSetCustomPrompt - Set per-file custom prompt
 */
function FileList({
  files,
  onRemove,
  onRetry,
  onClearCompleted,
  onClearAll,
  isProcessing,
  onSetCustomPrompt
}) {
  const completedCount = files.filter(f => f.status === 'completed').length;
  const failedCount = files.filter(f => f.status === 'failed').length;
  const hasCompleted = completedCount > 0;
  const hasFailed = failedCount > 0;

  return (
    <div className="file-list">
      {/* Header */}
      <div className="file-list-header">
        <h3 className="file-list-title">
          Files ({files.length})
        </h3>
        <div className="file-list-actions">
          {hasCompleted && (
            <button
              className="file-list-action"
              onClick={onClearCompleted}
              title="Clear completed"
            >
              <CheckCircle size={16} />
              Clear done
            </button>
          )}
          {!isProcessing && files.length > 0 && (
            <button
              className="file-list-action file-list-action-danger"
              onClick={onClearAll}
              title="Clear all"
            >
              <Trash2 size={16} />
              Clear all
            </button>
          )}
        </div>
      </div>

      {/* Status summary */}
      {(hasCompleted || hasFailed) && (
        <div className="file-list-summary">
          {hasCompleted && (
            <span className="summary-badge summary-success">
              <CheckCircle size={14} />
              {completedCount} completed
            </span>
          )}
          {hasFailed && (
            <span className="summary-badge summary-error">
              <XCircle size={14} />
              {failedCount} failed
            </span>
          )}
        </div>
      )}

      {/* File cards */}
      <div className="file-list-items">
        {files.map(file => (
          <FileCard
            key={file.id}
            file={file}
            onRemove={() => onRemove(file.id)}
            onRetry={() => onRetry(file.id)}
            onSetCustomPrompt={onSetCustomPrompt}
          />
        ))}
      </div>
    </div>
  );
}

export default FileList;
