/**
 * UploadLayout - Main 2-panel container for Neural Studio
 * Left: File management (drop zone + queue)
 * Right: Analysis configuration
 */

import React, { useCallback, useMemo, useState } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { Upload, FolderOpen, Settings } from 'lucide-react';

import { useIsMobile } from '../../../hooks/useIsMobile';
import { useSwipeNavigation } from '../../../hooks/useSwipeNavigation';
import MobilePanelTabs from '../../../components/MobilePanelTabs';
import FileDropZone from './FileDropZone';
import FileList from './FileList';
import AnalysisConfig from './AnalysisConfig';
import AlbumSelector from './AlbumSelector';

import { useUploadQueue } from '../hooks/useUploadQueue';
import { useAnalysisConfig } from '../hooks/useAnalysisConfig';
import { useToast } from '../../../components/toast/ToastProvider';

import './UploadLayout.css';

const MOBILE_PANELS = [
  { id: 'files', label: 'Files', icon: FolderOpen },
  { id: 'settings', label: 'Settings', icon: Settings },
];

const PANEL_IDS = MOBILE_PANELS.map(p => p.id);

function UploadLayout({ onUploadSuccess, onNavigateToDocument, onNavigateToImage }) {
  const isMobile = useIsMobile();
  const [mobilePanel, setMobilePanel] = useState('files');
  const { showSuccess } = useToast();

  const {
    files, isProcessing, pendingCount, completedCount, failedCount, totalCount,
    addFiles, removeFile, clearCompleted, clearAll, processQueue, stopProcessing,
    retryFile, setFileCustomPrompt
  } = useUploadQueue({
    onUploadSuccess: (file, result) => {
      onUploadSuccess?.(result);
      if (file.isDocument) {
        const docId = file.documentId;
        showSuccess('Document processed!', {
          description: 'PDF is ready for AI review.',
          action: { label: 'View Document \u2192', onClick: () => { window.location.hash = `#/documents${docId ? '/' + docId : ''}`; } }
        });
      } else {
        showSuccess('Image analyzed!', {
          description: 'AI created a note from your photo.',
          action: { label: 'View Note \u2192', onClick: () => { window.location.hash = '#/notes'; } }
        });
      }
    }
  });

  const {
    config, setUserPrompt, setModel, setPreset, toggleAdvanced,
    setAnalysisDepth, setAutoTagging, setMaxTags, setTargetAlbum,
    setAutoCreateNote, resetConfig, isModified, getConfigSummary, visionModel
  } = useAnalysisConfig();

  const hasPdfs = useMemo(() => files.some(f => f.file?.type === 'application/pdf'), [files]);
  const hasImages = useMemo(() => files.some(f => f.file?.type?.startsWith('image/')), [files]);

  const swipeHandlers = useSwipeNavigation(PANEL_IDS, mobilePanel, setMobilePanel);

  const handleFilesAdded = useCallback((newFiles) => {
    const result = addFiles(newFiles);
    if (result.rejected.length > 0) {
      console.warn('Some files were rejected:', result.rejected);
    }
    return result;
  }, [addFiles]);

  const handleAnalyze = useCallback(() => {
    if (pendingCount > 0) processQueue(config);
  }, [pendingCount, processQueue, config]);

  const handleStop = useCallback(() => { stopProcessing(); }, [stopProcessing]);

  const handleRetry = useCallback((fileId) => {
    retryFile(fileId);
    setTimeout(() => { processQueue(config); }, 0);
  }, [retryFile, processQueue, config]);

  const filesContent = (
    <div className="upload-files-content">
      <FileDropZone onFilesAdded={handleFilesAdded} disabled={isProcessing} />
      {totalCount > 0 && (
        <FileList
          files={files} onRemove={removeFile} onRetry={handleRetry}
          onClearCompleted={clearCompleted} onClearAll={clearAll}
          isProcessing={isProcessing} onSetCustomPrompt={setFileCustomPrompt}
          onNavigateToDocument={onNavigateToDocument} onNavigateToImage={onNavigateToImage}
        />
      )}
    </div>
  );

  const configContent = (
    <>
      <AnalysisConfig
        config={config} visionModel={visionModel} hasPdfs={hasPdfs} hasImages={hasImages}
        onUserPromptChange={setUserPrompt} onModelChange={setModel} onPresetChange={setPreset}
        onToggleAdvanced={toggleAdvanced} onDepthChange={setAnalysisDepth}
        onAutoTaggingChange={setAutoTagging} onMaxTagsChange={setMaxTags}
        onAutoCreateNoteChange={setAutoCreateNote} onReset={resetConfig}
        isModified={isModified()} configSummary={getConfigSummary()}
        albumPicker={<AlbumSelector selectedAlbumId={config.targetAlbumId} onAlbumChange={setTargetAlbum} />}
      />
      <div className="upload-actions">
        {isProcessing ? (
          <button className="upload-action-btn upload-stop-btn" onClick={handleStop}>
            <span className="upload-btn-spinner" /> Stop Processing
          </button>
        ) : (
          <button className="upload-action-btn upload-analyze-btn" onClick={handleAnalyze} disabled={pendingCount === 0}>
            <Upload size={20} />
            {pendingCount > 0 ? `Analyze ${pendingCount} File${pendingCount > 1 ? 's' : ''}` : 'Add files to analyze'}
          </button>
        )}
        {totalCount > 0 && (
          <div className="upload-status-summary">
            {completedCount > 0 && <span className="status-completed">{completedCount} completed</span>}
            {failedCount > 0 && <span className="status-failed">{failedCount} failed</span>}
            {isProcessing && pendingCount > 0 && <span className="status-processing">{pendingCount} remaining</span>}
          </div>
        )}
      </div>
    </>
  );

  // Mobile layout
  if (isMobile) {
    return (
      <div className="upload-layout ng-theme upload-layout--mobile">
        <div className="upload-header">
          <div className="upload-header-title"><h1>Upload</h1></div>
          <p className="upload-header-subtitle">Upload images and documents for AI-powered analysis</p>
        </div>
        <MobilePanelTabs panels={MOBILE_PANELS} activePanel={mobilePanel} onPanelChange={setMobilePanel} />
        <div className="upload-mobile-content" {...swipeHandlers}>
          {mobilePanel === 'files' && (
            <>
              {filesContent}
              {totalCount > 0 && (
                <div className="upload-actions upload-actions--mobile">
                  {isProcessing ? (
                    <button className="upload-action-btn upload-stop-btn" onClick={handleStop}>
                      <span className="upload-btn-spinner" /> Stop Processing
                    </button>
                  ) : (
                    <button className="upload-action-btn upload-analyze-btn" onClick={handleAnalyze} disabled={pendingCount === 0}>
                      <Upload size={20} />
                      {pendingCount > 0 ? `Analyze ${pendingCount} File${pendingCount > 1 ? 's' : ''}` : 'Add files to analyze'}
                    </button>
                  )}
                </div>
              )}
            </>
          )}
          {mobilePanel === 'settings' && configContent}
        </div>
      </div>
    );
  }

  // Desktop layout (unchanged)
  return (
    <div className="upload-layout ng-theme">
      <div className="upload-header">
        <div className="upload-header-title"><h1>Upload</h1></div>
        <p className="upload-header-subtitle">Upload images and documents for AI-powered analysis and note generation</p>
      </div>
      <PanelGroup direction="horizontal" className="upload-panel-group">
        <Panel defaultSize={60} minSize={40} maxSize={75} className="upload-panel upload-files-panel" id="upload-files">
          {filesContent}
        </Panel>
        <PanelResizeHandle className="upload-resize-handle" />
        <Panel defaultSize={40} minSize={25} maxSize={50} className="upload-panel upload-config-panel" id="upload-config">
          {configContent}
        </Panel>
      </PanelGroup>
    </div>
  );
}

export default UploadLayout;
