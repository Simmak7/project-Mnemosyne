/**
 * AI Chat Feature - Public Exports
 */

// Main layout component
export { default as AIChatLayout } from './components/AIChatLayout';

// Individual components (for advanced usage)
export { default as ConversationPane } from './components/ConversationPane';
export { default as ChatCanvas } from './components/ChatCanvas';
export { default as ContextRadar } from './components/ContextRadar';

// Context and hooks
export { AIChatProvider, useAIChatContext, useAIChatActions } from './hooks/AIChatContext';
export { useAIChat } from './hooks/useAIChat';
export { useAIChatKeyboardShortcuts } from './hooks/useAIChatKeyboardShortcuts';
