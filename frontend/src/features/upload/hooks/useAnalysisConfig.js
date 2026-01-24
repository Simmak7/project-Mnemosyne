/**
 * useAnalysisConfig Hook
 * Manages analysis configuration state with localStorage persistence
 */

import { useState, useCallback, useEffect } from 'react';
import { DEFAULT_MODEL, isValidModelKey } from '../utils/modelMapper';
import { UPLOAD_FLAGS } from '../utils/featureFlags';

const STORAGE_KEY = 'mnemosyne_upload_config';

/**
 * Default configuration
 * Returns to this on reset - matches current upload behavior
 */
const DEFAULT_CONFIG = {
  model: DEFAULT_MODEL,           // 'balanced' (maps to current model)
  userPrompt: '',                 // Empty = use backend default
  preset: null,                   // No preset selected
  showAdvanced: false,            // Advanced options collapsed
  // Advanced options
  analysisDepth: 'standard',      // 'quick' | 'standard' | 'detailed'
  autoTagging: true,              // Enable automatic tag extraction
  maxTags: 5,                     // Maximum number of tags to extract
  targetAlbumId: null,            // Album to add images to after upload
  autoCreateNote: true,           // Auto-create note from image
};

/**
 * Load config from localStorage
 */
function loadConfig() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      // Validate and merge with defaults
      return {
        ...DEFAULT_CONFIG,
        ...parsed,
        // Ensure model is valid
        model: isValidModelKey(parsed.model) ? parsed.model : DEFAULT_MODEL
      };
    }
  } catch (error) {
    console.warn('Failed to load upload config:', error);
  }
  return DEFAULT_CONFIG;
}

/**
 * Save config to localStorage
 */
function saveConfig(config) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
  } catch (error) {
    console.warn('Failed to save upload config:', error);
  }
}

/**
 * Analysis configuration hook
 * @returns {object} - Config state and actions
 */
export function useAnalysisConfig() {
  const [config, setConfig] = useState(loadConfig);

  // Persist config changes
  useEffect(() => {
    saveConfig(config);
  }, [config]);

  /**
   * Update a single config field
   */
  const updateConfig = useCallback((field, value) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  }, []);

  /**
   * Set model selection
   */
  const setModel = useCallback((model) => {
    if (UPLOAD_FLAGS.MODEL_SELECTION && isValidModelKey(model)) {
      updateConfig('model', model);
    }
  }, [updateConfig]);

  /**
   * Set user prompt (additive)
   */
  const setUserPrompt = useCallback((prompt) => {
    if (UPLOAD_FLAGS.USER_PROMPT_LAYER) {
      updateConfig('userPrompt', prompt);
    }
  }, [updateConfig]);

  /**
   * Set preset
   */
  const setPreset = useCallback((preset) => {
    if (UPLOAD_FLAGS.INTENT_PRESETS) {
      updateConfig('preset', preset);
    }
  }, [updateConfig]);

  /**
   * Toggle advanced options visibility
   */
  const toggleAdvanced = useCallback(() => {
    setConfig(prev => ({ ...prev, showAdvanced: !prev.showAdvanced }));
  }, []);

  /**
   * Set analysis depth
   */
  const setAnalysisDepth = useCallback((depth) => {
    if (['quick', 'standard', 'detailed'].includes(depth)) {
      updateConfig('analysisDepth', depth);
    }
  }, [updateConfig]);

  /**
   * Set auto-tagging enabled
   */
  const setAutoTagging = useCallback((enabled) => {
    updateConfig('autoTagging', enabled);
  }, [updateConfig]);

  /**
   * Set max tags
   */
  const setMaxTags = useCallback((count) => {
    if (count >= 0 && count <= 10) {
      updateConfig('maxTags', count);
    }
  }, [updateConfig]);

  /**
   * Set target album
   */
  const setTargetAlbum = useCallback((albumId) => {
    updateConfig('targetAlbumId', albumId);
  }, [updateConfig]);

  /**
   * Set auto-create note
   */
  const setAutoCreateNote = useCallback((enabled) => {
    updateConfig('autoCreateNote', enabled);
  }, [updateConfig]);

  /**
   * Reset to defaults
   */
  const resetConfig = useCallback(() => {
    setConfig(DEFAULT_CONFIG);
  }, []);

  /**
   * Check if config differs from default (would change behavior)
   */
  const isModified = useCallback(() => {
    return (
      config.userPrompt.trim() !== '' ||
      config.preset !== null ||
      config.model !== DEFAULT_MODEL ||
      config.analysisDepth !== 'standard' ||
      config.autoTagging !== true ||
      config.maxTags !== 5 ||
      config.targetAlbumId !== null ||
      config.autoCreateNote !== true
    );
  }, [config]);

  /**
   * Get config summary for display
   */
  const getConfigSummary = useCallback(() => {
    const parts = [];

    if (config.model !== DEFAULT_MODEL) {
      parts.push(`Model: ${config.model}`);
    }

    if (config.preset) {
      parts.push(`Preset: ${config.preset}`);
    }

    if (config.analysisDepth !== 'standard') {
      parts.push(`Depth: ${config.analysisDepth}`);
    }

    if (config.userPrompt.trim()) {
      parts.push('Custom prompt');
    }

    if (!config.autoTagging) {
      parts.push('No auto-tags');
    }

    if (config.targetAlbumId) {
      parts.push('Album set');
    }

    return parts.length > 0 ? parts.join(' • ') : 'Default settings';
  }, [config]);

  return {
    // State
    config,

    // Individual setters
    setModel,
    setUserPrompt,
    setPreset,
    toggleAdvanced,
    setAnalysisDepth,
    setAutoTagging,
    setMaxTags,
    setTargetAlbum,
    setAutoCreateNote,

    // Bulk operations
    updateConfig,
    resetConfig,

    // Computed
    isModified,
    getConfigSummary
  };
}

export default useAnalysisConfig;
