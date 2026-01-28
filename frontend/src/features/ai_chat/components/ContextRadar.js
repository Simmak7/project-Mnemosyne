/**
 * ContextRadar - Right panel with preview and settings
 *
 * Features:
 * - Preview section showing hovered/clicked citations
 * - Settings section for model configuration
 * - Brain section (placeholder for Phase 5)
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  ChevronRight,
  FileText,
  Image as ImageIcon,
  Settings,
  Brain,
  Sliders,
  ExternalLink,
  X,
  ChevronDown,
  ChevronUp,
  Loader2,
  Database,
  Sparkles,
  Check,
  AlertCircle,
} from 'lucide-react';
import { useAIChatContext } from '../hooks/AIChatContext';
import { useBrain } from '../hooks/useBrain';
import { useMnemosyneBrain } from '../hooks/useMnemosyneBrain';
import './ContextRadar.css';

/**
 * Active Citations list - shows all citations from the latest response
 */
function ActiveCitationsList({ citations, selectedId, onSelect }) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="active-citations">
      <div className="active-citations-header">Sources ({citations.length})</div>
      <div className="active-citations-list">
        {citations.slice(0, 8).map((citation, idx) => (
          <button
            key={`${citation.source_type}-${citation.source_id}-${idx}`}
            className={`citation-item ${selectedId === citation.source_id ? 'selected' : ''} ${citation.source_type}`}
            onClick={() => onSelect(citation)}
            title={citation.title || `${citation.source_type} #${citation.source_id}`}
          >
            {citation.source_type?.startsWith('image') ? (
              <ImageIcon size={12} />
            ) : (
              <FileText size={12} />
            )}
            <span className="citation-title">
              {citation.title || `${citation.source_type} #${citation.source_id}`}
            </span>
            <span className="citation-score">
              {Math.round((citation.relevance_score || 0) * 100)}%
            </span>
          </button>
        ))}
        {citations.length > 8 && (
          <div className="citations-more">+{citations.length - 8} more</div>
        )}
      </div>
    </div>
  );
}

/**
 * Preview section - shows note/image details when citation is clicked
 */
