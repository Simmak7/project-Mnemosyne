/**
 * QuickUploadWidget - Drag-and-drop upload widget using existing Studio config
 *
 * Reuses useAnalysisConfig + useUploadQueue from the upload feature.
 */
import React, { useCallback, useRef, useState, useEffect } from 'react';
import { Upload, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import WidgetShell from './WidgetShell';
import { useAnalysisConfig } from '../../upload/hooks/useAnalysisConfig';
import { useUploadQueue, FILE_STATES } from '../../upload/hooks/useUploadQueue';
import './QuickUploadWidget.css';

function QuickUploadWidget({ onTabChange, onUploadSuccess }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef(null);
  const { config } = useAnalysisConfig();

  const handleSuccess = useCallback(() => {
    onUploadSuccess?.();
  }, [onUploadSuccess]);

  const { files, addFiles, processQueue, isProcessing, pendingCount, completedCount, failedCount } =
    useUploadQueue({ onUploadSuccess: handleSuccess });

  // Auto-process when new pending files appear
  useEffect(() => {
    if (pendingCount > 0 && !isProcessing) {
      processQueue(config);
    }
  }, [pendingCount, isProcessing, processQueue, config]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
    const dropped = e.dataTransfer?.files;
    if (dropped?.length) {
      addFiles(dropped);
    }
  }, [addFiles]);

  const handleFileSelect = useCallback((e) => {
    const selected = e.target.files;
    if (selected?.length) {
      addFiles(selected);
    }
    if (inputRef.current) inputRef.current.value = '';
  }, [addFiles]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const activeFile = files.find(f =>
    f.status === FILE_STATES.UPLOADING || f.status === FILE_STATES.PROCESSING
  );

  return (
    <WidgetShell
      icon={Upload}
      title="Quick Upload"
      action={() => onTabChange('upload')}
      actionLabel="Open Studio"
    >
      <div
        className={`quick-upload-zone ${isDragOver ? 'quick-upload-zone--active' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept="image/*,application/pdf"
          onChange={handleFileSelect}
          className="quick-upload-input"
        />
        {isProcessing && activeFile ? (
          <div className="quick-upload-status">
            <Loader size={20} className="quick-upload-spinner" />
            <span className="quick-upload-status-text">
              Processing {activeFile.name}...
            </span>
          </div>
        ) : (
          <div className="quick-upload-prompt">
            <Upload size={20} className="quick-upload-icon" />
            <span>Drop files or click to upload</span>
          </div>
        )}
      </div>

      {(completedCount > 0 || failedCount > 0) && (
        <div className="quick-upload-results">
          {completedCount > 0 && (
            <span className="quick-upload-result quick-upload-result--success">
              <CheckCircle size={12} /> {completedCount} done
            </span>
          )}
          {failedCount > 0 && (
            <span className="quick-upload-result quick-upload-result--error">
              <AlertCircle size={12} /> {failedCount} failed
            </span>
          )}
        </div>
      )}
    </WidgetShell>
  );
}

export default QuickUploadWidget;
