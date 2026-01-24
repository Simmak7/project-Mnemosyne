/**
 * Tags Feature Module
 *
 * Provides tag management functionality including:
 * - useTags hook for fetching and managing tags
 * - Tag API utilities
 * - HashtagSuggestion for Tiptap editor integration
 *
 * Note: HashtagSuggestion and SuggestionList remain in components/editor/
 * as they are tightly coupled with the Tiptap editor implementation.
 */

export { useTags } from './hooks/useTags';
export { tagsApi } from './api';

// Re-export editor components that handle tags
// These stay in components/editor but are part of the tags feature conceptually
export { hashtagSuggestion } from '../../components/editor/HashtagSuggestion';
