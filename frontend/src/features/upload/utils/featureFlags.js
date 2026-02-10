/**
 * Upload Feature Flags
 * Controls rollout of new functionality
 *
 * Feature flag OFF → current behavior (backward compatible)
 * Feature flag ON → new enhanced UI
 */

export const UPLOAD_FLAGS = {
  // Core features (enabled by default for new experience)
  MULTI_FILE_UPLOAD: true,      // Allow multiple file selection
  USER_PROMPT_LAYER: true,      // Show additive prompt input
  PROCESSING_STATUS: true,      // Show detailed progress status

  // Advanced features (disabled by default, opt-in)
  PER_FILE_CONFIG: true,        // Per-file custom prompts (collapsed)
  MODEL_SELECTION: false,       // Replaced with real model display in Advanced Options
  DOCUMENT_SUPPORT: true,       // PDF support (backend ready)
  INTENT_PRESETS: true,         // Preset buttons for analysis type

  // Experimental
  BATCH_UPLOAD_API: false,      // Use batch endpoint when available
};

/**
 * Check if a feature is enabled
 * @param {string} flagName - Name of the feature flag
 * @returns {boolean} - Whether the feature is enabled
 */
export function isFeatureEnabled(flagName) {
  return UPLOAD_FLAGS[flagName] ?? false;
}

/**
 * Get all enabled features
 * @returns {string[]} - Array of enabled feature names
 */
export function getEnabledFeatures() {
  return Object.entries(UPLOAD_FLAGS)
    .filter(([, enabled]) => enabled)
    .map(([name]) => name);
}
