/**
 * ModelLibrary - Grid of ModelCards with filter tabs
 */
import React, { useState } from 'react';
import { Download, RefreshCw } from 'lucide-react';
import ModelCard from './ModelCard';

const TABS = [
  { key: 'all', label: 'All' },
  { key: 'installed', label: 'Installed' },
  { key: 'updates', label: 'Updates' },
  { key: 'vision', label: 'Vision' },
  { key: 'text', label: 'Text' },
];

function ModelLibrary({
  models, pullProgress, onPull, onDelete, onCancelPull, onPullCustom,
  updateStatus, checkingUpdates, onUpdate, onCheckUpdates,
}) {
  const [activeTab, setActiveTab] = useState('all');
  const [customModel, setCustomModel] = useState('');

  const updatesCount = Object.values(updateStatus || {}).filter(u => u.update_available).length;

  const filteredModels = (models || []).filter(m => {
    if (activeTab === 'installed') return m.is_available;
    if (activeTab === 'updates') {
      return m.is_available && updateStatus?.[m.id]?.update_available;
    }
    if (activeTab === 'vision') return m.category === 'vision';
    if (activeTab === 'text') return m.category !== 'vision';
    return true;
  });

  const handleCustomPull = () => {
    const name = customModel.trim();
    if (!name) return;
    onPullCustom(name);
    setCustomModel('');
  };

  return (
    <div className="model-library">
      <div className="model-library-header">
        <h4>Model Library</h4>
        <div className="model-library-header-right">
          <div className="model-library-tabs">
            {TABS.map(tab => (
              <button
                key={tab.key}
                className={`model-tab ${activeTab === tab.key ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.key)}
              >
                {tab.label}
                {tab.key === 'updates' && updatesCount > 0 && (
                  <span className="model-tab-count">{updatesCount}</span>
                )}
              </button>
            ))}
          </div>
          <button
            className="model-btn model-btn-check-updates"
            onClick={() => onCheckUpdates?.(true)}
            disabled={checkingUpdates}
            title="Check for model updates"
          >
            <RefreshCw size={14} className={checkingUpdates ? 'model-updates-spin' : ''} />
            {checkingUpdates ? 'Checking...' : 'Check Updates'}
          </button>
        </div>
      </div>

      <div className="model-library-grid">
        {filteredModels.map(m => (
          <ModelCard
            key={m.id}
            model={m}
            progress={pullProgress[m.id]}
            onPull={onPull}
            onDelete={onDelete}
            onCancelPull={onCancelPull}
            updateInfo={updateStatus?.[m.id]}
            onUpdate={onUpdate}
          />
        ))}
        {filteredModels.length === 0 && (
          <p className="model-library-empty">No models match this filter.</p>
        )}
      </div>

      {/* Pull custom model */}
      <div className="model-custom-pull">
        <label>Pull Custom Model</label>
        <p className="model-custom-help">
          Browse the{' '}
          <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer">
            Ollama Model Library
          </a>
          {' '}to find a model. Copy the model name (e.g. <code>gemma3:4b</code>) and paste it below to download.
        </p>
        <div className="model-custom-pull-row">
          <input
            type="text"
            value={customModel}
            onChange={e => setCustomModel(e.target.value)}
            placeholder="e.g. gemma3:4b"
            className="settings-input"
            onKeyDown={e => e.key === 'Enter' && handleCustomPull()}
          />
          <button
            className="model-btn model-btn-download"
            onClick={handleCustomPull}
            disabled={!customModel.trim()}
          >
            <Download size={14} /> Pull
          </button>
        </div>
        {/* Show progress for custom models not in registry */}
        {Object.entries(pullProgress)
          .filter(([id]) => !models?.some(m => m.id === id))
          .map(([id, prog]) => (
            <div key={id} className="model-custom-progress">
              <span>{id}</span>
              {prog.status !== 'error' && prog.status !== 'success' && (
                <div className="model-progress-bar">
                  <div className="model-progress-fill" style={{ width: `${prog.percent}%` }} />
                </div>
              )}
              <span>{prog.status} {prog.percent > 0 ? `${Math.round(prog.percent)}%` : ''}</span>
            </div>
          ))
        }
      </div>
    </div>
  );
}

export default ModelLibrary;
