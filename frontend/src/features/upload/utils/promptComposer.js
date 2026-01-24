/**
 * Prompt Composer
 * Handles the composition of system + user prompts
 *
 * CRITICAL: System prompt is LOCKED and INTERNAL
 * User prompt is ADDITIVE, never destructive
 *
 * Final Prompt = [SYSTEM_PROMPT] + [USER_ADDITIONS]
 */

/**
 * Analysis depth additions
 */
const DEPTH_ADDITIONS = {
  quick: 'Provide a brief 2-3 sentence summary of the main content.',
  standard: '', // Default behavior - no additions
  detailed: 'Provide a comprehensive and detailed analysis covering all visible elements, text, context, and potential use cases.'
};

/**
 * Compose final prompt for AI analysis
 * @param {object} options - Composition options
 * @param {string} [options.userPrompt] - Optional user-provided additions
 * @param {string} [options.preset] - Optional preset name
 * @param {string} [options.depth] - Analysis depth ('quick' | 'standard' | 'detailed')
 * @returns {string|null} - Composed prompt or null (uses backend default)
 */
export function composePrompt({ userPrompt = '', preset = null, depth = 'standard' } = {}) {
  // Get preset additions if specified
  const presetAdditions = preset ? getPresetAdditions(preset) : '';

  // Get depth additions
  const depthAdditions = DEPTH_ADDITIONS[depth] || '';

  // Combine all additions: depth + preset + user prompt
  const additions = [depthAdditions, presetAdditions, userPrompt]
    .filter(Boolean)
    .join(' ')
    .trim();

  // If no additions, return null to use backend default
  if (!additions) {
    return null;
  }

  // Return additions only - backend will prepend system prompt
  // This ensures system prompt remains locked on backend
  return additions;
}

/**
 * Get preset additions text
 * These are user-prompt-layer additions, NOT system prompts
 * @param {string} preset - Preset name
 * @returns {string} - Preset additions or empty string
 */
function getPresetAdditions(preset) {
  const presets = {
    // Image analysis (default behavior, no additions needed)
    image: '',

    // Document focus
    document: 'Focus on extracting text content, key information, and document structure. Identify headings, paragraphs, and any structured data.',

    // Diagram focus
    diagram: 'Focus on identifying diagram elements, relationships, connections, and the overall structure or flow. Describe what the diagram represents.',

    // Screenshot focus
    screenshot: 'This is a screenshot. Identify the application or context, extract any visible text, and describe the key elements shown.',

    // Handwritten notes
    handwritten: 'This contains handwritten content. Focus on transcribing the handwritten text accurately and preserving the structure.',
  };

  return presets[preset] || '';
}

/**
 * Available presets for UI
 */
export const PRESETS = [
  {
    id: 'image',
    label: 'Photo',
    icon: 'Image',
    description: 'Standard photo analysis'
  },
  {
    id: 'document',
    label: 'Document',
    icon: 'FileText',
    description: 'Extract text and structure'
  },
  {
    id: 'diagram',
    label: 'Diagram',
    icon: 'GitBranch',
    description: 'Analyze flow and connections'
  },
  {
    id: 'screenshot',
    label: 'Screenshot',
    icon: 'Monitor',
    description: 'App screenshots and UI'
  },
  {
    id: 'handwritten',
    label: 'Handwritten',
    icon: 'PenTool',
    description: 'Transcribe handwritten notes'
  }
];

/**
 * Check if prompt would change default behavior
 * @param {string|null} prompt - Composed prompt
 * @returns {boolean} - True if prompt modifies default
 */
export function isCustomPrompt(prompt) {
  return prompt !== null && prompt.trim().length > 0;
}
