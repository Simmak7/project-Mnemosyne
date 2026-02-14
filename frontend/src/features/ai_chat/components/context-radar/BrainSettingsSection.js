/**
 * Brain mode settings - model display, temperature, streaming
 *
 * Reads the user's brain_model preference to show the actual active model.
 */
import React, { useState, useEffect } from 'react';
import { Sliders, ChevronUp, ChevronDown, AlertTriangle } from 'lucide-react';
import { useAIChatContext } from '../../hooks/AIChatContext';
import { api } from '../../../../utils/api';

function BrainSettingsSection() {
  const { settings, updateSettings } = useAIChatContext();
  const [isExpanded, setIsExpanded] = useState(true);
  const [availableModels, setAvailableModels] = useState([]);
  const [systemDefault, setSystemDefault] = useState(null);
  const [userModel, setUserModel] = useState(undefined); // undefined = loading

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [modelsData, prefs] = await Promise.all([
          api.get('/models'),
          api.get('/settings/preferences'),
        ]);
        setAvailableModels(modelsData.models || []);
        setSystemDefault(modelsData.current_brain_model);
        setUserModel(prefs.brain_model || null);
      } catch (error) {
        console.error('Failed to fetch brain model info:', error);
      }
    };
    fetchData();
  }, []);

  const brainModels = availableModels.filter(
    m => m.use_cases?.includes('brain') || m.use_cases?.includes('both')
  );

  // Resolve the actual active model: user preference > system default
  const activeModelId = userModel || systemDefault;
  const activeModelInfo = brainModels.find(m => m.id === activeModelId);
  const displayName = activeModelInfo?.name
    || activeModelId?.split('/').pop()?.split(':').join(' ')
    || 'Loading...';
  const isCustom = userModel && userModel !== systemDefault;

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
            <div className="model-display brain">
              <span className="model-name">{displayName}</span>
              {activeModelInfo?.parameters && (
                <span className="model-params">{activeModelInfo.parameters}</span>
              )}
            </div>
            <span className="setting-hint">
              Change model in Settings &gt; AI Models
            </span>
            {isCustom && (
              <span className="setting-hint warning">
                <AlertTriangle size={11} />
                After changing models, we recommend rebuilding the Brain index
              </span>
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