function PreviewSection({ previewItem, activeCitations, onNavigateToNote, onNavigateToImage, onClear, onSelectCitation }) {
  const [noteData, setNoteData] = useState(null);
  const [imageData, setImageData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch preview data when item changes
  useEffect(() => {
    if (!previewItem) {
      setNoteData(null);
      setImageData(null);
      return;
    }

    async function fetchData() {
      setIsLoading(true);
      try {
        const token = localStorage.getItem('token');
        const headers = {
          'Authorization': token ? `Bearer ${token}` : '',
        };

        // Check if this is an image type (image, image_link, image_chunk, etc.)
        const isImageType = previewItem.type?.startsWith('image');

        if (!isImageType && (previewItem.type === 'note' || previewItem.type === 'chunk')) {
          const response = await fetch(
            `http://localhost:8000/notes/${previewItem.id}`,
            { headers }
          );
          if (response.ok) {
            const data = await response.json();
            setNoteData(data);
            setImageData(null);
          }
        } else if (isImageType) {
          // Use /images/{id} for JSON metadata, /image/{id} is for the actual file
          const response = await fetch(
            `http://localhost:8000/images/${previewItem.id}`,
            { headers }
          );
          if (response.ok) {
            const data = await response.json();
            setImageData(data);
            setNoteData(null);
          }
        }
      } catch (error) {
        console.error('Failed to fetch preview:', error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchData();
  }, [previewItem]);

  if (!previewItem) {
    return (
      <div className="preview-section empty">
        <ActiveCitationsList
          citations={activeCitations}
          selectedId={null}
          onSelect={onSelectCitation}
        />
        {(!activeCitations || activeCitations.length === 0) && (
          <div className="preview-empty">
            <FileText size={24} />
            <span>Click a citation to preview</span>
          </div>
        )}
      </div>
    );
  }

  // Check if this is an image type (image, image_link, image_chunk, etc.)
  const isImageType = previewItem?.type?.startsWith('image');

  const handleNavigate = () => {
    if (!isImageType && (previewItem.type === 'note' || previewItem.type === 'chunk')) {
      onNavigateToNote?.(previewItem.id);
    } else if (isImageType) {
      onNavigateToImage?.(previewItem.id);
    }
  };

  return (
    <div className="preview-section">
      <div className="preview-header">
        <div className="preview-type">
          {isImageType ? (
            <ImageIcon size={14} className="image-icon" />
          ) : (
            <FileText size={14} className="note-icon" />
          )}
          <span>{isImageType ? 'Image' : 'Note'}</span>
        </div>
        <button className="preview-close" onClick={onClear}>
          <X size={14} />
        </button>
      </div>

      {isLoading ? (
        <div className="preview-loading">Loading...</div>
      ) : noteData ? (
        <div className="preview-content">
          <h4 className="preview-title">{noteData.title || 'Untitled'}</h4>
          <div className="preview-text">
            {noteData.content?.substring(0, 300)}
            {noteData.content?.length > 300 && '...'}
          </div>
          {previewItem.citation && (
            <div className="preview-meta">
              <span className="meta-item">
                Relevance: {Math.round((previewItem.citation.relevance_score || 0) * 100)}%
              </span>
              <span className="meta-item">
                Method: {previewItem.citation.retrieval_method}
              </span>
            </div>
          )}
          <button className="preview-navigate" onClick={handleNavigate}>
            <ExternalLink size={14} />
            Open Note
          </button>
        </div>
      ) : imageData ? (
        <div className="preview-content image">
          <div className="preview-image-wrapper">
            <img
              src={`http://localhost:8000/image/${imageData.id}`}
              alt={imageData.filename || 'Image'}
            />
          </div>
          <h4 className="preview-title">{imageData.display_name || imageData.filename || 'Image'}</h4>
          {imageData.ai_analysis_result && (
            <div className="preview-text">
              {imageData.ai_analysis_result.substring(0, 200)}
              {imageData.ai_analysis_result.length > 200 && '...'}
            </div>
          )}
          <button className="preview-navigate" onClick={handleNavigate}>
            <ExternalLink size={14} />
            Open Image
          </button>
        </div>
      ) : (
        <div className="preview-loading">Failed to load preview</div>
      )}

      {/* Active Citations List below preview */}
      <ActiveCitationsList
        citations={activeCitations}
        selectedId={previewItem?.id}
        onSelect={onSelectCitation}
      />
    </div>
  );
}

/**
 * Settings section - model and retrieval configuration
 */
function SettingsSection() {
  const { settings, updateSettings } = useAIChatContext();
  const [isExpanded, setIsExpanded] = useState(true);

  const handleChange = (key, value) => {
    updateSettings({ [key]: value });
  };

  return (
    <div className="settings-section">
      <button
        className="section-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="section-title">
          <Sliders size={14} />
          <span>Settings</span>
        </div>
        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {isExpanded && (
        <div className="settings-content">
          {/* Model Selection */}
          <div className="setting-item">
            <label>Model</label>
            <select
              value={settings.model}
              onChange={(e) => handleChange('model', e.target.value)}
            >
              <option value="llama3.1:8b">Llama 3.1 8B</option>
              <option value="qwen2.5:7b">Qwen 2.5 7B</option>
              <option value="mistral:7b-instruct">Mistral 7B</option>
            </select>
          </div>

          {/* Temperature */}
          <div className="setting-item">
            <label>
              Temperature
              <span className="setting-value">{settings.temperature}</span>
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={settings.temperature}
              onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
            />
          </div>

          {/* Max Sources */}
          <div className="setting-item">
            <label>
              Max Sources
              <span className="setting-value">{settings.maxSources}</span>
            </label>
            <input
              type="range"
              min="1"
              max="20"
              step="1"
              value={settings.maxSources}
              onChange={(e) => handleChange('maxSources', parseInt(e.target.value))}
            />
          </div>

          {/* Min Similarity */}
          <div className="setting-item">
            <label>
              Min Similarity
              <span className="setting-value">{settings.minSimilarity}</span>
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={settings.minSimilarity}
              onChange={(e) => handleChange('minSimilarity', parseFloat(e.target.value))}
            />
          </div>

          {/* Toggles */}
          <div className="setting-toggles">
            <label className="toggle-item">
              <input
                type="checkbox"
                checked={settings.useStreaming}
                onChange={(e) => handleChange('useStreaming', e.target.checked)}
              />
              <span>Stream responses</span>
            </label>

            <label className="toggle-item">
              <input
                type="checkbox"
                checked={settings.includeImages}
                onChange={(e) => handleChange('includeImages', e.target.checked)}
              />
              <span>Search images</span>
            </label>

            <label className="toggle-item">
              <input
                type="checkbox"
                checked={settings.includeGraph}
                onChange={(e) => handleChange('includeGraph', e.target.checked)}
              />
              <span>Use wikilinks</span>
            </label>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Brain section - adapter status and training
 */
function BrainSection() {
  const [isExpanded, setIsExpanded] = useState(true);
  const {
    status,
    adapters,
    isLoading,
    error,
    activeOperation,
    hasAdapter,
    activeVersion,
    brainStatus,
    notesIndexed,
    imagesIndexed,
    samplesCount,
    factsCount,
    lastIndexed,
    lastTrained,
    fetchStatus,
    fetchAdapters,
    startIndexing,
    startTraining,
    activateAdapter,
    formatDate,
    isIndexing,
    isTraining,
    canTrain,
    canIndex,
  } = useBrain();

  // Fetch status on mount
  useEffect(() => {
    fetchStatus();
    fetchAdapters();
  }, []);

  // Handle indexing
  const handleIndex = async () => {
    try {
      await startIndexing(false);
    } catch (err) {
      console.error('Indexing failed:', err);
    }
  };

  // Handle training
  const handleTrain = async () => {
    try {
      await startTraining();
    } catch (err) {
      console.error('Training failed:', err);
    }
  };

  // Get status badge
  const getStatusBadge = () => {
    switch (brainStatus) {
      case 'ready':
        return <span className="status-badge ready"><Check size={10} /> Ready</span>;
      case 'indexing':
        return <span className="status-badge indexing"><Loader2 size={10} className="spinning" /> Indexing</span>;
      case 'training':
        return <span className="status-badge training"><Loader2 size={10} className="spinning" /> Training</span>;
      case 'indexed':
        return <span className="status-badge indexed"><Database size={10} /> Indexed</span>;
      default:
        return <span className="status-badge none">Not Setup</span>;
    }
  };

  return (
    <div className="brain-section">
      <button
        className="section-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="section-title">
          <Brain size={14} />
          <span>Brain</span>
          {getStatusBadge()}
        </div>
        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {isExpanded && (
        <div className="brain-content">
          {error && (
            <div className="brain-error">
              <AlertCircle size={12} />
              {error}
            </div>
          )}

          {/* Progress bar during operations */}
          {activeOperation && (
            <div className="brain-progress">
              <div className="progress-bar">
                <div className="progress-bar-indeterminate" />
              </div>
              <span className="progress-text">
                {activeOperation.type === 'indexing' ? 'Indexing your content...' : 'Training your brain...'}
              </span>
            </div>
          )}

          {/* Stats */}
          <div className="brain-stats">
            <div className="brain-stat">
              <span className="stat-label">Adapter</span>
              <span className="stat-value">
                {hasAdapter ? `v${activeVersion}` : 'None'}
              </span>
            </div>
            <div className="brain-stat">
              <span className="stat-label">Notes</span>
              <span className="stat-value">{notesIndexed}</span>
            </div>
            <div className="brain-stat">
              <span className="stat-label">Images</span>
              <span className="stat-value">{imagesIndexed}</span>
            </div>
            <div className="brain-stat">
              <span className="stat-label">Samples</span>
              <span className="stat-value">{samplesCount}</span>
            </div>
            <div className="brain-stat">
              <span className="stat-label">Facts</span>
              <span className="stat-value">{factsCount}</span>
            </div>
          </div>

          {/* Timestamps */}
          <div className="brain-timestamps">
            <span>Indexed: {formatDate(lastIndexed)}</span>
            <span>Trained: {formatDate(lastTrained)}</span>
          </div>

          {/* Action buttons */}
          <div className="brain-actions">
            <button
              className="brain-action-btn index"
              onClick={handleIndex}
              disabled={!canIndex || isLoading}
              title="Analyze your notes and images to extract knowledge"
            >
              {isIndexing ? (
                <Loader2 size={14} className="spinning" />
              ) : (
                <Database size={14} />
              )}
              {isIndexing ? 'Indexing...' : 'Index'}
            </button>

            <button
              className="brain-action-btn train"
              onClick={handleTrain}
              disabled={!canTrain || isLoading}
              title={samplesCount === 0 ? 'Index first to generate training samples' : 'Train a personalized AI adapter'}
            >
              {isTraining ? (
                <Loader2 size={14} className="spinning" />
              ) : (
                <Sparkles size={14} />
              )}
              {isTraining ? 'Training...' : 'Train'}
            </button>
          </div>

          {/* Hint when no samples */}
          {samplesCount === 0 && !activeOperation && (
            <p className="brain-hint">
              Click "Index" to analyze your notes and generate training data.
            </p>
          )}

          {/* Adapters list */}
          {adapters.length > 0 && (
            <div className="brain-adapters">
              <div className="adapters-header">Adapters</div>
              {adapters.slice(0, 3).map((adapter) => (
                <div
                  key={adapter.version}
                  className={`adapter-item ${adapter.is_active ? 'active' : ''}`}
                  onClick={() => !adapter.is_active && activateAdapter(adapter.version)}
                >
                  <span className="adapter-version">
                    {adapter.is_active ? <Check size={12} /> : <span className="adapter-radio" />}
                    v{adapter.version}
                  </span>
                  <span className="adapter-info">
                    {adapter.dataset_size} samples
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * BrainFilesPanel - Shows brain files and topics for Mnemosyne mode
 */
function BrainFilesPanel() {
  const [isExpanded, setIsExpanded] = useState(true);
  const { state } = useAIChatContext();
  const { brainFiles, fetchBrainFiles, hasBrain, isReady, isBuilding } = useMnemosyneBrain();

  useEffect(() => {
    fetchBrainFiles();
  }, []);

  const { brainFilesUsed, topicsMatched } = state;

  return (
    <div className="brain-section">
      <button
        className="section-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="section-title">
          <Brain size={14} />
          <span>Brain Files</span>
          {isReady ? (
            <span className="status-badge ready"><Check size={10} /> Ready</span>
          ) : isBuilding ? (
            <span className="status-badge indexing"><Loader2 size={10} className="spinning" /> Building</span>
          ) : (
            <span className="status-badge none">Not Built</span>
          )}
        </div>
        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {isExpanded && (
        <div className="brain-content">
          {/* Files loaded for last response */}
          {brainFilesUsed.length > 0 && (
            <div className="brain-stats">
              <div className="adapters-header">Loaded Files</div>
              {brainFilesUsed.map((fileKey, idx) => (
                <div key={idx} className="adapter-item">
                  <span className="adapter-version">
                    <FileText size={12} />
                    {fileKey}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Topics matched */}
          {topicsMatched.length > 0 && (
            <div className="brain-stats">
              <div className="adapters-header">Topics Matched</div>
              {topicsMatched.map((topic, idx) => (
                <div key={idx} className="adapter-item">
                  <span className="adapter-version">
                    <Sparkles size={12} />
                    {topic}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* All brain files */}
          {brainFiles.length > 0 && (
            <div className="brain-stats">
              <div className="adapters-header">All Brain Files ({brainFiles.length})</div>
              {brainFiles.map((file, idx) => (
                <div key={idx} className="adapter-item">
                  <span className="adapter-version">
                    <FileText size={12} />
                    {file.file_key}
                  </span>
                  <span className="adapter-info">
                    {file.file_type} · ~{file.token_count_approx || '?'} tokens
                  </span>
                </div>
              ))}
            </div>
          )}

          {!hasBrain && brainFiles.length === 0 && (
            <p className="brain-hint">
              Build your brain first to enable Mnemosyne mode.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Brain mode settings - simplified, only temperature
 */
function BrainSettingsSection() {
  const { settings, updateSettings } = useAIChatContext();
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="settings-section">
      <button
        className="section-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="section-title">
          <Sliders size={14} />
          <span>Settings</span>
        </div>
        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {isExpanded && (
        <div className="settings-content">
          <div className="setting-item">
            <label>
              Temperature
              <span className="setting-value">{settings.temperature}</span>
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={settings.temperature}
              onChange={(e) => updateSettings({ temperature: parseFloat(e.target.value) })}
            />
          </div>

          <div className="setting-toggles">
            <label className="toggle-item">
              <input
                type="checkbox"
                checked={settings.useStreaming}
                onChange={(e) => updateSettings({ useStreaming: e.target.checked })}
              />
              <span>Stream responses</span>
            </label>
          </div>
        </div>
      )}
    </div>
  );
}

function ContextRadar({ isCollapsed, onCollapse, onNavigateToNote, onNavigateToImage }) {
  const { state, dispatch, ActionTypes } = useAIChatContext();
  const isBrainMode = state.chatMode === 'mnemosyne';

  const handleClearPreview = useCallback(() => {
    dispatch({ type: ActionTypes.CLEAR_PREVIEW });
  }, [dispatch, ActionTypes]);

  const handleSelectCitation = useCallback((citation) => {
    dispatch({
      type: ActionTypes.SET_PREVIEW,
      payload: {
        type: citation.source_type,
        id: citation.source_id,
        title: citation.title,
        citation,
      },
    });
  }, [dispatch, ActionTypes]);

  return (
    <div className="context-radar">
      {/* Header */}
      <div className="context-radar-header">
        <div className="context-radar-title">
          <Settings size={16} />
          <span>{isBrainMode ? 'Brain & Settings' : 'Context & Settings'}</span>
        </div>
        <button
          className="collapse-btn"
          onClick={onCollapse}
          title="Collapse panel"
        >
          <ChevronRight size={18} />
        </button>
      </div>

      {/* Scrollable content area */}
      <div className="context-radar-content">
        {isBrainMode ? (
          <>
            {/* Brain Files Panel */}
            <BrainFilesPanel />
            {/* Simplified Settings */}
            <BrainSettingsSection />
          </>
        ) : (
          <>
            {/* Preview Section */}
            <PreviewSection
              previewItem={state.previewItem}
              activeCitations={state.activeCitations}
              onNavigateToNote={onNavigateToNote}
              onNavigateToImage={onNavigateToImage}
              onClear={handleClearPreview}
              onSelectCitation={handleSelectCitation}
            />
            {/* Settings Section */}
            <SettingsSection />
            {/* Brain Section */}
            <BrainSection />
          </>
        )}
      </div>
    </div>
  );
}

export default ContextRadar;
