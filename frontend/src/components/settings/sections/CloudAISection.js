/**
 * Cloud AI settings section - API keys, provider selection, model config
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Cloud, AlertTriangle, Key, CheckCircle, XCircle, Trash2, Zap } from 'lucide-react';
import { api } from '../../../utils/api';
import './CloudAISection.css';

const PROVIDERS = [
  { id: 'anthropic', name: 'Anthropic', placeholder: 'sk-ant-...' },
  { id: 'openai', name: 'OpenAI', placeholder: 'sk-...' },
  { id: 'custom', name: 'Custom (OpenAI-compatible)', placeholder: 'API key...' },
];

function CloudAISection({ preferences, availableModels, onPreferenceUpdate }) {
  const [apiKeys, setApiKeys] = useState([]);
  const [activeTab, setActiveTab] = useState('anthropic');
  const [keyInput, setKeyInput] = useState('');
  const [baseUrlInput, setBaseUrlInput] = useState('');
  const [testing, setTesting] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [saving, setSaving] = useState(false);

  const fetchApiKeys = useCallback(async () => {
    try {
      const data = await api.get('/settings/api-keys');
      setApiKeys(data);
    } catch {
      // Keys not loaded yet
    }
  }, []);

  useEffect(() => { fetchApiKeys(); }, [fetchApiKeys]);

  const cloudEnabled = preferences?.cloud_ai_enabled || false;
  const savedProviders = new Set(apiKeys.map(k => k.provider));

  const activeProvider = preferences?.cloud_ai_provider;
  const cloudModels = (availableModels || []).filter(
    m => m.provider === activeProvider
  );
  const ragCloudModels = cloudModels.filter(
    m => m.use_cases?.includes('rag') || m.use_cases?.includes('both')
  );
  const brainCloudModels = cloudModels.filter(
    m => m.use_cases?.includes('brain') || m.use_cases?.includes('both')
  );

  const handleSaveKey = async () => {
    if (!keyInput.trim()) return;
    setSaving(true);
    try {
      const body = { provider: activeTab, api_key: keyInput.trim() };
      if (activeTab === 'custom' && baseUrlInput.trim()) {
        body.base_url = baseUrlInput.trim();
      }
      await api.post('/settings/api-keys', body);
      setKeyInput('');
      setBaseUrlInput('');
      setTestResult(null);
      fetchApiKeys();
    } catch (e) {
      setTestResult({ valid: false, message: e.message });
    }
    setSaving(false);
  };

  const handleTestKey = async (provider) => {
    setTesting(provider);
    setTestResult(null);
    try {
      const data = await api.post(`/settings/api-keys/${provider}/test`);
      setTestResult(data);
    } catch (e) {
      setTestResult({ valid: false, message: e.message });
    }
    setTesting(null);
  };

  const handleDeleteKey = async (provider) => {
    try {
      await api.delete(`/settings/api-keys/${provider}`);
      fetchApiKeys();
      setTestResult(null);
    } catch { /* ignore */ }
  };

  const activeKeyInfo = apiKeys.find(k => k.provider === activeTab);

  return (
    <div className="settings-section cloud-ai-section">
      <div className="settings-section-header">
        <Cloud size={20} />
        <h3>Cloud AI</h3>
        <span className="cloud-ai-badge">Experimental</span>
      </div>

      {/* Privacy warning */}
      <div className="cloud-ai-warning">
        <AlertTriangle size={16} />
        <div>
          <strong>Data leaves your machine.</strong> Cloud AI sends your notes
          and queries to external servers (Anthropic, OpenAI, or your custom
          endpoint). Only enable if you understand the privacy implications.
        </div>
      </div>

      {/* Master toggle */}
      <div className="settings-item settings-item-toggle">
        <div className="settings-item-info">
          <label>Enable Cloud AI</label>
          <p>Use cloud models for RAG and Brain queries</p>
        </div>
        <button
          className={`toggle-switch ${cloudEnabled ? 'active' : ''}`}
          onClick={() => onPreferenceUpdate('cloud_ai_enabled', !cloudEnabled)}
          role="switch"
          aria-checked={cloudEnabled}
        >
          <span className="toggle-slider" />
        </button>
      </div>

      {cloudEnabled && (
        <>
          {/* Provider tabs */}
          <div className="cloud-ai-tabs">
            {PROVIDERS.map(p => (
              <button
                key={p.id}
                className={`cloud-ai-tab ${activeTab === p.id ? 'active' : ''}`}
                onClick={() => { setActiveTab(p.id); setTestResult(null); }}
              >
                {p.name}
                {savedProviders.has(p.id) && (
                  <CheckCircle size={12} className="tab-check" />
                )}
              </button>
            ))}
          </div>

          {/* Key management for active tab */}
          <div className="cloud-ai-key-section">
            {activeKeyInfo ? (
              <div className="cloud-ai-saved-key">
                <div className="saved-key-info">
                  <Key size={14} />
                  <span className="key-hint">{activeKeyInfo.key_hint}</span>
                  <span className={`key-status ${activeKeyInfo.is_valid ? 'valid' : 'invalid'}`}>
                    {activeKeyInfo.is_valid ? 'Valid' : 'Invalid'}
                  </span>
                </div>
                <div className="saved-key-actions">
                  <button
                    className="cloud-ai-btn cloud-ai-btn-test"
                    onClick={() => handleTestKey(activeTab)}
                    disabled={testing === activeTab}
                  >
                    {testing === activeTab ? 'Testing...' : 'Test'}
                  </button>
                  <button
                    className="cloud-ai-btn cloud-ai-btn-delete"
                    onClick={() => handleDeleteKey(activeTab)}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ) : (
              <div className="cloud-ai-key-input-group">
                <input
                  type="password"
                  className="cloud-ai-input"
                  placeholder={PROVIDERS.find(p => p.id === activeTab)?.placeholder}
                  value={keyInput}
                  onChange={e => setKeyInput(e.target.value)}
                />
                {activeTab === 'custom' && (
                  <input
                    type="text"
                    className="cloud-ai-input"
                    placeholder="https://api.example.com/v1"
                    value={baseUrlInput}
                    onChange={e => setBaseUrlInput(e.target.value)}
                  />
                )}
                <button
                  className="cloud-ai-btn cloud-ai-btn-save"
                  onClick={handleSaveKey}
                  disabled={saving || !keyInput.trim()}
                >
                  {saving ? 'Saving...' : 'Save Key'}
                </button>
              </div>
            )}

            {/* Test result */}
            {testResult && (
              <div className={`cloud-ai-test-result ${testResult.valid ? 'success' : 'error'}`}>
                {testResult.valid ? <CheckCircle size={14} /> : <XCircle size={14} />}
                <span>{testResult.message}</span>
                {testResult.models_available > 0 && (
                  <span className="models-count">{testResult.models_available} models</span>
                )}
              </div>
            )}
          </div>

          {/* Active provider selection */}
          <div className="cloud-ai-provider-select">
            <label>
              <Zap size={14} className="label-icon" />
              Active Provider
            </label>
            <select
              className="settings-select"
              value={preferences?.cloud_ai_provider || ''}
              onChange={e => onPreferenceUpdate('cloud_ai_provider', e.target.value)}
            >
              <option value="">Select a provider...</option>
              {PROVIDERS.filter(p => savedProviders.has(p.id)).map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          {/* Cloud model selection */}
          {preferences?.cloud_ai_provider && savedProviders.has(preferences.cloud_ai_provider) && (
            <div className="cloud-ai-model-grid">
              <div className="settings-appearance-item model-select-item">
                <label>Cloud RAG Model</label>
                <select
                  className="settings-select"
                  value={preferences?.cloud_rag_model || ''}
                  onChange={e => onPreferenceUpdate('cloud_rag_model', e.target.value)}
                >
                  <option value="">Select model...</option>
                  {ragCloudModels.map(m => (
                    <option key={m.id} value={m.id}>{m.name}</option>
                  ))}
                </select>
              </div>
              <div className="settings-appearance-item model-select-item">
                <label>Cloud Brain Model</label>
                <select
                  className="settings-select"
                  value={preferences?.cloud_brain_model || ''}
                  onChange={e => onPreferenceUpdate('cloud_brain_model', e.target.value)}
                >
                  <option value="">Select model...</option>
                  {brainCloudModels.map(m => (
                    <option key={m.id} value={m.id}>{m.name}</option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default CloudAISection;
