/**
 * Model Mapper
 * Abstracts model selection from raw model names
 *
 * Users see: Balanced, Fast, Precise
 * Backend receives: actual model IDs
 */

/**
 * Model configurations
 * All currently map to the same model (safe default)
 * Update mappings when additional models are configured
 */
export const MODELS = {
  balanced: {
    id: 'llama3.2-vision:11b',
    label: 'Balanced',
    description: 'Best balance of quality and speed',
    icon: 'Scale',
    default: true
  },
  fast: {
    id: 'llama3.2-vision:11b', // Ready for faster model when available
    label: 'Fast',
    description: 'Quick analysis for simple images',
    icon: 'Zap',
    default: false
  },
  precise: {
    id: 'llama3.2-vision:11b', // Ready for larger model when available
    label: 'Precise',
    description: 'Thorough analysis with more detail',
    icon: 'Target',
    default: false
  }
};

/**
 * Default model key
 */
export const DEFAULT_MODEL = 'balanced';

/**
 * Get model ID from user-friendly key
 * @param {string} key - Model key (balanced, fast, precise)
 * @returns {string} - Actual model ID for backend
 */
export function getModelId(key) {
  const model = MODELS[key] || MODELS[DEFAULT_MODEL];
  return model.id;
}

/**
 * Get model configuration
 * @param {string} key - Model key
 * @returns {object} - Model configuration object
 */
export function getModelConfig(key) {
  return MODELS[key] || MODELS[DEFAULT_MODEL];
}

/**
 * Get all available models for UI
 * @returns {Array} - Array of model configs with keys
 */
export function getAvailableModels() {
  return Object.entries(MODELS).map(([key, config]) => ({
    key,
    ...config
  }));
}

/**
 * Check if model selection would change default
 * @param {string} key - Selected model key
 * @returns {boolean} - True if non-default model selected
 */
export function isNonDefaultModel(key) {
  return key !== DEFAULT_MODEL;
}

/**
 * Validate model key
 * @param {string} key - Model key to validate
 * @returns {boolean} - True if valid
 */
export function isValidModelKey(key) {
  return key in MODELS;
}
