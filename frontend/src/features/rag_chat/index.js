/**
 * RAG Chat Feature - Main Export
 *
 * Provides citation-aware AI chat with:
 * - Multi-turn conversations
 * - Real-time streaming responses
 * - Source citations with explainability
 * - Conversation history management
 */

// Components
export { default as RAGChat } from './components/RAGChat';
export { default as CitationCard, CitationList } from './components/CitationCard';
export { default as RetrievalExplainer, RetrievalBadges } from './components/RetrievalExplainer';

// Hooks
export { default as useRAGChat } from './hooks/useRAGChat';
