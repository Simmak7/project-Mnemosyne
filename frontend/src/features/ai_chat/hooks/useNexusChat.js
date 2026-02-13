/**
 * useNexusChat - Hook for NEXUS graph-native adaptive retrieval
 *
 * Handles NEXUS-specific queries with richer response data:
 * - Rich citations with graph context
 * - Connection insights
 * - Exploration suggestions
 * - Mode detection (FAST/STANDARD/DEEP)
 */

import { useCallback, useRef } from 'react';
import { useAIChatContext, useAIChatActions } from './AIChatContext';
import { api } from '../../../utils/api';
import { parseNexusSSEStream } from './utils/nexusStreamParser';
import { createUserMessage, createAssistantPlaceholder } from './utils/streamParser';
import * as conversationApi from './utils/conversationApi';

export function useNexusChat() {
  const { state, settings } = useAIChatContext();
  const actions = useAIChatActions();
  const abortControllerRef = useRef(null);

  const buildQueryOptions = useCallback((query) => ({
    query,
    conversation_id: state.conversationId,
    mode: settings.nexusMode || 'auto',
    max_sources: settings.maxSources,
    include_images: settings.includeImages,
    include_graph: settings.includeGraph,
    min_similarity: settings.minSimilarity,
  }), [state.conversationId, settings]);

  /** Send a NEXUS query (non-streaming) */
  const sendQuery = useCallback(async (query) => {
    actions.setLoading(true);
    actions.setError(null);
    actions.addMessage(createUserMessage(query));

    try {
      const data = await api.post('/nexus/query', buildQueryOptions(query));

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.answer,
        citations: data.rich_citations,
        usedCitationIndices: data.used_citation_indices,
        connectionInsights: data.connection_insights,
        explorationSuggestions: data.exploration_suggestions,
        confidenceScore: data.confidence_score,
        confidenceLevel: data.confidence_level,
        modelUsed: data.model_used,
        isNexusMode: true,
        nexusMode: data.retrieval_metadata?.mode,
        timestamp: new Date().toISOString(),
      };
      actions.addMessage(assistantMessage);

      if (data.conversation_id && data.conversation_id !== state.conversationId) {
        actions.setConversation(data.conversation_id);
      }

      actions.setRetrievalMetadata(data.retrieval_metadata);

      if (data.connection_insights?.length > 0) {
        actions.setConnectionInsights(data.connection_insights);
      }
      if (data.exploration_suggestions?.length > 0) {
        actions.setExplorationSuggestions(data.exploration_suggestions);
      }

      if (data.rich_citations?.length > 0) {
        actions.setActiveCitations(data.rich_citations);
        const top = data.rich_citations[0];
        actions.setPreview({
          type: top.source_type,
          id: top.source_id,
          title: top.title,
          citation: top,
        });
      }

      return data;
    } catch (err) {
      actions.setError(err.message);
      actions.addMessage({
        id: Date.now() + 1,
        role: 'assistant',
        content: `Error: ${err.message}`,
        isError: true,
        timestamp: new Date().toISOString(),
      });
      throw err;
    } finally {
      actions.setLoading(false);
    }
  }, [state.conversationId, settings, actions, buildQueryOptions]);

  /** Send a streaming NEXUS query */
  const sendStreamingQuery = useCallback(async (query) => {
    actions.setLoading(true);
    actions.setStreaming(true);
    actions.setError(null);
    actions.addMessage(createUserMessage(query));

    const placeholder = createAssistantPlaceholder();
    placeholder.isNexusMode = true;
    const messageId = placeholder.id;
    actions.addMessage(placeholder);

    abortControllerRef.current = new AbortController();

    try {
      const response = await api.fetch('/nexus/query/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildQueryOptions(query)),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed: ${response.status}`);
      }

      const reader = response.body.getReader();
      const result = await parseNexusSSEStream(reader, {
        onToken: (content) => actions.updateMessage(messageId, { content }),
        onCitations: (citations) => {
          if (citations?.length > 0) {
            actions.setActiveCitations(citations);
            const top = citations[0];
            actions.setPreview({
              type: top.source_type,
              id: top.source_id,
              title: top.title,
              citation: top,
            });
          }
        },
        onConnections: (connections) => {
          if (connections?.length > 0) {
            actions.setConnectionInsights(connections);
          }
        },
        onSuggestions: (suggestions) => {
          if (suggestions?.length > 0) {
            actions.setExplorationSuggestions(suggestions);
          }
        },
        onMetadata: (metadata) => {
          actions.setRetrievalMetadata(metadata);
          if (metadata.conversation_id && metadata.conversation_id !== state.conversationId) {
            actions.setConversation(metadata.conversation_id);
          }
        },
        onDone: ({ content, citations, usedIndices, connections, suggestions, confidence }) => {
          actions.updateMessage(messageId, {
            content,
            citations,
            usedCitationIndices: usedIndices,
            connectionInsights: connections,
            explorationSuggestions: suggestions,
            confidenceScore: confidence?.score,
            confidenceLevel: confidence?.level,
            modelUsed: confidence?.modelUsed,
            isStreaming: false,
            isNexusMode: true,
            nexusMode: state.lastRetrievalMetadata?.mode,
          });
        },
      });

      return result;
    } catch (err) {
      if (err.name === 'AbortError') {
        actions.updateMessage(messageId, { content: ' [Cancelled]', isStreaming: false });
        return null;
      }
      actions.setError(err.message);
      actions.updateMessage(messageId, { content: `Error: ${err.message}`, isError: true, isStreaming: false });
      throw err;
    } finally {
      actions.setLoading(false);
      actions.setStreaming(false);
      abortControllerRef.current = null;
    }
  }, [state.conversationId, state.lastRetrievalMetadata, settings, actions, buildQueryOptions]);

  const cancelStream = useCallback(() => {
    abortControllerRef.current?.abort();
  }, []);

  const loadConversation = useCallback(async (id) => {
    actions.setLoading(true);
    try {
      const data = await conversationApi.fetchConversation(id);
      actions.setConversation(data.id);
      actions.setMessages(data.messages);

      // Restore citations from the last assistant message
      const lastAssistant = [...data.messages].reverse().find(m => m.role === 'assistant');
      if (lastAssistant?.citations?.length > 0) {
        actions.setActiveCitations(lastAssistant.citations);
        const top = lastAssistant.citations[0];
        actions.setPreview({
          type: top.source_type,
          id: top.source_id,
          title: top.title,
          citation: top,
        });
      }

      // Restore NEXUS insights (always set, even if empty, to clear stale state)
      actions.setConnectionInsights(data.connectionInsights || []);
      actions.setExplorationSuggestions(data.explorationSuggestions || []);

      return data;
    } catch (err) {
      actions.setError(err.message);
      throw err;
    } finally {
      actions.setLoading(false);
    }
  }, [actions]);

  const listConversations = useCallback(async (skip = 0, limit = 50) => {
    return conversationApi.listConversations(skip, limit);
  }, []);

  const deleteConversation = useCallback(async (id) => {
    try {
      await conversationApi.deleteConversation(id);
      if (id === state.conversationId) {
        actions.clearMessages();
      }
      return true;
    } catch (err) {
      actions.setError(err.message);
      throw err;
    }
  }, [state.conversationId, actions]);

  const updateConversation = useCallback(async (id, updates) => {
    try {
      return await conversationApi.updateConversation(id, updates);
    } catch (err) {
      actions.setError(err.message);
      throw err;
    }
  }, [actions]);

  return {
    sendQuery,
    sendStreamingQuery,
    cancelStream,
    loadConversation,
    listConversations,
    deleteConversation,
    updateConversation,
  };
}

export default useNexusChat;
