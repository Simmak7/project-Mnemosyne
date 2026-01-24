/**
 * UploadLayout - Main 2-panel container for Neural Studio
 * Left: File management (drop zone + queue)
 * Right: Analysis configuration
 */

import React, { useCallback } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { Upload, Sparkles } from 'lucide-react';

import FileDropZone from './FileDropZone';
import FileList from './FileList';
import AnalysisConfig from './AnalysisConfig';
import AlbumSelector from './AlbumSelector';

import { useUploadQueue } from '../hooks/useUploadQueue';
import { useAnalysisConfig } from '../hooks/useAnalysisConfig';

import './UploadLayout.css';

/**
 * UploadLayout Component
 * @param {object} props
 * @param {function} props.onUploadSuccess - Callback when a file completes
 */
function UploadLayout({ onUploadSuccess }) {
  // Upload queue state
  const {
    files,
    isProcessing,
    pendingCount,
    completedCount,
    failedCount,
    totalCount,
    addFiles,
    removeFile,
    clearCompleted,
    clearAll,
    processQueue,
    stopProcessing,
    retryFile,
    setFileCustomPrompt
  } = useUploadQueue({
    onUploadSuccess: (file, result) => {
      onUploadSuccess?.(result);
    }
  });

  // Analysis config state
  const {
    config,
    setUserPrompt,
    setModel,
    setPreset,
    toggleAdvanced,
    setAnalysisDepth,
    setAutoTagging,
    setMaxTags,
    setTargetAlbum,
    setAutoCreateNote,
    resetConfig,
    isModified,
    getConfigSummary
  } = useAnalysisConfig();

  // Handle file drop/selection
  const handleFilesAdded = useCallback((newFiles) => {
    const result = addFiles(newFiles);

    if (result.rejected.length > 0) {
      // Could show toast notification here
      console.warn('Some files were rejected:', result.rejected);
    }

    return result;
  }, [addFiles]);

  // Handle analyze button click
  const handleAnalyze = useCallback(() => {
    if (pendingCount > 0) {
      processQueue(config);
    }
  }, [pendingCount, processQueue, config]);

  // Handle stop button click
  const handleStop = useCallback(() => {
    stopProcessing();
  }, [stopProcessing]);

  // Handle retry - reset file and auto-process
  const handleRetry = useCallback((fileId) => {
    retryFile(fileId);
    // Use setTimeout to ensure state update happens first
    setTimeout(() => {
      processQueue(config);
    }, 0);
  }, [retryFile, processQueue, config]);

  return (
    <div className="upload-layout ng-theme">
      {/* Header */}
      <div className="upload-header">
        <div className="upload-header-title">
          <Sparkles className="upload-header-icon" size={24} />
          <h1>Neural Studio</h1>
        </div>
        <p className="upload-header-subtitle">
          Upload images for AI-powered analysis and note generation
        </p>
      </div>

      {/* Main content - 2 panel layout */}
      <PanelGroup direction="horizontal" className="upload-panel-group">
        {/* Left Panel - File Management */}
        <Panel
          defaultSize={60}
          minSize={40}
          maxSize={75}
          className="upload-panel upload-files-panel"
          id="upload-files"
        >
          <div className="upload-files-content">
            {/* Drop Zone */}
            <FileDropZone
              onFilesAdded={handleFilesAdded}
              disabled={isProcessing}
            />

            {/* File Queue */}
            {totalCount > 0 && (
              <FileList
                files={files}
                onRemove={removeFile}
                onRetry={handleRetry}
                onClearCompleted={clearCompleted}
                onClearAll={clearAll}
                isProcessing={isProcessing}
                onSetCustomPrompt={setFileCustomPrompt}
              />
            )}
          </div>
        </Panel>

        <PanelResizeHandle className="upload-resize-handle" />

        {/* Right Panel - Configuration */}
        <Panel
          defaultSize={40}
          minSize={25}
          maxSize={50}
          className="upload-panel upload-config-panel"
          id="upload-config"
        >
          <AnalysisConfig
            config={config}
            onUserPromptChange={setUserPrompt}
            onModelChange={setModel}
            onPresetChange={setPreset}
            onToggleAdvanced={toggleAdvanced}
            onDepthChange={setAnalysisDepth}
            onAutoTaggingChange={setAutoTagging}
            onMaxTagsChange={setMaxTags}
            onAutoCreateNoteChange={setAutoCreateNote}
            onReset={resetConfig}
            isModified={isModified()}
            configSummary={getConfigSummary()}
            albumPicker={
              <AlbumSelector
                selectedAlbumId={config.targetAlbumId}
                onAlbumChange={setTargetAlbum}
              />
            }
          />

          {/* Action Button */}
          <div className="upload-actions">
            {isProcessing ? (
              <button
                className="upload-action-btn upload-stop-btn"
                onClick={handleStop}
              >
                <span className="upload-btn-spinner" />
                Stop Processing
              </button>
            ) : (
              <button
                className="upload-action-btn upload-analyze-btn"
                onClick={handleAnalyze}
                disabled={pendingCount === 0}
              >
                <Upload size={20} />
                {pendingCount > 0
                  ? `Analyze ${pendingCount} File${pendingCount > 1 ? 's' : ''}`
                  : 'Add files to analyze'
                }
              </button>
            )}

            {/* Status summary */}
            {totalCount > 0 && (
              <div className="upload-status-summary">
                {completedCount > 0 && (
                  <span className="status-completed">
                    {completedCount} completed
                  </span>
                )}
                {failedCount > 0 && (
                  <span className="status-failed">
                    {failedCount} failed
                  </span>
                )}
                {isProcessing && pendingCount > 0 && (
                  <span className="status-processing">
                    {pendingCount} remaining
                  </span>
                )}
              </div>
            )}
          </div>
        </Panel>
      </PanelGroup>
    </div>
  );
}

export default UploadLayout;
