/**
 * Settings constants and feature flags
 */

export const FEATURE_FLAGS = [
  { key: 'ENABLE_NEW_BRAIN_GRAPH', label: 'Neural Glass Brain Graph', description: 'New graph visualization with exploration views', default: false },
  { key: 'ENABLE_NEW_GALLERY', label: 'Immich-style Gallery', description: 'Grid layout with blurhash placeholders', default: true },
  { key: 'ENABLE_NEW_NOTES', label: '3-Pane Notes Layout', description: 'Collections, list, and editor panels', default: true },
  { key: 'ENABLE_NEW_AI_CHAT', label: 'AI Chat Layout', description: 'Enhanced chat with history panel', default: true },
  { key: 'ENABLE_NEW_UPLOAD', label: 'Neural Studio Upload', description: '2-pane upload experience', default: true },
  { key: 'ENABLE_WORKSPACE', label: 'Workspace Mode', description: 'Full workspace layout', default: true },
  { key: 'ENABLE_LORA_TRAINING', label: 'LoRA Brain Training', description: 'Experimental: Fine-tune AI model with your notes (requires GPU)', default: false },
];

export const ACCENT_COLORS = {
  blue: { primary: '#3B82F6', hover: '#2563EB', light: '#DBEAFE' },
  purple: { primary: '#8B5CF6', hover: '#7C3AED', light: '#EDE9FE' },
  green: { primary: '#10B981', hover: '#059669', light: '#D1FAE5' },
  orange: { primary: '#F59E0B', hover: '#D97706', light: '#FEF3C7' },
  pink: { primary: '#EC4899', hover: '#DB2777', light: '#FCE7F3' },
};

export const DENSITY_VALUES = {
  compact: { spacing: '8px', padding: '12px', fontSize: '13px' },
  comfortable: { spacing: '16px', padding: '16px', fontSize: '14px' },
  spacious: { spacing: '24px', padding: '20px', fontSize: '15px' },
};
