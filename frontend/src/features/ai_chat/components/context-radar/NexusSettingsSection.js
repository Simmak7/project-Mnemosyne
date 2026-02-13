/**
 * NexusSettingsSection - NEXUS-specific settings for the ContextRadar
 *
 * Provides:
 * - Analysis depth selector (Auto/Fast/Standard/Deep)
 * - Model selector for NEXUS generation
 * - Shared settings (max sources, similarity, streaming)
 */
import React, { useState, useEffect } from 'react';
import { Sliders, ChevronUp, ChevronDown, Zap, Network, Layers } from 'lucide-react';
import { useAIChatContext } from '../../hooks/AIChatContext';
import { api } from '../../../../utils/api';

const MODE_OPTIONS = [
  { value: 'auto', label: 'Auto', icon: Zap, desc: 'Auto-detect based on query' },
  { value: 'fast', label: 'Fast', icon: Zap, desc: 'Vector search only (2-4s)' },
  { value: 'standard', label: 'Standard', icon: Network, desc: '+ Graph navigation (4-7s)' },
  { value: 'deep', label: 'Deep', icon: Layers, desc: '+ PageRank diffusion (5-9s)' },
];

function NexusSettingsSection() {
  const { settings, updateSettings } = useAIChatContext();
  const [isExpanded, setIsExpanded] = useState(true);
  const [availableModels, setAvailableModels] = useState([]);
  const [currentNexusModel, setCurrentNexusModel] = useState(null);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const data = await api.get('/models');
        setAvailableModels(data.models || []);
        setCurrentNexusModel(data.current_nexus_model || data.current_rag_model);
      } catch (error) {
        console.error('Failed to fetch models:', error);
      }
    };
    fetchModels();
  }, []);

  const handleChange = (key, value) => {
    updateSettings({ [key]: value });
  };

  const handleModelChange = async (modelId) => {
    try {
      await api.patch('/settings/preferences', { nexus_model: modelId || '' });
      setCurrentNexusModel(modelId);
    } catch (error) {
      console.error('Failed to update NEXUS model:', error);
    }
  };

  // Filter to non-vision models for NEXUS generation
  const nexusModels = availableModels.filter(
    m => m.use_cases?.includes('rag') || m.use_cases?.includes('brain') || m.use_cases?.includes('both')
  );

  const nexusMode = settings.nexusMode || 'auto';

  return (
    <div className="settings-section">
      <button
        className="section-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="section-title">
          <Sliders size={14} />
          <span>NEXUS Settings</span>
        </div>
        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {isExpanded && (
        <div className="settings-content">
          {/* Analysis Depth / Mode */}
          <div className="setting-item">
            <label>Analysis Depth</label>
            <div className="nexus-mode-selector">
              {MODE_OPTIONS.map(opt => {
                const Icon = opt.icon;
                return (
                  <button
                    key={opt.value}
                    className={`nexus-mode-option ${nexusMode === opt.value ? 'active' : ''}`}
                    onClick={() => handleChange('nexusMode', opt.value)}
                    title={opt.desc}
                  >
                    <Icon size={12} />
                    <span>{opt.label}</span>
                  </button>
                );
              })}
            </div>
            <span className="setting-hint">
              {MODE_OPTIONS.find(m => m.value === nexusMode)?.desc}
            </span>
          </div>

          {/* Model Selection */}
          <div className="setting-item">
            <label>Generation Model</label>
            {nexusModels.length > 0 ? (
              <select
                className="nexus-model-select"
                value={currentNexusModel || ''}
                onChange={(e) => handleModelChange(e.target.value)}
              >
                {nexusModels.map(m => (
                  <option key={m.id} value={m.id} disabled={!m.is_available}>
                    {m.name} ({m.parameters}){!m.is_available ? ' [not installed]' : ''}
                  </option>
                ))}
              </select>
            ) : (
              <span className="model-name">Loading...</span>
            )}
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

export default NexusSettingsSection;
