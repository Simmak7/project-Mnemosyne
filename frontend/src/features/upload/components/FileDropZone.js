/**
 * FileDropZone - Multi-file drag & drop component
 * Supports both drag-drop and click-to-browse
 */

import React, { useState, useRef, useCallback } from 'react';
import { Upload, Image, FileText, Plus } from 'lucide-react';
import { getAcceptString, validateFiles } from '../utils/fileValidation';
import { UPLOAD_FLAGS } from '../utils/featureFlags';

import './FileDropZone.css';

/**
 * FileDropZone Component
 * @param {object} props
 * @param {function} props.onFilesAdded - Callback when files are added
 * @param {boolean} props.disabled - Whether drop zone is disabled
 */
function FileDropZone({ onFilesAdded, disabled = false }) {
  const [dragActive, setDragActive] = useState(false);
  const [recentRejects, setRecentRejects] = useState([]);
  const fileInputRef = useRef(null);

  // Handle drag events
  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setDragActive(true);
  }, [disabled]);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  // Handle file drop
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (disabled) return;

    const droppedFiles = e.dataTransfer?.files;
    if (droppedFiles && droppedFiles.length > 0) {
      processFiles(droppedFiles);
    }
  }, [disabled]);

  // Handle file input change
  const handleFileChange = useCallback((e) => {
    const selectedFiles = e.target.files;
    if (selectedFiles && selectedFiles.length > 0) {
      processFiles(selectedFiles);
    }
    // Reset input so same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  // Process selected files
  const processFiles = useCallback((files) => {
    // Limit to single file if multi-file disabled
    const filesToProcess = UPLOAD_FLAGS.MULTI_FILE_UPLOAD
      ? files
      : [files[0]];

    const result = onFilesAdded?.(filesToProcess);

    // Show rejected files briefly
    if (result?.rejected?.length > 0) {
      setRecentRejects(result.rejected);
      setTimeout(() => setRecentRejects([]), 5000);
    }
  }, [onFilesAdded]);

  // Handle click to browse
  const handleClick = useCallback(() => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  }, [disabled]);

  // Handle keyboard interaction
  const handleKeyDown = useCallback((e) => {
    if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
      e.preventDefault();
      fileInputRef.current?.click();
    }
  }, [disabled]);

  return (
    <div className="file-drop-zone-container">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept={getAcceptString()}
        multiple={UPLOAD_FLAGS.MULTI_FILE_UPLOAD}
        onChange={handleFileChange}
        disabled={disabled}
        className="file-input-hidden"
        aria-label="File input"
      />

      {/* Drop Zone */}
      <div
        className={`file-drop-zone ng-glass ${dragActive ? 'drag-active' : ''} ${disabled ? 'disabled' : ''}`}
        onClick={handleClick}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onKeyDown={handleKeyDown}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="Drop files here or click to browse"
      >
        <div className="drop-zone-content">
          <div className="drop-zone-icon-container">
            <Upload className="drop-zone-icon primary" size={48} />
            <Plus className="drop-zone-icon-plus" size={20} />
          </div>

          <div className="drop-zone-text">
            <p className="drop-zone-title">
              {dragActive ? 'Drop files here' : 'Drop files or click to upload'}
            </p>
            <p className="drop-zone-subtitle">
              {UPLOAD_FLAGS.MULTI_FILE_UPLOAD
                ? 'Select multiple images or PDFs at once'
                : 'Select a file to analyze'
              }
            </p>
          </div>

          <div className="drop-zone-types">
            <span className="type-badge">
              <Image size={14} />
              Images
            </span>
            {UPLOAD_FLAGS.DOCUMENT_SUPPORT && (
              <span className="type-badge">
                <FileText size={14} />
                Documents
              </span>
            )}
          </div>

          <p className="drop-zone-limit">
            Images: 10MB max • PDFs: 50MB max • JPG, PNG, GIF, WebP, PDF
          </p>
        </div>
      </div>

      {/* Rejection messages */}
      {recentRejects.length > 0 && (
        <div className="drop-zone-rejects">
          {recentRejects.map((reject, index) => (
            <div key={index} className="reject-message">
              <span className="reject-file">{reject.file.name}</span>
              <span className="reject-error">{reject.error}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default FileDropZone;
