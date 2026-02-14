/**
 * Settings constants and feature flags
 */

export const FEATURE_FLAGS = [
  { key: 'ENABLE_CLOUD_AI', label: 'Cloud AI Providers', description: 'Enable cloud AI models (Claude, ChatGPT) for more powerful responses. Data leaves your machine.', default: false },
  { key: 'ENABLE_LORA_TRAINING', label: 'LoRA Brain Training', description: 'Experimental: Fine-tune AI model with your notes (requires GPU)', default: false },
  { key: 'ENABLE_LEGACY_RAG', label: 'Legacy RAG Mode', description: 'Show the classic RAG search mode in the AI chat mode toggle. NEXUS RAG is the recommended replacement.', default: false },
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
