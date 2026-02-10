/**
 * AnalysisConfig - Right panel configuration for AI analysis
 * Includes presets, model selection, and user prompt input
 */

import React from 'react';
import {
  Settings,
  Image,
  FileText,
  GitBranch,
  Monitor,
  PenTool,
  ChevronDown,
  ChevronRight,
  RotateCcw,
  Info,
  Zap,
  Gauge,
  Sparkles,
  Tags,
  FolderPlus,
  FileEdit,
  Languages,
  Eye
} from 'lucide-react';
import { UPLOAD_FLAGS } from '../utils/featureFlags';
import { PRESETS } from '../utils/promptComposer';

import './AnalysisConfig.css';

/**
 * Get icon component for preset
 */
function getPresetIcon(iconName) {
  const icons = {
    Image,
    FileText,
    GitBranch,
    Monitor,
    PenTool
  };
  return icons[iconName] || Image;
}

/**
 * Analysis depth options
 */
const DEPTH_OPTIONS = [
  { id: 'quick', label: 'Quick', icon: Zap, description: 'Brief summary' },
  { id: 'standard', label: 'Standard', icon: Gauge, description: 'Balanced analysis' },
  { id: 'detailed', label: 'Detailed', icon: Sparkles, description: 'Comprehensive' }
];

/**
 * AnalysisConfig Component
 * @param {object} props
 * @param {object} props.config - Current configuration
 * @param {function} props.onUserPromptChange - User prompt change handler
 * @param {function} props.onModelChange - Model change handler
 * @param {function} props.onPresetChange - Preset change handler
 * @param {function} props.onToggleAdvanced - Toggle advanced options
 * @param {function} props.onDepthChange - Analysis depth change handler
 * @param {function} props.onAutoTaggingChange - Auto-tagging toggle handler
 * @param {function} props.onMaxTagsChange - Max tags change handler
 * @param {function} props.onAutoCreateNoteChange - Auto-create note toggle handler
 * @param {function} props.onReset - Reset to defaults
 * @param {boolean} props.isModified - Whether config differs from defaults
 * @param {string} props.configSummary - Human-readable config summary
 * @param {object} props.albumPicker - Optional album picker component
 */
