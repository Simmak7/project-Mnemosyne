/**
 * AI Models settings section - RAG and Brain model selection
 */
import React from 'react';
import { Cpu, Sparkles, Brain, Eye } from 'lucide-react';

function AIModelsSection({ availableModels, modelConfig, preferences, onPreferenceUpdate }) {
  if (!availableModels?.length || !preferences) {
    return (
      <div className="settings-section">
        <div className="settings-section-header">
          <Cpu size={20} />
          <h3>AI Models</h3>
        </div>
        <p className="settings-section-description">
          Choose which AI models power your NEXUS RAG and ZAIA AI.
        </p>
        <div className="settings-item">
          <div className="settings-item-info">
            <p className="settings-placeholder">Loading models...</p>
          </div>
        </div>
      </div>
    );
  }

  const ragModels = availableModels.filter(
    m => m.use_cases?.includes('rag') || m.use_cases?.includes('both')
  );
  const brainModels = availableModels.filter(
    m => m.use_cases?.includes('brain') || m.use_cases?.includes('both')
  );

  return (
    <div className="settings-section">
      <div className="settings-section-header">
        <Cpu size={20} />
        <h3>AI Models</h3>
      </div>
      <p className="settings-section-description">
        Choose which AI models power your NEXUS RAG and ZAIA AI.
      </p>
      <div className="settings-appearance-grid">
        <div className="settings-appearance-item model-select-item">
          <label>
            <Sparkles size={14} className="label-icon" />
            NEXUS RAG Model
          </label>
          <select
            value={preferences.rag_model || ''}
            onChange={(e) => onPreferenceUpdate('rag_model', e.target.value)}
            className="settings-select"
          >
            <option value="">System Default ({modelConfig?.current_rag_model || 'auto'})</option>
            {ragModels.map(m => (
              <option key={m.id} value={m.id} disabled={m.is_available === false}>
                {m.name} ({m.parameters}) {m.is_default_rag ? '\u2605' : ''}
                {m.is_available === false ? ' \u26A0\uFE0F Not installed' : ''}
              </option>
            ))}
          </select>
          {preferences.rag_model && (
            <div className="model-info">
              {availableModels.find(m => m.id === preferences.rag_model)?.description}
            </div>
          )}
        </div>
        <div className="settings-appearance-item model-select-item">
          <label>
            <Brain size={14} className="label-icon" />
            ZAIA AI Model
          </label>
          <select
            value={preferences.brain_model || ''}
            onChange={(e) => onPreferenceUpdate('brain_model', e.target.value)}
            className="settings-select"
          >
            <option value="">
              System Default ({modelConfig?.current_brain_model?.split('/').pop() || 'auto'})
            </option>
            {brainModels.map(m => (
              <option key={m.id} value={m.id} disabled={m.is_available === false}>
                {m.name} ({m.parameters}) {m.is_default_brain ? '\u2605' : ''}
                {m.is_available === false ? ' \u26A0\uFE0F Not installed' : ''}
              </option>
            ))}
          </select>
          {preferences.brain_model && (
            <div className="model-info">
              {availableModels.find(m => m.id === preferences.brain_model)?.description}
            </div>
          )}
        </div>
        <VisionModelDisplay
          availableModels={availableModels}
          modelConfig={modelConfig}
        />
      </div>
    </div>
  );
}

function VisionModelDisplay({ availableModels, modelConfig }) {
  const visionModelId = modelConfig?.current_vision_model;
  const visionModel = availableModels.find(m => m.id === visionModelId);

  return (
    <div className="settings-appearance-item model-select-item">
      <label>
        <Eye size={14} className="label-icon" />
        Image Analysis
      </label>
      <div className="model-readonly-display ng-glass-inset">
        <span className="model-readonly-name">
          {visionModel?.name || visionModelId || 'Unknown'}
        </span>
        {visionModel?.parameters && (
          <span className="model-readonly-params">({visionModel.parameters})</span>
        )}
        {visionModel && (
          <span className={`model-readonly-status ${visionModel.is_available !== false ? 'available' : 'unavailable'}`}>
            {visionModel.is_available !== false ? 'Active' : 'Not installed'}
          </span>
        )}
      </div>
      {visionModel?.description && (
        <div className="model-info">{visionModel.description}</div>
      )}
    </div>
  );
}

export default AIModelsSection;
