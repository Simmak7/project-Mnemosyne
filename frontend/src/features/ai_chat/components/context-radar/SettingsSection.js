/**
 * Settings section - model and retrieval configuration for RAG mode
 */
import React, { useState, useEffect } from 'react';
import { Sliders, ChevronUp, ChevronDown } from 'lucide-react';
import { useAIChatContext } from '../../hooks/AIChatContext';

function SettingsSection() {
  const { settings, updateSettings } = useAIChatContext();
  const [isExpanded, setIsExpanded] = useState(true);
  const [availableModels, setAvailableModels] = useState([]);
  const [currentModel, setCurrentModel] = useState(null);

  // Fetch available models on mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch('http://localhost:8000/models', {
          credentials: 'include'
        });
        if (response.ok) {
          const data = await response.json();
          setAvailableModels(data.models || []);
          setCurrentModel(data.current_rag_model);
        }
      } catch (error) {
        console.error('Failed to fetch models:', error);
      }
    };
    fetchModels();
  }, []);

  const handleChange = (key, value) => {
    updateSettings({ [key]: value });
  };

  // Get RAG-capable models
  const ragModels = availableModels.filter(
    m => m.use_cases?.includes('rag') || m.use_cases?.includes('both')
  );

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
          {/* Model Display */}
          <div className="setting-item">
            <label>Active Model</label>
            {ragModels.length > 0 ? (
              <div className="model-display">
                <span className="model-name">
                  {ragModels.find(m => m.id === currentModel)?.name || currentModel || 'Loading...'}
                </span>
                <span className="model-hint">Configure in Settings</span>
              </div>
            ) : (
              <div className="model-display">
                <span className="model-name">{currentModel || 'Loading...'}</span>
              </div>
            )}
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

export default SettingsSection;