function AnalysisConfig({
  config,
  visionModel,
  hasPdfs = false,
  hasImages = false,
  onUserPromptChange,
  onModelChange,
  onPresetChange,
  onToggleAdvanced,
  onDepthChange,
  onAutoTaggingChange,
  onMaxTagsChange,
  onAutoCreateNoteChange,
  onReset,
  isModified,
  configSummary,
  albumPicker
}) {
  const pdfOnly = hasPdfs && !hasImages;
  const mixedQueue = hasPdfs && hasImages;

  return (
    <div className="analysis-config">
      {/* Header */}
      <div className="config-header">
        <div className="config-header-title">
          <Settings size={18} />
          <h2>Analysis Settings</h2>
        </div>
        {isModified && (
          <button
            className="config-reset-btn"
            onClick={onReset}
            title="Reset to defaults"
          >
            <RotateCcw size={14} />
            Reset
          </button>
        )}
      </div>

      {/* Config summary */}
      {isModified && (
        <div className="config-summary">
          <Info size={14} />
          {configSummary}
        </div>
      )}

      {/* Main content */}
      <div className="config-content">
        {/* PDF-only info block */}
        {pdfOnly && (
          <div className="config-pdf-info">
            <FileText size={16} />
            <div>
              <strong>PDF Analysis</strong>
              <p>PDFs use automatic text extraction and AI enrichment. You can review and edit suggestions before creating notes.</p>
            </div>
          </div>
        )}

        {/* Mixed queue notice */}
        {mixedQueue && (
          <div className="config-mixed-notice">
            <Info size={14} />
            <span>Settings below apply to images only. PDFs use automatic analysis.</span>
          </div>
        )}

        {/* Intent Presets (if enabled, images only) */}
        {UPLOAD_FLAGS.INTENT_PRESETS && !pdfOnly && (
          <div className="config-section">
            <h3 className="config-section-title">Analysis Type</h3>
            <div className="config-presets">
              {PRESETS.map(preset => {
                const Icon = getPresetIcon(preset.icon);
                const isActive = config.preset === preset.id;
                return (
                  <button
                    key={preset.id}
                    className={`config-preset ${isActive ? 'active' : ''}`}
                    onClick={() => onPresetChange(isActive ? null : preset.id)}
                    title={preset.description}
                  >
                    <Icon size={16} />
                    {preset.label}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* User Prompt (if enabled) */}
        {UPLOAD_FLAGS.USER_PROMPT_LAYER && (
          <div className="config-section">
            <h3 className="config-section-title">
              {pdfOnly ? 'Document Instructions' : 'Global Instructions'}
              <span className="config-optional">(optional)</span>
            </h3>
            <p className="config-section-hint">
              {pdfOnly
                ? 'Additional instructions for AI analysis. These guide what the AI focuses on in the document.'
                : 'Applied to all files. Individual files can override this via "Custom instructions" on each file card.'}
            </p>
            <textarea
              className="config-prompt-input ng-glass-inset"
              value={config.userPrompt}
              onChange={(e) => onUserPromptChange(e.target.value)}
              placeholder={pdfOnly
                ? 'e.g., Focus on key arguments and conclusions, extract any tables or data...'
                : 'e.g., Focus on extracting text and identifying key concepts...'}
              rows={4}
            />
          </div>
        )}

        {/* Advanced Options (collapsed by default, hidden for PDF-only) */}
        {!pdfOnly && (
          <div className="config-section config-advanced">
            <button
              className="config-advanced-toggle"
              onClick={onToggleAdvanced}
            >
              {config.showAdvanced ? (
                <ChevronDown size={16} />
              ) : (
                <ChevronRight size={16} />
              )}
              <span>Advanced Options</span>
            </button>

            {config.showAdvanced && (
              <div className="config-advanced-content">
                {/* Active Vision Model */}
                {visionModel && (
                  <div className="config-advanced-section">
                    <h4 className="config-advanced-label">
                      <Eye size={14} />
                      AI Model
                    </h4>
                    <div className="config-model-info-display">
                      <span className="config-model-name">{visionModel.name}</span>
                      {visionModel.parameters && (
                        <span className="config-model-params">{visionModel.parameters}</span>
                      )}
                      <span className={`config-model-status ${visionModel.is_available ? 'active' : 'unavailable'}`}>
                        {visionModel.is_available ? 'Active' : 'Unavailable'}
                      </span>
                    </div>
                  </div>
                )}

                {/* Analysis Depth */}
                <div className="config-advanced-section">
                  <h4 className="config-advanced-label">
                    <Gauge size={14} />
                    Analysis Depth
                  </h4>
                  <div className="config-depth-options">
                    {DEPTH_OPTIONS.map(depth => {
                      const DepthIcon = depth.icon;
                      const isActive = config.analysisDepth === depth.id;
                      return (
                        <button
                          key={depth.id}
                          className={`config-depth-btn ${isActive ? 'active' : ''}`}
                          onClick={() => onDepthChange(depth.id)}
                          title={depth.description}
                        >
                          <DepthIcon size={14} />
                          {depth.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Auto-Tagging */}
                <div className="config-advanced-section">
                  <h4 className="config-advanced-label">
                    <Tags size={14} />
                    Auto-Tagging
                  </h4>
                  <div className="config-toggle-row">
                    <label className="config-toggle">
                      <input
                        type="checkbox"
                        checked={config.autoTagging}
                        onChange={(e) => onAutoTaggingChange(e.target.checked)}
                      />
                      <span className="config-toggle-slider"></span>
                      <span className="config-toggle-label">
                        Extract tags automatically
                      </span>
                    </label>
                  </div>
                  {config.autoTagging && (
                    <div className="config-slider-row">
                      <span className="config-slider-label">Max tags:</span>
                      <input
                        type="range"
                        min="1"
                        max="10"
                        value={config.maxTags}
                        onChange={(e) => onMaxTagsChange(parseInt(e.target.value))}
                        className="config-slider"
                      />
                      <span className="config-slider-value">{config.maxTags}</span>
                    </div>
                  )}
                </div>

                {/* Album Assignment */}
                <div className="config-advanced-section">
                  <h4 className="config-advanced-label">
                    <FolderPlus size={14} />
                    Album Assignment
                  </h4>
                  {albumPicker || (
                    <p className="config-hint">
                      Select an album to add uploaded images
                    </p>
                  )}
                </div>

                {/* Note Options */}
                <div className="config-advanced-section">
                  <h4 className="config-advanced-label">
                    <FileEdit size={14} />
                    Note Options
                  </h4>
                  <div className="config-toggle-row">
                    <label className="config-toggle">
                      <input
                        type="checkbox"
                        checked={config.autoCreateNote}
                        onChange={(e) => onAutoCreateNoteChange(e.target.checked)}
                      />
                      <span className="config-toggle-slider"></span>
                      <span className="config-toggle-label">
                        Auto-create note from image
                      </span>
                    </label>
                  </div>
                </div>

                {/* Language - Coming Soon */}
                <div className="config-advanced-section config-coming-soon">
                  <h4 className="config-advanced-label">
                    <Languages size={14} />
                    Language
                    <span className="config-badge-soon">Coming Soon</span>
                  </h4>
                  <p className="config-hint">
                    Multi-language analysis support
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Info footer */}
      <div className="config-footer">
        <div className="config-footer-info">
          <Info size={14} />
          <span>
            Your settings are saved automatically and will be used for all files
            in the queue unless overridden.
          </span>
        </div>
      </div>
    </div>
  );
}

export default AnalysisConfig;
