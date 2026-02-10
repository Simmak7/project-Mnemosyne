/**
 * Brain mode settings - simplified, only temperature
 */
import React, { useState, useEffect } from 'react';
import { Sliders, ChevronUp, ChevronDown } from 'lucide-react';
import { useAIChatContext } from '../../hooks/AIChatContext';

function BrainSettingsSection() {
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
          setCurrentModel(data.current_brain_model);
        }
      } catch (error) {
        console.error('Failed to fetch models:', error);
      }
    };
    fetchModels();
  }, []);

  // Get Brain-capable models
  const brainModels = availableModels.filter(
    m => m.use_cases?.includes('brain') || m.use_cases?.includes('both')
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
            {brainModels.length > 0 ? (
              <div className="model-display brain">
                <span className="model-name">
                  {brainModels.find(m => m.id === currentModel)?.name || currentModel?.split('/').pop() || 'Loading...'}
                </span>
                <span className="model-hint">Configure in Settings</span>
              </div>
            ) : (
              <div className="model-display brain">
                <span className="model-name">{currentModel?.split('/').pop() || 'Loading...'}</span>
              </div>
            )}
          </div>

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

export default BrainSettingsSection;
