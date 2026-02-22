/**
 * AI Models settings section - Model selection + Model Library with pull/delete
 */
import React, { useEffect, useCallback, useRef } from 'react';
import { Cpu, Sparkles, Brain, Eye } from 'lucide-react';
import ModelLibrary from '../components/ModelLibrary';
import { useModelManagement } from '../hooks/useModelManagement';
import './AIModelsSection.css';

function AIModelsSection({ availableModels, modelConfig, preferences, onPreferenceUpdate, onModelsChanged }) {
  const {
    pullProgress, pullModel, cancelPull, deleteModel, clearProgress,
    updateStatus, checkingUpdates, checkForUpdates,
  } = useModelManagement(onModelsChanged);

  const checkedRef = useRef(false);
  useEffect(() => {
    if (availableModels?.length && !checkedRef.current) {
      checkedRef.current = true;
      checkForUpdates(false);
    }
  }, [availableModels, checkForUpdates]);

  const handleUpdate = useCallback((modelId) => {
    pullModel(modelId);
  }, [pullModel]);

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
  const visionModels = availableModels.filter(
    m => m.use_cases?.includes('vision')
  );

  return (
    <div className="settings-section">
      <div className="settings-section-header">
        <Cpu size={20} />
        <h3>AI Models</h3>
      </div>
      <p className="settings-section-description">
        Choose which AI models power your NEXUS RAG, ZAIA AI, and image analysis.
      </p>

      {/* Model selectors */}
      <div className="settings-appearance-grid">
        <ModelSelect
          icon={<Sparkles size={14} className="label-icon" />}
          label="NEXUS RAG Model"
          value={preferences.rag_model || ''}
          onChange={v => onPreferenceUpdate('rag_model', v)}
          models={ragModels}
          defaultLabel={modelConfig?.current_rag_model || 'auto'}
          allModels={availableModels}
          defaultFlag="is_default_rag"
        />
        <ModelSelect
          icon={<Brain size={14} className="label-icon" />}
          label="ZAIA AI Model"
          value={preferences.brain_model || ''}
          onChange={v => onPreferenceUpdate('brain_model', v)}
          models={brainModels}
          defaultLabel={modelConfig?.current_brain_model?.split('/').pop() || 'auto'}
          allModels={availableModels}
          defaultFlag="is_default_brain"
        />
        <ModelSelect
          icon={<Eye size={14} className="label-icon" />}
          label="Image Analysis"
          value={preferences.vision_model || ''}
          onChange={v => onPreferenceUpdate('vision_model', v)}
          models={visionModels}
          defaultLabel={modelConfig?.current_vision_model || 'auto'}
          allModels={availableModels}
        />
      </div>

      {/* Model Library */}
      <ModelLibrary
        models={availableModels.filter(m => m.provider === 'ollama')}
        pullProgress={pullProgress}
        onPull={pullModel}
        onDelete={deleteModel}
        onCancelPull={cancelPull}
        onPullCustom={pullModel}
        updateStatus={updateStatus}
        checkingUpdates={checkingUpdates}
        onUpdate={handleUpdate}
        onCheckUpdates={checkForUpdates}
      />
    </div>
  );
}

function ModelSelect({ icon, label, value, onChange, models, defaultLabel, allModels, defaultFlag }) {
  const selectedInfo = allModels?.find(m => m.id === value);

  return (
    <div className="settings-appearance-item model-select-item">
      <label>{icon} {label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="settings-select"
      >
        <option value="">System Default ({defaultLabel})</option>
        {models.map(m => (
          <option key={m.id} value={m.id} disabled={m.is_available === false}>
            {m.name} ({m.parameters}) {defaultFlag && m[defaultFlag] ? '\u2605' : ''}
            {m.is_available === false ? ' - Not installed' : ''}
          </option>
        ))}
      </select>
      {value && selectedInfo?.description && (
        <div className="model-info">{selectedInfo.description}</div>
      )}
    </div>
  );
}

export default AIModelsSection;
