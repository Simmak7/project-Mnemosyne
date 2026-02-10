/**
 * useAIChat - Hook for AI Chat API operations
 *
 * Uses AIChatContext for persistent state.
 * Provides query methods, conversation management, and streaming support.
 */

import { useCallback, useRef } from 'react';
import { useAIChatContext, useAIChatActions } from './AIChatContext';
import { useBrainChat } from './useBrainChat';
import { api } from '../../../utils/api';
import { parseSSEStream, createUserMessage, createAssistantPlaceholder } from './utils/streamParser';
import * as conversationApi from './utils/conversationApi';

export function useAIChat() {
  const { state, settings } = useAIChatContext();
  const actions = useAIChatActions();
  const abortControllerRef = useRef(null);
  const brainChat = useBrainChat();
  const isBrainMode = state.chatMode === 'mnemosyne';

  // Helper to set citation preview
  const setTopCitationPreview = useCallback((citations) => {
    if (citations?.length > 0) {
      actions.setActiveCitations(citations);
      const topCitation = citations[0];
      actions.setPreview({
        type: topCitation.source_type,
        id: topCitation.source_id,
        title: topCitation.title,
        citation: topCitation,
      });
    }
  }, [actions]);

  // Build query options
  const buildQueryOptions = useCallback((options) => ({
    query: options.query,
    conversation_id: state.conversationId,
    max_sources: options.maxSources ?? settings.maxSources,
    include_images: options.includeImages ?? settings.includeImages,
    include_graph: options.includeGraph ?? settings.includeGraph,
    min_similarity: options.minSimilarity ?? settings.minSimilarity,
  }), [state.conversationId, settings]);

  /**
   * Send a RAG query (non-streaming)
   */
  const sendQuery = useCallback(async (query, options = {}) => {
    actions.setLoading(true);
    actions.setError(null);
    actions.addMessage(createUserMessage(query));

    try {
      const data = await api.post('/rag/query', buildQueryOptions({ query, ...options }));

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.answer,
        citations: data.citations,
        usedCitationIndices: data.used_citation_indices,
        confidenceScore: data.confidence_score,
        confidenceLevel: data.confidence_level,
        modelUsed: data.model_used,
        timestamp: new Date().toISOString(),
      };
      actions.addMessage(assistantMessage);

      if (data.conversation_id && data.conversation_id !== state.conversationId) {
        actions.setConversation(data.conversation_id);
      }

      actions.setRetrievalMetadata(data.retrieval_metadata);
      setTopCitationPreview(data.citations);

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
  }, [state.conversationId, settings, actions, buildQueryOptions, setTopCitationPreview]);

  /**
   * Send a streaming RAG query
   */
  const sendStreamingQuery = useCallback(async (query, options = {}) => {
    actions.setLoading(true);
    actions.setStreaming(true);
    actions.setError(null);
    actions.addMessage(createUserMessage(query));

    const placeholder = createAssistantPlaceholder();
    const messageId = placeholder.id;
    actions.addMessage(placeholder);

    abortControllerRef.current = new AbortController();

    try {
      const response = await api.fetch('/rag/query/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildQueryOptions({ query, ...options })),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed: ${response.status}`);
      }

      const reader = response.body.getReader();
      const result = await parseSSEStream(reader, {
        onToken: (content) => actions.updateMessage(messageId, { content }),
        onMetadata: (metadata) => {
          actions.setRetrievalMetadata(metadata);
          if (metadata.conversation_id && metadata.conversation_id !== state.conversationId) {
            actions.setConversation(metadata.conversation_id);
          }
        },
        onDone: ({ content, citations, usedIndices, confidence }) => {
          actions.updateMessage(messageId, {
            content,
            citations,
            usedCitationIndices: usedIndices,
            confidenceScore: confidence?.score,
            confidenceLevel: confidence?.level,
            modelUsed: confidence?.modelUsed,
            isStreaming: false,
          });
          setTopCitationPreview(citations);
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
  }, [state.conversationId, settings, actions, buildQueryOptions, setTopCitationPreview]);

  /**
   * Cancel streaming query
   */
  const cancelStream = useCallback(() => {
    abortControllerRef.current?.abort();
  }, []);

  /**
   * Regenerate an assistant message
   */
  const regenerateMessage = useCallback(async (query, messageIdToReplace, options = {}) => {
    actions.setLoading(true);
    actions.setError(null);
    actions.updateMessage(messageIdToReplace, { content: '', citations: [], isStreaming: true, isError: false });

    try {
      if (settings.useStreaming) {
        abortControllerRef.current = new AbortController();

        const response = await api.fetch('/rag/query/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(buildQueryOptions({ query, ...options })),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Request failed: ${response.status}`);
        }

        const reader = response.body.getReader();
        const result = await parseSSEStream(reader, {
          onToken: (content) => actions.updateMessage(messageIdToReplace, { content }),
          onMetadata: (metadata) => actions.setRetrievalMetadata(metadata),
          onDone: ({ content, citations, usedIndices, confidence }) => {
            actions.updateMessage(messageIdToReplace, {
              content,
              citations,
              usedCitationIndices: usedIndices,
              confidenceScore: confidence?.score,
              confidenceLevel: confidence?.level,
              isStreaming: false,
              timestamp: new Date().toISOString(),
            });
            setTopCitationPreview(citations);
          },
        });

        return result;
      } else {
        const data = await api.post('/rag/query', buildQueryOptions({ query, ...options }));

        actions.updateMessage(messageIdToReplace, {
          content: data.answer,
          citations: data.citations,
          usedCitationIndices: data.used_citation_indices,
          confidenceScore: data.confidence_score,
          confidenceLevel: data.confidence_level,
          isStreaming: false,
          timestamp: new Date().toISOString(),
        });

        actions.setRetrievalMetadata(data.retrieval_metadata);
        setTopCitationPreview(data.citations);

        return data;
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        actions.updateMessage(messageIdToReplace, { content: '[Regeneration cancelled]', isStreaming: false });
        return null;
      }
      actions.setError(err.message);
      actions.updateMessage(messageIdToReplace, { content: `Error: ${err.message}`, isError: true, isStreaming: false });
      throw err;
    } finally {
      actions.setLoading(false);
      actions.setStreaming(false);
      abortControllerRef.current = null;
    }
  }, [state.conversationId, settings, actions, buildQueryOptions, setTopCitationPreview]);

  // Conversation management methods
  const startNewConversation = useCallback(async (title = null) => {
    try {
      const data = await conversationApi.createConversation(title);
      actions.setConversation(data.id);
      actions.clearMessages();
      return data;
    } catch (err) {
      actions.setError(err.message);
      throw err;
    }
  }, [actions]);

  const loadConversation = useCallback(async (id) => {
    actions.setLoading(true);
    try {
      const data = await conversationApi.fetchConversation(id);
      actions.setConversation(data.id);
      actions.setMessages(data.messages);
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
    // State
    messages: state.messages,
    isLoading: state.isLoading,
    isStreaming: state.isStreaming,
    error: state.error,
    conversationId: state.conversationId,
    chatMode: state.chatMode,
    lastRetrievalMetadata: state.lastRetrievalMetadata,
    previewItem: state.previewItem,
    brainFilesUsed: state.brainFilesUsed,
    topicsMatched: state.topicsMatched,

    // Query methods (delegated by mode)
    sendQuery: isBrainMode ? brainChat.sendQuery : sendQuery,
    sendStreamingQuery: isBrainMode ? brainChat.sendStreamingQuery : sendStreamingQuery,
    cancelStream: isBrainMode ? brainChat.cancelStream : cancelStream,
    regenerateMessage: isBrainMode ? null : regenerateMessage,

    // Message management
    clearMessages: actions.clearMessages,

    // Conversation management (delegated by mode)
    startNewConversation,
    loadConversation: isBrainMode ? brainChat.loadConversation : loadConversation,
    listConversations: isBrainMode ? brainChat.listConversations : listConversations,
    deleteConversation: isBrainMode ? brainChat.deleteConversation : deleteConversation,
    updateConversation: isBrainMode ? brainChat.updateConversation : updateConversation,

    // Mode management
    setChatMode: actions.setChatMode,

    // Preview management
    setPreview: actions.setPreview,
    clearPreview: actions.clearPreview,
  };
}

export default useAIChat;
